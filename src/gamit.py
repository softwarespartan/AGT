#!/usr/bin/python

"""
Created on Feb 18, 2013

@author: abelbrown
"""

import os, re, glob, gzip, Utils, Processing, Resources, pyDate;

QUEUE = 'com_widelane_jobstats';

from boto.sqs.connection import SQSConnection
from boto.sqs.message    import Message

class GamitException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
def wlapr2apr(aprFile):         
        
    sittblFile = 'sittbl.';  gamitAprFileName = 'gamit.apr'
    
    # make sure that the file exists
    if not os.path.isfile(aprFile):
        raise GamitException('could not find apr file '+aprFile);
    
    # open the apr file for reading
    try:
        src = open(aprFile,'r');
    except:
        raise GamitException('could not open file '+aprFile);
    
    # parse the apr file path to figure out enclosing directory
    (path,fileName) = os.path.split(aprFile);
    
    # create absolute path to the sigma file
    sittblFile = os.path.join(path,sittblFile);
    
    # open sittbl next to the incoming apr file
    try:
        sittbl = open(sittblFile,'w');
        sittbl.write('SITE              FIX    --COORD.CONSTR.--\n');
    except:
        raise GamitException('could not open file '+sittblFile);
    
    # create absolute path to the sigma file
    gamitAprFilePath = os.path.join(path,gamitAprFileName)
    
    # open gamit apr file for writing
    try:
        gamitAprFileHandle = open(gamitAprFilePath,'w')
    except:
        raise GamitException('could not open file '+gamitAprFilePath)

    aprFileName = os.path.basename(aprFile);
    year = float(aprFileName[0:4])
    doy  = float(aprFileName[5:8])
    refEpoch = year + doy/366

    # get the reference epoch from the file
    #refEpoch = float(src.readline());

    # get the lines and populate the files    
    for line in src.readlines():
        
        # clean up the line
        line = line.lower().strip();
        
        # break the line apart
        lineParts = re.split('\s+',line);

        # defensive check
        if len(lineParts) != 10:
            os.sys.stderr.write('invalid apr line: '+line+'\n'); continue;
            
        # parse the station id
        try:
            (ns,code) = Utils.parse_stnId(lineParts[0]);
        except GamitException as e:
            os.sys.stderr.write(str(e)+'\n'); continue;
            
        try:
            # convert all the input to doubles
            X    = float(lineParts[2]); Y    = float(lineParts[3]); Z    = float(lineParts[4]);
            sigE = float(lineParts[8]); sigN = float(lineParts[9]); sigU = float(lineParts[10]);
        except:
            os.sys.stderr.write('error parsing APR line: '+ line); continue;
        
        # check the sigma for too big
        #if sigX >= 10 or sigY >= 10 or sigZ >=10:
        #    os.sys.stderr.write('ignoring apr for '+lineParts[0]+' since sigma greater than 10 meters\n');
        
        # create the apr line
        aprline = " %s_GPS %12.3f %12.3f %12.3f %8.4f %8.4f %8.4f %9.3f" \
            % (code.upper(),X,Y,Z,0,0,0,refEpoch);
        
        # write the apr line to the file
        gamitAprFileHandle.write(aprline+'\n');
        
        # create the sigma line (note NEU not ENU)
        sigline = "%s %s_GPS     NNN    %5.3f %5.3f %5.3f" % (code.upper(),code.upper(),sigN,sigE,sigU);
        
        # write the sigma data to the file
        sittbl.write(sigline+'\n');
    
    # clean up - make sure to close all the file handles
    src.close();  sittbl.close();  gamitAprFileHandle.close();

    # return path to resulting apr file
    return gamitAprFilePath
    
