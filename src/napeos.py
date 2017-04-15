#!/usr/bin/python

import os, glob, Processing, Resources, gamit, pyDomes, StnInfoLib, Utils, re, tarfile, shutil, pyDate, math

ATX_FILE_PATH = "$HOME/db/files/atx/gps.atx";
APR_FILE_PATH = "$HOME/db/files/stat/gps.apr";
OTL_GRID_PATH = "/processing/local_tables/gamit/otl.grid";

class NapeosException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Session(Processing.Session):

    def __init__(self):

        # call super class constructor
        super(Session, self).__init__()

        # all the metadata needs coordinated DOMES numbers
        self.domesMgr = pyDomes.Domes()

        # compute processing date
        self.date = None;

    # @Override
    def initialize(self):

        # do all the program independent stuff
        super(Session, self).initialize();

        # create generic date objectcd
        self.date = pyDate.Date(year=self.options['year'], doy=self.options['doy']);

        # figure out which stations have APR
        stns_with_apr = self.get_stns_with_apr();

        # initialize DOMES for each station requested
        # note that site.dat, gps.apr, and D-file use only stns listed in domesMgr
        for stnid in self.stn_list:

            # if there is no APR then do not add to DOMES
            if not stnid in stns_with_apr:
                os.sys.stderr.write('excluding station not found in apr: %s\n'%stnid)
                continue

            # parse the station id
            (ns,code) = Utils.parse_stnId(stnid)

            # add the station to the domes mgr if it's not already defined
            if not self.domesMgr.containsStnId(code): self.domesMgr.addStn(code);

        # get the resource bucket path
        bucket = self.get_resources_path();

        apr_file_path = self.files['apr']

        # create gamit apr file for OTL computations
        gamit_apr_file_path = gamit.wlapr2apr(apr_file_path)

        # get the binaries for gamit (bin file path used by create_U_file)
        self.files['bin'] = Resources.get_bin('napeos', self.work_dir_path)

        # get the tables for gamit
        self.files['tables'] = Resources.get_tables('napeos', self.work_dir_path)

        # combine all of the station info files into single file
        gamit_station_info_file_path = self.concatonate_station_info_files()

        # convert the station info file into station.dat
        napeos_station_dat_file_path = self.convert_station_info_to_dat(gamit_station_info_file_path)

        # convert the generic agt apr file to napeos crd file
        napeos_crd_file_path = self.convert_apr_to_crd(apr_file_path)

        # create the site.dat file with domes numbers for each station
        napeos_site_dot_dat = self.create_site_dot_dat()

        napeos_BLQ_file_path = self.create_OTL_file(gamit_apr_file_path,self.domesMgr.stn_list())

        # clean up all this shit
        self.init_cleanup()

        # create the setup script for the job
        setup_script_file_path = self.create_setup_script()

        # create the run script for the job
        run_script_file_path = self.create_run_script()

        # create the teardown script for the job
        teardown_script_file_path = self.create_tear_down_script()

    def get_stns_with_apr(self):
        with open(self.files['apr'],'r') as fid:
            return [line.split()[0] for line in fid]

    def concatonate_station_info_files(self):

        # get the resources path
        resources_dir = self.get_resources_path();

        # if there is no resources directory then nothing to do
        if not os.path.isdir(resources_dir): return

        # get a list of station info files in the resources directory
        station_info_files_list = glob.glob(os.path.join(resources_dir,"*.station.info"))

        # make sure there is something to do
        if len(station_info_files_list) == 0: return

        # create file name for combined station info
        station_info_out_file_name = "gamit.station.info"

        # create file path for combined station info
        station_info_out_file_path = os.path.join(resources_dir,station_info_out_file_name);

        # define the required header line for station.info files
        header_line = "*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN "

        # write lines of each station info to output
        with open(station_info_out_file_path,'w') as outfile:

            # add header line to the output station info file
            outfile.write(header_line+'\n')

            # now add the lines from each station info file
            for infofile in station_info_files_list:

                # add the lines from i'th info file
                with open(infofile,'r') as infile: outfile.write(infile.read())

                # add footer to force new line
                outfile.write('* \n');

        # return file path to the resulting combine station info
        return station_info_out_file_path

    def convert_station_info_to_dat(self,info_file_path):

        # local helper function
        #def mk2dstr(d):
        #    dstr = str(d);
        #    if d < 10: dstr = "0" + dstr; return dstr

        def mk2dstr(d):
            if d < 10: dstr = "0" + str(d);
            else: dstr = str(d);
            return dstr

        # init collection of station info objects for station in file
        stnInfoFile = StnInfoLib.StnInfoCollection(info_file_path)

        # init index
        indx = 1

        # get path to resources
        resources_dir = self.get_resources_path()

        # output dat file
        station_dat_file_name = "station.dat"

        # create the output file path
        station_dat_file_path = os.path.join(resources_dir,station_dat_file_name)

        with open(station_dat_file_path,'w') as fid:

            # write the header line for station.dat
            fid.write("NSTADB    " + str(stnInfoFile.numberOfLines())+'\n')

            # add content for each station
            for stnInfoObj in stnInfoFile:

                # set the station name we're working with
                stnName = stnInfoObj.getName().lower();

                # add the station to the domes mgr if it's not already defined
                if not self.domesMgr.containsStnId(stnName):
                    #stnName, domesNumber = self.domesMgr.addStn(stnName);
                    print('excluding station info for station not defined in domes: '+stnName)
                    continue

                domesNumber = self.domesMgr.domesForStnId(stnName);

                # control to print "S" or "-"
                isFirstLine = True;

                # row header
                tag = "S";

                # get line for date
                line = stnInfoObj.getStnInfo(self.date);

                #make sure entry for date, if not move along
                if line is None:
                    print('excluding station info missing entry for date: '+stnName)
                    continue

                # for each line in stnInfoObj ...
                #for line in stnInfoObj:

                startDateStr = "%4d/%2s/%2s-00:00:00.000000" % (
                line.startDate.year, mk2dstr(line.startDate.month), mk2dstr(line.startDate.day));
                stopDateStr = "%4d/%2s/%2s-00:00:00.000000" % (
                line.stopDate.year, mk2dstr(line.stopDate.month), mk2dstr(line.stopDate.day));
                rxVers = line.rx.vers;

                fid.write("%1s %4s GPS %10s %4d %9s %4s  0 %26s  0 %26s  %6.4f  %6.4f  %6.4f %-15s %4s %20s %-20s %-5s %-11s %-80s %-50s 1 %80s %-80s %10.2f %10.2f\n" % (
                tag, stnName.upper(), "", indx, domesNumber, stnName.upper(), startDateStr, stopDateStr, line.ant.n,
                line.ant.e, line.ant.ht, line.ant.type, line.ant.dome[0:4], line.ant.sn, line.rx.type, line.rx.sn[0:5],
                line.rx.vers[0:11], APR_FILE_PATH[0:80], "auto generated by info2dat.py", " ", ATX_FILE_PATH[0:80], 1575.42,
                1227.60))

                if isFirstLine: tag = "-"

                # udpate index
                indx +=1

            # put the footer in there and we're done
            fid.write("endlist\n")

        # fin
        return station_dat_file_path

    def convert_apr_to_crd(self, apr_file_path):

        header  = "STATION COORDINATES AT EPOCH 2000.00                                                                               \n"
        header += "NAPEOS STATION COORDINATES AND VELOCITIES Created for GSN                                                          \n"
        header += "                                                                                                                   \n"
        header += "DOMES NB. SITE NAME        TECH. ID.                        X/Vx         Y/Vy         Z/Vz         Sigmas     SOLN \n"
        header += "                                                            -----------------------m/m/y----------------------     \n"
        header += "-------------------------------------                 -------------------------------------------------------------\n"

        # local helper function
        def printAsCrd(dst, domesNumber, stnId, x, y, z, sigX, sigY, sigZ):

            xyzStr = "%9s %4s %9s     GPS %4s                  %12.3f %12.3f %12.3f %5s %5s %5s OSU" % (
                domesNumber, stnId.upper(), domesNumber, stnId.upper(), x, y, z, sigX, sigY, sigZ)
            velStr = "%9s %4s %9s         %4s                  %12.3f %12.3f %12.3f %5.3f %5.3f %5.3f OSU" % (
                domesNumber, "", "", "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

            dst.write(xyzStr + "\n");
            dst.write(velStr + "\n");

        # get the location of the resources for this work dir
        resources_dir = self.get_resources_path()

        # set the name for napeos coordinate file
        crd_file_name = 'gps.apr'

        # create the full file path for crd file
        crd_file_path = os.path.join(resources_dir,crd_file_name);

        with open(crd_file_path,'w') as fid:
            with open(apr_file_path,'r') as src:

                # write header to the CRD file
                fid.write(header)

                # header is reference epoch on line 1
                referenceEpoch = float(src.readline());

                for line in src.readlines():

                    # kill white spaces either side
                    line = line.strip();

                    # decompose the line
                    lineParts = re.split("\s+", line);

                    if len(lineParts) != 10:
                        os.sys.stderr.write("line: " + line + " is invalid.  apr line must have 10 fields but has "+str(len(lineParts)) +".  Use -h option\n");
                        continue;

                    # every line has at least this
                    stnId = lineParts[0][4:].lower();

                    # not sure if this is correct but we're going to
                    # ignore any stations not already in domes manager
                    if not self.domesMgr.containsStnId(stnId): continue

                    x    = float(lineParts[1]);
                    y    = float(lineParts[2]);
                    z    = float(lineParts[3]);

                    sigX = float(lineParts[4]);
                    sigY = float(lineParts[5]);
                    sigZ = float(lineParts[6]);

                    sigX = ("%5.3f" % sigX)[0:5];
                    sigY = ("%5.3f" % sigY)[0:5];
                    sigZ = ("%5.3f" % sigZ)[0:5];

                    # print the line to the apr file
                    printAsCrd(fid, self.domesMgr.domesForStnId(stnId), stnId, x, y, z, sigX, sigY, sigZ);

        return crd_file_path

    def create_site_dot_dat(self):

        # get full path to resources for this job
        resources_dir = self.get_resources_path()

        # set the name for this file
        site_dat_file_name = 'site.dat'

        # create full file path for output file
        site_dat_file_path = os.path.join(resources_dir,site_dat_file_name)

        # get number of stations in the domes manager
        numStns = self.domesMgr.size();

        # open the file and write entries for each station
        with open(site_dat_file_path,'w') as fid:

            # write the header with number of stations
            fid.write("SITEDB    " + str(numStns) + "\n");

            for (stnid,domes_number) in self.domesMgr:

                # trim the domes number down
                domes_number = str(domes_number).strip()[0:5];

                # create entry for this station
                siteStr = " %4s %-17s %-11s %7.3f %7.3f %4s" % (domes_number, "", "USA", 0.000, 0.000, "NOAM")

                # write the entry to the file
                fid.write(siteStr + "\n");

            # add the footer to the file and we're done
            fid.write("endlist\n");

        # fin
        return site_dat_file_path

    def create_D_file(self, gamit_apr_file_path, stn_list):

        # get the path to the resources dir
        resources_dir = self.get_resources_path()

        # create name for the d-file
        D_file_name = "dtemp0.000"

        # create full path to the d-file
        D_file_path = os.path.join(resources_dir,D_file_name)

        # get the name to the gamit apr file (i.e. L-file)
        #apr_file_name = os.path.basename(gamit_apr_file_path)

        # create D-file with station entries
        with open(D_file_path,'w') as fid:

            # create the header (apr file must start with 'l')
            fid.write(" 1\n 1\n"+ 'lxyz.apr' + "\n"+ "\n\n\n");

            # now add number of stations that will be listed
            fid.write(str(len(stn_list)) + "\n");

            # create entry for each station listed in domesMgr
            for stnid in stn_list:
                if not self.domesMgr.containsStnId(stnid):
                    raise NapeosException('station not found in domes manager: '+stnid)

                fid.write("x" + stnid + "0.000\n")


        # fin
        return D_file_path

    def create_U_file(self, gamit_D_file_path):

        # get the path of the bin tar.gz file
        bin_tar_file_path = self.files['bin']

        # make sure we have otl grid file first
        if not os.path.isfile(OTL_GRID_PATH):
            raise NapeosException("could not find otl.grd file at "+OTL_GRID_PATH)

        # extract the tar file with binaries to work dir
        with tarfile.open(bin_tar_file_path, "r:gz") as tid:
            tid.extractall(self.work_dir_path)

        if not os.path.isdir(os.path.join(self.work_dir_path,'bin')):
            raise NapeosException("could not find bin directory")

        # get path to the resources folder
        resources_dir = self.get_resources_path()

        # change to resources directory
        os.chdir(resources_dir)

        # make link to otl.grid file if not located in resource dir
        if not os.path.isfile('otl.grid'):
            os.symlink(OTL_GRID_PATH, 'otl.grid')

        yearStr = str(self.options['year'])
        doyStr  = str(self.options['doy' ])

        # must be file name, gamit can not take full path
        D_file_name = os.path.basename(gamit_D_file_path);

        # file must start with 'l' (see create_D_file for more details)
        if not os.path.islink('lxyz.apr'): os.symlink('gamit.apr', 'lxyz.apr')

        # make the command to execute
        exeStr = '../bin/grdtab.bin' + ' ' + D_file_name + ' ' + yearStr + ' ' + doyStr + ' '  '1.25 ' + 'otl.grid' + ' >> grdtab.out'

        # finally execute the grdtab
        status = os.system(exeStr);

        # descriptive name of the file generated by grdtab
        U_file_name = 'u'; U_file_path = None

        # if grdtab was successful then we have a file
        if status == 0:
            U_file_path = os.path.join(resources_dir,U_file_name)

        # we're done!
        return status,U_file_path

    def create_BLQ_file(self, gamit_U_file_path):

        # if grdtab failed u_file_path could be empty
        if gamit_U_file_path is None: return

        # make path the the ufile just created by grdtab
        uFile = gamit_U_file_path

        # make sure that the ufile actually exists
        if not os.path.isfile(uFile):
            raise NapeosException("ufile: " + uFile + " does not exist");

        # get location of resources folder
        resources_dir = self.get_resources_path()

        # name of the output file
        blq_file_name = 'otl.blq'

        # full path to the outfile
        blq_file_path = os.path.join(resources_dir,blq_file_name)

        with open(gamit_U_file_path,'r') as ufileid:
            with open(blq_file_path,'a') as blqid:

                # for each line in the ufiles
                for line in ufileid.readlines():

                    # clean up the line
                    line = line.strip();

                    if line.startswith("STATION"):
                        # print line;

                        lineParts = re.split("\W+", line);
                        stnName = lineParts[1].lower();
                        stnId = stnName

                        if not self.domesMgr.containsStnId(stnId):
                            raise NapeosException('station '+stnId+' do not have DOMES number')

                        # get the DOMES number for this station
                        domesNumber = self.domesMgr.domesForStnId(stnId);

                        # construct the entry header
                        blqid.write("$$\n")
                        entryHeader = "  %-9s      %4s\n" % (domesNumber[0:5], stnName.upper())
                        blqid.write(entryHeader);

                        # initialize the data row index
                        indx = 1;

                    # see if we're at a data line
                    if line.startswith("OCEANLOD") and not line.startswith("OCEANLOD MODEL"):

                        # break up the line into parts
                        lineParts = re.split("\s+", line);

                        # remove the row header
                        lineParts.remove("OCEANLOD");

                        # convert the data to numbers
                        data = map(float, lineParts);

                        # need to convert the first 3 lines to meters
                        if indx <= 3:

                            # update data index
                            indx += 1;

                            # convert to meters
                            data = [d / 1000 for d in data[:]];

                            # convert to strings for shitty format print
                            data = map(str, data);

                            # remove e-5 and e-6 exponential format
                            for i in range(0, len(data)):
                                if data[i].endswith("e-05"):
                                    data[i] = "0.0000" + data[i][0];
                                elif data[i].endswith("e-06"):
                                    data[i] = "0.00000" + data[i][0];

                            # ok, now window each number to remove leading zero
                            data = [d[1:7] for d in data[:]];

                            # finally, zero pad any number thats too short
                            for i in range(0, len(data)):
                                if len(data[i]) < 6:
                                    data[i] = data[i] + "0" * (6 - len(data[i]));

                            # make format string
                            fmtStr = "  " + "%6s " * 11 + "\n";
                        else:
                            # lol, the easy case here
                            fmtStr = "  " + "%6.1f " * 11 + "\n";

                        # finally, write the string to the output file
                        blqid.write(fmtStr % tuple(data));

        # fin
        return blq_file_path

    def create_OTL_file(self,gamit_apr_file_path,stn_list):

        # depends on GAMIT max_dim (usually something like 85)
        batchsz = 49

        # compute number of batches
        num_batches = int(math.floor(len(stn_list)/batchsz))

        # if one extra iter if not perfect division
        if len(stn_list) % batchsz != 0: num_batches += 1;

        # init none
        napeos_BLQ_file_path = None

        for i in range(0,max(1,num_batches)):

            # compute the start and stop index into station list
            start_indx =  (i+0)*batchsz - 0
            stop_indx  =  (i+1)*batchsz - 1

            # make sure not to overshoot length of list
            stop_indx  = min(stop_indx,len(stn_list))

            # extract batch of stations
            batch_stn_list = stn_list[start_indx:stop_indx+1]

            if len(batch_stn_list) == 0: continue

            # create the D-file for OTL call
            gamit_D_file_path = self.create_D_file(gamit_apr_file_path, batch_stn_list)

            # create the U-file containing ocean loading coeffs
            (status, gamit_U_file_path) = self.create_U_file(gamit_D_file_path)

            # create the napeos BLQ file
            napeos_BLQ_file_path = self.create_BLQ_file(gamit_U_file_path)

        return napeos_BLQ_file_path

    def init_cleanup(self):

        # figure out where the resources for this job are
        resources_dir = self.get_resources_path()

        # misc stuff
        shutil.rmtree(os.path.join(self.work_dir_path, 'bin'))

        def try_remove_resource(fileName):
            try:
                os.remove(os.path.join(resources_dir, fileName))
            except Exception as e:
                os.sys.stderr.write(str(e) + "\n");

        try_remove_resource('dtemp0.000'        )
        try_remove_resource('u'                 )
        try_remove_resource('lxyz.apr'          )
        try_remove_resource('otl.grid'          )
        try_remove_resource('grdtab.out'        )
        try_remove_resource('GAMIT.status'      )
        try_remove_resource('sittbl.'           )
        try_remove_resource('gamit.station.info')
        try_remove_resource('gamit.apr'         )


        # finally
        try_remove_resource(os.path.basename(self.files['apr']))

    def create_setup_script(self):

        setup_file_path = os.path.join(self.work_dir_path, 'setup.sh');

        with open(setup_file_path,'w') as fid:

            contents = \
                """
                #!/bin/bash

                # make sure we can find the program -- put local bin first
                export PATH=`pwd`/bin:${PATH}

                # unpack the tar.gz files (bin and tables)
                for file in $(ls *.gz );do gunzip -f  $file;done
                for file in $(ls *.tar);do tar   -xf  $file;done

                # clean up
                #rm *.tar

                # create links to the tables
                ln -s tables/db db
                ln -s tables/sc sc

                # create napeos working dirs
                mkdir input output solution scratch

                """

            # create the name of the appropriate bahn sat dat
            bahn_sat_dat_file_name = 'bahn_sat.dat.'+self.options['expt_type'].upper()

            # link the bahn_sat tables
            contents += \
                """
                # link bahn tables
                ln -sf %s sc/REF_GPS/mode/bahn/IGSFREE/bahn_sat.dat
                ln -sf %s sc/REF_GPS/mode/bahn/IGSFIX/bahn_sat.dat

                """ % (bahn_sat_dat_file_name,bahn_sat_dat_file_name);

            # link metadata files the to correct place
            contents +=\
                """
                ln -sf `pwd`/resources/station.dat db/tables/station.dat
                ln -sf `pwd`/resources/site.dat    db/tables/site.dat
                ln -sf `pwd`/resources/gps.apr     db/files/stat/gps.apr
                ln -sf `pwd`/resources/otl.blq     db/files/stat/FES2004_CMC.blq

                """

            # prep the rinex files
            contents +=\
                """
                # move to the resource directory
                cd resources

                # decompress and uncompact all the d.Z file
                #for file in $(ls *.[0-9][0-9]d.*);do  gunzip -f $file; done
                #for file in $(ls *.[0-9][0-9]d);  do  crx2rnx.bin    $file; done

                ls *.[0-9][0-9]d.* | xargs -n1 -P8 -I% gunzip      -f %
                ls *.[0-9][0-9]d   | xargs -n1 -P8 -I% crx2rnx.bin -f % 
                
                function hello {
                    OUTFILE=tmp.${1};
                    cc2noncc.bin $1 tmp.${1} ../db/tables/p1c1bias.dat >/dev/null;
                    [[ -f ${OUTFILE} ]] && mv ${OUTFILE} $file;
                }
                

                # run cc2noncc for each existing rinex file
                for file in $(ls *[0-9][0-9]o);do
                    cc2noncc.bin $file tmp ../db/tables/p1c1bias.dat >/dev/null;
                    [[ -f tmp ]] && mv tmp $file;
                done
                
                #ls *[0-9][0-9]o | xargs -n1 -P8 -I% hello %
                

                # up compress sp3 files
                gunzip *.sp3*

                # restore the working dir
                cd ..

                """

            contents +=\
                """
                # move to input director to link resources
                cd input

                # link resources for input
                ln -sf ../resources/*[0-9][0-9]o ./
                ln -sf ../resources/*.sp3        ./
                ln -sf *.sp3 orbit.sp3

                # restore working dir
                cd ..

                """

            # generate pydate for date of job
            #date = pyDate.Date(year=self.options['year'], doy=self.options['doy'])

            # create date strings
            year = str(self.date.year);  month = str(self.date.month);  day = str(self.date.day);

            # make sure that both month and day are two digits
            if self.date.month < 10: month = '0'+month
            if self.date.day   < 10: day   = '0'+day

            # create $HOME resolution
            contents +=\
                """
                # set the working dir
                home=`pwd`;

                # resolve the misdirs.dat file for db files
                cat db/tables/missdirs.dat | sed -e "s@\$HOME@$home@" > tmp;
                mv tmp db/tables/missdirs.dat;

                # resolve the date for the status file (i.e. set the run time)
                echo "R  0000/00/00-00:00:00.000 GENERATED    run %s/%s/%s-00:00:00.000000+00-00:00:00.000000 GPS" > tables/statusfile
                #cat statusFile | sed -e "s@\$YYYY@$year@g" -e "s@\$MM@$month@g" -e "s@\$DD@$day@g"> tmp;
                #mv tmp statusFile;

                # search for lof files and do substitution
                for lofFile in $(find . -name "*.lof" -print);do
                        cat $lofFile | sed -e "s@\$HOME@$home@" > tmp;
                        mv tmp $lofFile;
                done

                # resolve HOME for station.dat
                #cat resources/station.dat | sed -e "s@\$HOME@$home@g" > tmp
                #mv tmp resources/station.dat


                """ % (year,month,day)

            fid.write(contents)

        # add executable rights for setup script
        os.system('chmod +x '+setup_file_path)

        return setup_file_path

    def create_run_script(self):

        run_file_path = os.path.join(self.work_dir_path, 'run.sh');

        with open(run_file_path, 'w') as fid:
            contents = \
                """
                #!/bin/bash
                logfile=napeos.out
                [[ $? -eq 0 ]] && ./bin/BuildCat.bin  < sc/REF_GPS/mode/buildcat/IGS/buildcat.lof            | tee    ${logfile}
                [[ $? -eq 0 ]] && ./bin/GnssObs.bin   < sc/REF_GPS/mode/gnssobs/IGS/gnssobs.lof              | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/ClockRef.bin  < sc/REF_GPS/mode/clockref/AFTER_GNSSOBS/clockref.lof  | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/Bahn.bin      < sc/REF_GPS/mode/bahn/IGSFREE/bahn.lof                | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/ClockRef.bin  < sc/REF_GPS/mode/clockref/AFTER_BAHNFREE/clockref.lof | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/AmbFix.bin    < sc/REF_GPS/mode/ambfix/IGS/ambfix.lof                | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/Bahn.bin      < sc/REF_GPS/mode/bahn/IGSFIX/bahn.lof                 | tee -a ${logfile}
                [[ $? -eq 0 ]] && ./bin/par2sinex.bin < sc/REF_GPS/mode/par2sinex/IGS/par2sinex.lof          | tee -a ${logfile}

                cp napeos.out solution/
                """

            # write contents to the run script
            fid.write(contents)

        # make executable
        os.system("chmod +x "+run_file_path)

        return run_file_path

    def create_tear_down_script(self):

        # initialize a date object
        #date = pyDate.Date(year=self.options['year'], doy=self.options['doy' ])

        # extract the gps week and day of week
        gps_week     = self.date.gpsWeek
        gps_week_day = self.date.gpsWeekDay

        # extract the gps week and convert to string
        gpsWeek_str    = str(self.date.gpsWeek   )
        gpsWeekDay_str = str(self.date.gpsWeekDay)

        # normalize gps week string
        if self.date.gpsWeek < 1000: gpsWeek_str = '0' + gpsWeek_str

        # create file path to the teardown script
        teardown_file_path = os.path.join(self.work_dir_path, 'teardown.sh')

        # get the solutions directory path
        solutions_dir_path = self.relative_solution_path()

        # open file for writing
        with open(teardown_file_path, 'w') as fid:

            contents = \
            """
            #!/bin/bash
            cd ./%s
            """ % solutions_dir_path

            contents += \
            """
            mv bahnfix.snx %s%s%s.snx
            """ % (self.options['org'],gpsWeek_str,gpsWeekDay_str)

            contents += \
            """
            mv napeos.out %s%s%s.out
            """ % (self.options['org'],gpsWeek_str,gpsWeekDay_str)

            contents += \
            """
            for file in $(ls); do gzip ${file}; done
            """

            contents +=\
            """
            cd ../
            """

            fid.write(contents+"\n");

        # make the script executable
        os.system("chmod +x "+teardown_file_path);

        # we're done
        return teardown_file_path

    def relative_solution_path(self):

        return 'solution';

    def get_local_solutions_dir(self):

        return os.path.join(self.work_dir_path, self.relative_solution_path());

    def exe(self):

        if self.isDebug: os.sys.stdout.write('ignoring exe() in debug mode ... \n'); return;

        # move to the working dir
        run_str = 'cd ' + self.work_dir_path + '; ';

        # run setup, execution, and tear down
        run_str += './setup.sh && ./run.sh && ./teardown.sh;';

        # invoke the command on the system
        status = os.system(run_str);

        # return the status
        return status;

    def finalize(self):

        if self.isDebug: os.sys.stdout.write('ignoring finalize() in debug mode ... \n'); return;

        for snx in self.getSNX(): self.mk_mat(snx)

        # file away the data products
        self.pushSNX('');
        self.pushOUT('');
        self.pushMAT('');
        self.pushSP3(  );


def main():

    # initialize a new Processing.Session
    session = Session();

    # initialization
    try:

        # populate using the system input arguments
        session.configure_with_args(os.sys.argv);

        # validate the configuration
        session.validate();

        # blab about it
        session.dump();

        # initialize the session
        session.initialize();

        # execute the program
        session.exe();

        # copy solutions, etc
        session.finalize();

    except NapeosException as err:

        # blab about the exception details and exit
        os.sys.stderr.write(str(err));

    finally:

        print("finally, all done")

        #session.dispose();


if __name__ == '__main__':
    main()