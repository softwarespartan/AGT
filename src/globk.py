#!/usr/bin/python

import os, re, glob, Utils, Processing, Resources, pyDate, snxParse, snx2mat, scipy.io, gamit;


class GlobkException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Session(Processing.Session):
        
        
    def __init__(self):
        
        # call super class constructor
        super(Session,self).__init__();
        
        
    # @Override    
    def initialize(self):
        
        # no call to super.initialize().  just create work dir ourselves
        
        year = Utils.get_norm_year_str(self.options['year']);
        doy  = Utils.get_norm_doy_str( self.options['doy'] );
        
        # init date object
        date = pyDate.Date(year=year,doy=doy);

        # create date object
        #self.date = pyDate.Date(year=self.options['year'], doy=self.options['doy'])

        # check for pre-existing solution if lazy
        (solutionAlreadyExists, key) = Resources.soln_exists(
            date,
            self.options['expt'],
            self.options['org'],
            self.options['network_id']
        )

        if solutionAlreadyExists and self.isLazy:
            raise Processing.LazyException("file exists: " + key)
        
        # make sure we have something specified to work with
        if len(self.src) == 0: 
            raise GlobkException('no src has been specified');
              
        # make sure that work directory has been initialized
        if not self.is_valid():
            raise GlobkException('invalid session state');    
         
        # make sure the the temporary directory does not already exist
        if os.path.isdir(self.work_dir_path):
            raise GlobkException(
                'temporary work directory '+self.work_dir_path+' already exists'
            );
        
        # attempt to create the work directory
        try:
            # make parent dirs also
            os.makedirs(self.work_dir_path    , 0755);
            os.makedirs(self.get_resources_path(), 0755);
        except Exception, e:
            
            # unsuccessful attempt
            raise GlobkException(str(e));
        
        # get the resource bucket path
        bucket = self.get_resources_path();
        
        # get the binaries for gamit/globk
        self.files['bin']    = Resources.get_bin   ('gamit', self.work_dir_path);
        
        # get the tables for gamit/globk
        self.files['tables'] = Resources.get_tables('gamit', self.work_dir_path);
        
        # init empty list of snx files
        self.files['snx'] = list();
        
        self.files['apr'] = Resources.get_apr(                          \
                                              self.options['year'    ], \
                                              self.options['doy'     ], \
                                              list()                  , \
                                              self.get_resources_path() \
                                             );
                                             
        # get the apr file 
        #apr_file = glob.glob(os.path.join(bucket,'*.apr'));
        
        # yell about it if not found
        #if len(apr_file) != 1:
        #    raise GlobkException('problem identifying APR resources in '+bucket);
        
        # create apr file
        #gamit.wlapr2apr(os.path.join(bucket,apr_file[0]));
        
        # number of days on each side of the 
        dt = 0;
        
        # compute the start and stop dates
        start_date = pyDate.Date(mjd=(date.mjd-dt));
        stop_date  = pyDate.Date(mjd=(date.mjd+dt));
        
        # get the snx files for each source
        for src in self.src:
            
            #print re.split(':',src),bucket
            
            # date to iterate with 
            __date__ = start_date;
            
            # make sure the src is valid
            if len(re.split(':',src)) != 2:
                raise GlobkException('invalid src specification: '+src+'.  use --src=expt:org');
            
            # parse the src
            expt,org = re.split(':',src);
            
            while __date__.mjd <= stop_date.mjd:
            
                # get the bucket for this src
                soln_bucket = Processing.solution_bucket(                             \
                                                         __date__.year              , \
                                                         __date__.doy               , \
                                                         ''                         , \
                                                         expt                       , \
                                                         org                        , \
                                                         None                         \
                                                        );
                                                    
                print soln_bucket
                                                                    
                # ok get the snx with this bucket prefix
                self.files['snx'] += Resources.get_snx(soln_bucket, bucket);
                
                # update the date
                __date__ = pyDate.Date(mjd=(__date__.mjd+1));
            
            
        
        # create custom setup shell script
        self.files['setup_script_path'   ] = self.__create_setup_script()   ;
        
        # create custom run script
        self.files['run_script_path'     ] = self.__create_run_script()     ;
        
        # create the custom cleanup script
        self.files['teardown_script_path'] = self.__create_teardown_script();
    
    
    def __create_setup_script(self):
        
        setup_file_path = os.path.join(self.work_dir_path,'setup.sh');
        
        # open sittbl next to the incoming apr file
        try:
            setup_file = open(setup_file_path,'w');
        except:
            raise GlobkException('could not open file '+setup_file_path);
        
        contents = \
        """
        #!/bin/bash
        
        # make sure we can find the program
        export PATH=${PATH}:`pwd`/bin
        
        # initialize the solutions directory
        [ ! -d solutions ] && mkdir solutions
        
        # unpack the tar.gz files
        for file in $(ls *.gz);do gunzip $file;done
        for file in $(ls *.tar);do tar -xf  $file;done
        
        # unpack sinex files
        for file in $(find . -name "*.snx.*" -print ); do gunzip $file;done
    
        # convert files to binary files for globk
        for file in $(find . -name "*.snx" -print);do ./bin/htoglb `dirname $file` test.svs $file;done 2>&1 > ./solutions/htoglb.out
            
        # clean up a little more
        rm *.tar
        
        """
        
        # blurt to the file
        setup_file.write(contents);
        
        # all done
        setup_file.close();
        
        # add executable premissions
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
            raise GlobkException('could not open file '+run_file_path);
        
        contents = \
        """
        #!/bin/bash
        
        # make sure we can find the program
        export PATH=${PATH}:`pwd`/bin

        # data product file names
        OUT_FILE=%s%s%s;

        # mk solutions directory for prt files etc
        [ ! -d solutions ] && mkdir solutions

        # move to tables dir for globk execution
        cd tables;
    
        # create global directory listing for globk
        for file in $(find .. -name "*.gls" -print);do echo $file;done | grep    "\/n0\/"  > globk.gdl
        for file in $(find .. -name "*.gls" -print);do echo $file;done | grep -v "\/n0\/" >> globk.gdl
    
        # create the globk cmd file
        echo " app_ptid all"                                                         > globk.cmd
        echo " prt_opt GDLF MIDP CMDS"                                              >> globk.cmd
        echo " out_glb ../solutions/file.GLX"                                       >> globk.cmd
        echo " in_pmu pmu.usno"                                                     >> globk.cmd
        echo " descript Daily combination of global and regional solutions"         >> globk.cmd
        echo " apr_wob    10 10  10 10 "                                            >> globk.cmd
        echo " apr_ut1    10 10        "                                            >> globk.cmd
        echo " max_chii  1. 0.6"                                                    >> globk.cmd
        echo " apr_svs all 0.05 0.05 0.05 0.005 0.005 0.005 0.01 0.01 0.00 0.01 FR" >> globk.cmd
        echo " apr_neu  all       00.3   00.3   00.3   0 0 0"                       >> globk.cmd
        #cat ../resources/*.apr | sed -n '2,$p' | while read line; do
        #
        #        stn=`echo $line| awk '{print $1}' |cut -d"." -f2`;
        #        sign=`echo $line | awk '{print $5}'`;
        #        sige=`echo $line | awk '{print $6}'`;
        #        sigu=`echo $line | awk '{print $7}'`;
        #        echo " apr_neu  $stn  $sign  $sige  $sigu  0 0 0"                   >> globk.cmd;
        #done
        
        # create the sinex header file
        echo "+FILE/REFERENCE                               " >  head.snx 
        echo " DESCRIPTION       The Ohio State University  " >> head.snx                          
        echo " OUTPUT            GPS Combined Solution      " >> head.snx 
        echo " CONTACT           mbevis@osu.edu             " >> head.snx 
        echo " SOFTWARE          glbtosnx Version           " >> head.snx  
        echo " HARDWARE          .                          " >> head.snx                                  
        echo " INPUT             Globk combined binary files" >> head.snx                                       
        echo "-FILE/REFERENCE                               " >> head.snx
        
        # run globk 
        globk 0 ../solutions/file.prt ../solutions/globk.log globk.gdl globk.cmd 2>&1 > ../solutions/globk.out
    
        # convert the GLX file into sinex
        glbtosnx ../solutions/ ./head.snx ../solutions/file.GLX ../solutions/${OUT_FILE}.snx 2>&1 > ../solutions/glbtosnx.out
    
        # restore original directory
        cd ..;
        
        # move to solutions directory to create log file
        cd ./solutions;
        
        # figure out where the parameters start in the prt file
        LINE=`grep -n "PARAMETER ESTIMATES" file.prt | cut -d ":" -f1`
        
        # reduce line by one to make a little cleaner
        let LINE--;
        
        # print prt header
        sed -n 1,${LINE}p file.prt > ${OUT_FILE}.out
        
        # append the log file
        cat globk.log >> ${OUT_FILE}.out
        
        # create the fsnx file which contains only the solution estimate
        lineNumber=`grep --binary-file=text -m 1 -n "\-SOLUTION/ESTIMATE" ${OUT_FILE}.snx | cut -d : -f 1`

        # extract the solution estimate
        head -$lineNumber ${OUT_FILE}.snx > ${OUT_FILE}.fsnx;
        
        # restore original directory
        cd ../
        
        """ % (self.options['org'],gpsWeek_str,str(date.gpsWeekDay));

        run_file.write(contents);
        
        # all done
        run_file.close();
        
        # add executable premissions
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
        
        teardown_file_path = os.path.join(self.work_dir_path,'teardown.sh');
        
        # open sittbl next to the incoming apr file
        try:
            teardown_file = open(teardown_file_path,'w');
        except:
            raise GlobkException('could not open file '+teardown_file_path);
        
        contents = \
        """
        #!/bin/bash
        
        # clear out log files
        rm -f ./solutions/file*
        rm -f ./solutions/globk*
        rm -f ./solutions/glb*
        rm -f ./solutions/hto*
        
        # clean up a little more
        rm -f HTOGLB* test.svs
        
        # clean up tables directory
        rm -f ./tables/GLBSOL.BIN
        rm -f ./tables/GLBSOR.BIN
        rm -f ./tables/GLOBK.*
        rm -f ./tables/head.snx
        rm -f ./tables/globk.cmd
        rm -f ./tables/globk.gdl
        
        # clean out all the binary sinex files
        find . -name "*.gls" -print | xargs -n1 rm -f
        
        # compress sinex file
        gzip --force ./solutions/*.snx
        gzip --force ./solutions/*.fsnx
        gzip --force ./solutions/*.out
        
        """
        
        teardown_file.write(contents);
        
        # make sure to close the file
        teardown_file.close();
        
        # add executable premissions
        os.system('chmod +x '+teardown_file_path);
        
        # return path
        return teardown_file_path;  
    
    
    # @Overides
    def relative_solution_path(self):
        return os.path.join('solutions');
    
    
    def finalize(self):
        
        for snx in self.getSNX():
            self.mk_mat(snx);
        
        self.pushSNX('');
        self.pushOUT('');
        self.pushMAT('');

def main():

    # initialize a new Processing.Session
    session = Session(); 
     
    # initialization    
    try:
        
        # populate using the system input arguments
        session.configure_with_args(os.sys.argv)
        
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
        
    except GlobkException as err:
        
        # blab about the exception details and exit
        os.sys.stderr.write(str(err));
        
    finally:
        
        session.dispose();
                
    
if __name__ == '__main__':
    
    main()