class Session(Processing.Session):
        
    def __init__(self):
        
        # call super class constructor
        super(Session,self).__init__();
        
        
    # @Override    
    def initialize(self):

        # create date object
        self.date = pyDate.Date(year=self.options['year'], doy=self.options['doy'])

        # check for pre-existing solution if lazy
        (solutionAlreadyExists, key) = Resources.soln_exists(
            self.date,
            self.options['expt'],
            self.options['org'],
            self.options['network_id']
        )

        if solutionAlreadyExists and self.isLazy:
            raise Processing.LazyException("file exists: " + key)

        # do all the program independent stuff
        super(Session,self).initialize();
        
        # get the resource bucket path
        bucket = self.get_resources_path();
        
        # get the apr file 
        apr_file = glob.glob(os.path.join(bucket,'*.apr'));
        
        # yell about it if not found
        if len(apr_file) != 1:
            raise GamitException('problem identifying APR resources in '+bucket);
        
        # create apr file
        wlapr2apr(os.path.join(bucket,apr_file[0]));
        
        # get the binaries for gamit
        self.files['bin']    = Resources.get_bin   ('gamit', self.work_dir_path);
        
        # get the tables for gamit
        self.files['tables'] = Resources.get_tables('gamit', self.work_dir_path);
        
        # create custom setup shell script
        self.files['setup_script_path'   ] = self.__create_setup_script()   ;
        
        # create custom run script
        self.files['run_script_path'     ] = self.__create_run_script()     ;
        
        # create the custom cleanup script
        self.files['teardown_script_path'] = self.__create_teardown_script();
    
    def __create_setup_script(self):
        
        year = Utils.get_norm_year_str(self.options['year']);
        doy  = Utils.get_norm_doy_str (self.options['doy' ]);
        
        setup_file_path = os.path.join(self.work_dir_path,'setup.sh');
        
        # open sittbl next to the incoming apr file
        try:
            setup_file = open(setup_file_path,'w');
        except:
            raise GamitException('could not open file '+setup_file_path);
        
        contents = \
        """
        # make sure we can find the program -- put local bin first
        export PATH=`pwd`/bin:${PATH}
        
        # unpack the tar.gz files
        for file in $(ls *.gz);do gunzip $file;done
        for file in $(ls *.tar);do tar -xf  $file;done
        
        # clean up
        rm *.tar
        
        # init the station info file
        echo "*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN " > tables/station.info;
        #cat resources/*.station.info >> tables/station.info
        for file in $(ls resources/*.station.info);do 
            cat $file >> tables/station.info;
            echo "* ">>tables/station.info;
        done
        
        
        # link apr and sigmas
        cd tables
        ln -s ../resources/sittbl. .
        ln -s ../resources/gamit.apr .
        cd ..
        
        """
        
        contents += \
        """
        # set up links
        cd tables;
        sh_links.tables -frame J2000 -year %s -eop %s -topt none > sh_links.out;
        cd ..;
        
        """ % (year,self.options['eop_type']);


        contents += \
        """
        # create the gfiles
        cp resources/*.sp3*  tables/
        cd tables
        gunzip *.sp3*;
        sed -e 's@OL/AL:NONE@OL/AL:@g' *.sp3 > tmp;  mv tmp *.sp3
        sh_sp3fit -f *.sp3 -o file -d %s %s -m 0.1 > sh_sp3fit.out
        cp gfile* ../resources/
        cd ..
        
        """ % (year,doy);
        
        contents += \
        """
        # link session table
        cd tables;
        ln -s sestbl.%s sestbl.
        cd ..;
        
        """  % (self.options['expt_type'].upper());
        
        
        contents += \
        """
        #
        # check all the rnx files have entry in apr sigma file
        #
        
        # move to the resource directory
        cd resources
        
        # decompress and uncompact all the d.Z file
        for file in $(ls *.[0-9][0-9]d.*);do  gunzip --force $file; done  
        for file in $(ls *.[0-9][0-9]d);  do  crx2rnx        $file; done
        
        # check each o-file 
        for file in $(ls *.[0-9][0-9]o);do 
        
                # get the station name
                name=`echo $file | cut -c 1-4 | tr [:lower:] [:upper:]`; 
        
                # figure out if it's in the sittbl.
                grep -q ${name} sittbl.
        
                # if not matched in the file ...
                if [ $? -ne 0 ]; then
        
                        # blab about it
                        echo "adding ${name} to resources/sittbl. with 9.999 apr sigma";
        
                        # initialize tmp file with existing apr sigmas
                        cat sittbl. > tmp;
        
                        # add the missing entry to the temp file
                        echo "${name} ${name}_GPS     NNN    99.99 99.99 99.99" >> tmp;
                        
                        # restore the apr sigma file 
                        mv tmp sittbl.; 
                fi 
        done
        
        # purge all apr sigma and use 99.99
        #cat sittbl. | sed -e 's/NNN    .*/NNN    99.99 99.99 99.99/g' > tmp && mv tmp sittbl.;
        #cat sittbl. | sed -e 's/100.000/99.000/g' -e 's/\.000/\.00/g' > tmp && mv tmp sittbl.;
        
        # restore directory
        cd ../;
        """
        
        # blurt to the file
        setup_file.write(contents);
        
        # all done
        setup_file.close();
        
        # add executable permissions
        os.system('chmod +x '+setup_file_path);
        
        # return the path for traceability
        return setup_file_path;

    def __create_run_script(self):
        
        year = Utils.get_norm_year_str(self.options['year']);
        doy  = Utils.get_norm_doy_str( self.options['doy'] );
        
        # init date object
        date = pyDate.Date(year=year,doy=doy);
        
        # extract the gps week and convert to string
        gpsWeek_str = str(date.gpsWeek);
        
        # normalize gps week string
        if date.gpsWeek < 1000: gpsWeek_str = '0'+gpsWeek_str
        
        # set the path and name for the run script
        run_file_path = os.path.join(self.work_dir_path,'run.sh');
        
        # open sittbl next to the incoming apr file
        try:
            run_file = open(run_file_path,'w');
        except:
            raise GamitException('could not open file '+run_file_path);
        
        contents = \
        """
        #!/bin/bash
        
        # should we iterate solution
        SHOULD_ITERATE=%s

        # set max depth for recursion
        MAX_LEVEL=3;
        
        # parse input
        level=$1; [ $# -eq 0 ] && level=1;
        
        # check that level less than max depth
        if [[ $level -gt $MAX_LEVEL ]];then
            # if so then exit
            echo "MAX ITERATION DEPTH REACHED ... MUST EXIT"
            exit 0;
        fi
        
        echo "Iteration depth: $level"

        # make sure we can find the program -- put local bin first!
        export PATH=`pwd`/bin:${PATH}
        
        # set the params
        EXPT=%s;
        YEAR=%s;
        DOY=%s;
        MIN_SPAN=%s;
        EOP=%s;
        
        # set the name of the outfile
        OUT_FILE=%s%s%s.out
        
        # execution flag for sh_gamit
        EXE=1;

        while [ $EXE -eq 1 ]; do

        # set exe to 0 so that we exit exe loop if no problems found                                                                                                                                   
        EXE=0;
        
        # do the damn thing 
        sh_gamit -expt $EXPT -d $YEAR $DOY -orbt file -minspan $MIN_SPAN -noftp -remakex Y -eop $EOP """ \
        % (self.options['should_iterate'],self.options['expt'],year,doy,self.options['minspan'],self.options['eop_type'],self.options['org'],gpsWeek_str,str(date.gpsWeekDay));

        # if we're in debug mode do not pipe output to file
        if not self.isDebug: contents += """ &> $OUT_FILE; """;

        contents += """

        grep -q "Geodetic height unreasonable"  $OUT_FILE;
        if [ $? -eq 0 ]; then
            sstn=`grep "MODEL/open: Site" $OUT_FILE  | tail -1 | cut -d ":" -f 5 | cut -d " " -f 3 |tr '[:upper:]' '[:lower:]'`;
            echo "deleting station ${sstn}: unreasonable geodetic height";
            rm resources/${sstn}* ;
            grep "MODEL/open: Site" $OUT_FILE  | tail -1
            echo "will try sh_gamit again ..."
            #sh_gamit -expt $EXPT -d $YEAR $DOY -orbt file -minspan $MIN_SPAN -noftp -remakex Y -eop $EOP &> $OUT_FILE
            EXE=1;
        fi
        
        grep "FATAL.*MAKEX/lib/rstnfo: No match for" $OUT_FILE
        if [ $? -eq 0 ];then
            sstn=`grep "FATAL.*MAKEX/lib/rstnfo: No match for" $OUT_FILE | tail -1 | cut -d ":" -f5 | awk '{print $4}' | tr '[:upper:]' '[:lower:]'`
            echo "deleting station ${sstn}: no station info";
            rm resources/${sstn}* ;
            echo "will try sh_gamit again ..."
            #sh_gamit -expt $EXPT -d $YEAR $DOY -orbt file -minspan $MIN_SPAN -noftp -remakex Y -eop $EOP &> $OUT_FILE
            EXE=1;
        fi
        
        grep -q "Error extracting velocities for"  $OUT_FILE;
        if [ $? -eq 0 ]; then
            sstn=`grep "Error extracting velocities for" $OUT_FILE  | head -1 | cut -d ":" -f 5 | cut -d " " -f 6 |tr '[:upper:]' '[:lower:]'`;
            echo "deleting station ${sstn}: Error extracting velocities for";
            rm resources/${sstn}* ;
            grep "Error extracting velocities for" $OUT_FILE  | tail -1
            echo "will try sh_gamit again ..."
            #sh_gamit -expt $EXPT -d $YEAR $DOY -orbt file -minspan $MIN_SPAN -noftp -remakex Y -eop $EOP &> $OUT_FILE
            EXE=1;
        fi
        
        grep -q    "Bad WAVELENGTH FACT" $OUT_FILE;
        if [ $? -eq 0 ]; then
            sstn=`grep "Bad WAVELENGTH FACT" $OUT_FILE | tail -1 | cut -d ":" -f 5 | cut -d " " -f 6 | cut -c 3-6`
            echo "deleting station ${sstn}: Bad WAVELENGTH FACT in rinex header";
            rm resources/${sstn}*;
            echo "will try sh_gamit again ...";
            EXE=1;
        fi
        
        grep -q    "Error decoding swver" $OUT_FILE;
        if [ $? -eq 0 ]; then
            grep       "Error decoding swver" $OUT_FILE;
            sstn=`grep "Error decoding swver" $OUT_FILE | tail -1 | awk '{print $8}' | tr '[:upper:]' '[:lower:]'`
            echo "deleting station ${sstn}: Error decoding swver";
            rm resources/${sstn}*;
            echo "will try sh_gamit again ...";
            EXE=1;
        fi
        
        grep -q    "FATAL.*MAKEX/lib/hisub:  Antenna code.*not in hi.dat" $OUT_FILE;
        if [ $? -eq 0 ]; then
            grep       "FATAL.*MAKEX/lib/hisub:  Antenna code.*not in hi.dat" $OUT_FILE;
            sstn=`grep "FATAL.*MAKEX/lib/hisub:  Antenna code.*not in hi.dat" $OUT_FILE | tail -1 | awk '{print $9}' | cut -c2-5 | tr '[:upper:]' '[:lower:]'`
            echo "deleting station ${sstn}: Antenna code not in hi.dat";
            rm resources/${sstn}*;
            echo "will try sh_gamit again ...";
            EXE=1;
        fi
        
        done
                
        # clean up
        rm -rf ionex met teqc*
        
        # blab about falures
        grep "FATAL" *.out
        
        # copy the out file to the solutions direcoty if it exists
        [ -d ./solutions/* ] && cp *.out ./solutions/*;
        
        """ ;

        run_file.write(contents);
        
        contents = \
        """
        # remove extrainious solution files
        rm ./solutions/*/l*[ab].*;
        
        # decompress the remaining solution files
        gunzip ./solutions/*/*;
        
        # make sure to rename the gfilea to the correct gfile[0-9].doy
        [ -e ./solutions/*/gfilea.* ] && mv -f ./solutions/*/gfilea* ./solutions/*/gfile[0-9]*
        
        # see if any of the coordinates were updated, exit if not
        grep Updated ./solutions/*/l*.*; [ $? -ne 0 ] && exit 
        
        # if we should not iterate then exit now
        [ $SHOULD_ITERATE == "no" ] && exit
        
        # recreate the apr file with updated coordinates minus the comments
        sed -e 's/Updated from l.....\.[0-9][0-9][0-9]//g' ./solutions/*/l*.* > ./resources/gamit.apr;
        
        # I think we should copy over the gamit.apr
        
        # copy over an updated gfile if it exists
        #[ -e ./solutions/*/gfilea.* ] && mv -f ./solutions/*/gfilea.* ./resources/gfile%s.%s
        cp ./solutions/*/gfile* ./resources/
        
        # update level
        level=$((level+1));
        
        # remove the 'old' solution
        [ $level -le $MAX_LEVEL ] && rm -rf ./solutions/*;
        
        # do another iteration
        [ $SHOULD_ITERATE == "yes" ] && ./run.sh $level;
        
        """ % (year[-1],doy);
        
        run_file.write(contents);

        # all done
        run_file.close();
        
        # add executable permissions
        os.system('chmod +x '+run_file_path);
        
        # return path
        return run_file_path;

    def __create_teardown_script(self):
        
        # create normalized versions of the year and day of year
        year = Utils.get_norm_year_str(self.options['year']);
        doy  = Utils.get_norm_doy_str( self.options['doy'] );
        
        # initialize a date object
        date = pyDate.Date(year=year, doy=doy);
        
        # extract the gps week and day of week
        gps_week = date.gpsWeek;  gps_week_day = date.gpsWeekDay;
        
        # extract the gps week and convert to string
        gpsWeek_str = str(date.gpsWeek);
        
        # normalize gps week string
        if date.gpsWeek < 1000: gpsWeek_str = '0'+gpsWeek_str
        
        teardown_file_path = os.path.join(self.work_dir_path,'teardown.sh');
        
        # open sittbl next to the incoming apr file
        try:
            teardown_file = open(teardown_file_path,'w');
        except:
            raise GamitException('could not open file '+teardown_file_path);
        
        contents = \
        """
        #!/bin/bash

        # make sure we can find the program
        export PATH=${PATH}:`pwd`/bin
        
        # set the name of the outfile
        FILE=%s%s%s
        
        # move to the solution path
        cd ./solutions/*
        
        # make sure an h file exists, if not exit
        [ ! -f h* ] && exit ;
        
        # link the svnav.dat file
        ln -s ../../tables/svnav.dat .
        
        # create the binary h-file
        htoglb . tmp.svs h*  >> ../../${FILE}.out
        
        # convert the binary h-file to sinex file
        glbtosnx . "" h*.glx ${FILE}.snx >> ../../${FILE}.out
        
        # clean up
        rm HTOGLB.* *.gl* tmp.svs l*  svnav.dat
        
        # move back to home
        cd ../../;
        
        """ % (self.options['org'], gpsWeek_str, str(gps_week_day))

        # dump contents to the script file
        teardown_file.write(contents);
        
        if self.options['expt_type'] == 'relax':
        
            # create an sp3 file from the g-file
            contents  = \
            """
            # move to the solutions directory
            cd ./solutions/*
            
            # make temporary directory
            mkdir tmp
            
            # copy the gfile to temp dir
            cp gfile* tmp/
            
            # move to the temp dir
            cd tmp;
            
            # do the damn thing
            mksp3.sh %s %s %s
            
            # copy the sp3 file to solution dir if exists
            [ -e *.sp3 ] && mv *.sp3 ..;
            
            # move out of temporary directory
            cd ..;
            
            # clean up
            rm -rf tmp gfile*;
            
            # back to home directory
            cd ../..
            
            """ % (year,doy,self.options['org']);
            
            teardown_file.write(contents);
        
        contents = \
        """
        # move to the solutions directory
        cd ./solutions/*
        
        # rename o file to znd file
        if [ -f o*a.[0-9][0-9][0-9]* ]; then
            mv -f o*a.[0-9][0-9][0-9]* %s%s%s.znd;
        fi
        
        # remove a priori o file
        if [ -f o*p.[0-9][0-9][0-9]* ]; then
            rm -f o*p.[0-9][0-9][0-9]*;
        fi
        
        # restore home dir
        cd ../..
        
        """ % (self.options['org'], gpsWeek_str, str(gps_week_day));
        
        teardown_file.write(contents);
        
        contents = \
        """
        # move to the solutions directory
        cd ./solutions/*
        
        # clean up
        rm -rf gfile*
        
        # compress remaining files
        for file in $(ls);do gzip --force $file; done
        
        # return to home directory
        cd ../..
        
        """
        
        teardown_file.write(contents);
        
        # make sure to close the file
        teardown_file.close();
        
        # add executable permissions
        os.system('chmod +x '+teardown_file_path);
        
        # return path
        return teardown_file_path;
    
    def relative_solution_path(self):
        
        # create normalized versions of the year and day of year
        year = Utils.get_norm_year_str(self.options['year']);
        doy  = Utils.get_norm_doy_str( self.options['doy'] );
        
        return os.path.join('solutions',year+'_'+doy);
    
    def pushH(self,prog_id):
        
        # define where and what 
        h_file_descriptor = os.path.join(self.get_local_solutions_dir(),'h*.[0-9][0-9][0-9][0-9][0-9]*');
        
        # query for file listing
        h_file_list = glob.glob(h_file_descriptor); 
        
        # push each snx file
        for h_file in h_file_list:
            print "pushing hfile: ",h_file
            Resources.pushSNX(self.get_solution_bucket(prog_id), h_file);
    
    def pushO(self,prog_id):
        
        # define where and what 
        file_descriptor = os.path.join(self.get_local_solutions_dir(),'o*a.[0-9][0-9][0-9]*');
        
        # query for file listing
        file_list = glob.glob(file_descriptor); 
        
        # push each snx file
        for file in file_list:
            print "pushing ofile: ",file
            Resources.pushSNX(self.get_solution_bucket(prog_id), file);
            
    def pushZND(self,prog_id):
        
        # define where and what 
        file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.znd*');
        
        # query for file listing
        file_list = glob.glob(file_descriptor); 
        
        # push each snx file
        for file in file_list:
            print "pushing znd file: ",file
            Resources.pushSNX(self.get_solution_bucket(prog_id), file);
            
    def pushSp3Local(self,prog_id):
        
        #put a copy of the sp3 file in the solution directory
        
        # define where and what 
        file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.sp3*');
        
        # query for file listing
        file_list = glob.glob(file_descriptor); 
        
        # push each snx file
        for file in file_list:
            print "pushing sp3 file: ",file
            Resources.pushSNX(self.get_solution_bucket(prog_id), file);
     
    def getStatus(self):
        
        # call super class definition
        status = super(Session,self).getStatus();
        
        # out files to match
        out_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.out*');

        # soln files to match
        soln_file_descriptor = os.path.join(self.get_local_solutions_dir(), '*.snx*');
            
        # look for out files to get status from
        out_file_list = glob.glob(out_file_descriptor);

        # look for soln files to get status from
        soln_file_list = glob.glob(soln_file_descriptor);
        
        # if no out files ... not a good sign
        if len(out_file_list) == 0:
            status['status'] = False;
            return status;

        # if no solution files ... oi vey
        if len(soln_file_list) == 0:
            status['solution'] = False;
        else:
            status['solution'] = True;

        # create regular expression to match keyword
        pattern = re.compile('.*FATAL.*');
        
        # look through out files and check for key word 
        for ofile in out_file_list:
            f = gzip.open(ofile);
            for line in f:
                if pattern.match(line):
                    status['status'] = False;
                    return status;
                
        # OK, no keyword found so all good
        status['status'] = True;
        
        # that's all folks
        return status;
    
    def pushStatus(self):
        
        # get the status
        status = self.getStatus();

        # create a connection to SQS
        conn = SQSConnection();
        
        # ask for the QUEUE
        q = conn.get_queue(QUEUE);
        
        # create a new message
        m = Message();
    
        # set the message body to the status
        m.set_body(str(status));
        
        # publish the message to SQS
        q.write(m);
        
        # blab about it for now
        print str(status);
            
    def finalize(self):
        
        if self.isDebug: os.sys.stdout.write('ignoring finalize() in debug mode ... \n'); return;
        
        # create mat files from sinex files
        for snx in self.getSNX(): self.mk_mat(snx);
        
        # file away the data products
        self.pushSNX('');
        self.pushOUT('');
        self.pushZND('');
        self.pushMAT('');
        self.pushSP3(  );
        
        # put a copy of the sp3 file in the soln dir
        self.pushSp3Local('');
        
        # publish sucess or failure
        self.pushStatus();
    
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
        
    except GamitException as err:
        
        # blab about the exception details and exit
        os.sys.stderr.write(str(err));
        
    finally:
        
        session.dispose();
    
if __name__ == '__main__':
    
    main()