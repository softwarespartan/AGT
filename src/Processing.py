"""
Created on Feb 9, 2013

@author: abelbrown
"""

import datetime     ;
import re           ;
import os,sys,getopt;
import Utils        ;
import Resources    ;
import glob         ;

MIN_YEAR     = 1992;
MIN_SPAN_MIN = 6   ;
MIN_SPAN_MAX = 23  ;

AGT_WORK_ROOT_DEFAULT = os.path.expanduser('~');
AGT_WORK_ROOT_ENV_VAR = 'AGT_WORK_ROOT'        ;


class SessionException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
def solution_bucket(year,doy,prog_id,expt,org,network_id=None):
    
    # create normalized versions of the year and day of year
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    path = os.path.join(
                        year                      ,
                        doy                       ,
                        prog_id                   ,
                        expt                      ,
                        org
                    );
                
    # if the network id was specified then tack it on
    if network_id != None: path = '/'.join((path,network_id));
    
    # that's all
    return path;

class Session(object):

    def __init__(self):
        
        self.stn_list = []; self.src = [];

        self.options = {
                       'year'           : None       ,
                       'doy'            : None       ,
                       'eop_type'       : 'usno'     ,
                       'expt_type'      : 'baseline' ,
                       'minspan'        : 12         ,
                       'should_iterate' : 'yes'      ,
                       'sp3_type'       : 'ig1'      ,
                       'org'            : 'tmp'      ,
                       'expt'           : 'none'     ,
                       'network_id'     : 'n0'       ,
                       'dns'            : 'osf.gamit',
                       };
                       
        self.work_dir_path = None;
        
        self.files = dict();
        
        self.isDebug = False;
                       
    def configure_with_args(self,argv):
        
        # init long arguments
        longArgs = [op+'=' for op in self.options.keys()];
        
        # tack on the stn src and debug args
        longArgs.append('stn='); longArgs.append('src='); longArgs.append('debug')
        
        # prep argv options
        for e in argv:
            if not e.startswith('--'):
                if e.startswith('-'):
                    os.sys.stderr.write('ignoring short arg: '+e+'\n'); 
                argv.remove(e);
          
        # parse system arguments  
        try:
            opts,args = getopt.getopt(argv, [], longArgs)
        
        except getopt.GetoptError, err:
            
            # print help information and exit:
            os.sys.stderr.write(str(err)+'\n');
            
            # that's all we can do here
            sys.exit(2);
            
        # assign parsed arguments
        for option,arg in opts:
            
            # prepare the option and the associated argument
            option = option.lower().replace('--','');  arg = arg.strip().lower();
                
            # assign to options if option is configuration element
            if option in self.options.keys(): self.options[option] = arg; continue;
                
            # process station specifications
            if option == 'stn' : self.stn_list.append(arg); 
                
            # process station list specification    
            if option == 'stn_list': self.stn_list += re.split(",",arg); 
            
            # process globk src specification
            if option == 'src': self.src.append(arg);
            
            # process debug option
            if option == 'debug': self.isDebug = True;
            
        # ok one last thing, compute a working directory name
        self.work_dir_path = self.compute_work_dir_path();    
        
        # that's all folks
        return self;
    
    
    def validate(self):
        
        # check the year is specified
        if self.options['year'] is None: 
            raise SessionException('must specify integer year as --year=YYYY');
        
        # make sure that year is a number
        try:
            # atoi
            int(self.options['year']);
        except:
            raise SessionException('must specify integer year as --year=YYYY');
        
        # make sure that year is big enough
        if int(self.options['year']) < MIN_YEAR:
            raise SessionException('must specify year greater than '+str(MIN_YEAR));
        
        # make sure that year is not too big
        if  int(self.options['year']) > datetime.datetime.now().year:
            raise SessionException('year is too big');
        
        # check the doy is specified
        if self.options['doy'] is None: 
            raise SessionException('must specify integer doy using --doy=');
        
        # make sure that doy is a number
        try:
            # parse to int
            int(self.options['doy']);
        except:
            raise SessionException('must specify integer doy using --doy=');
        
        # make sure that year is big enough
        if int(self.options['doy']) < 1 or int(self.options['doy']) > 366:
            raise SessionException('must specify doy between 1 and 366');
        
        # make sure that the expt is specified as char
        if not type(self.options['expt']) is str:
            raise SessionException('must specify expt as 4-char using --expt=abcd');
        
        # make sure that the expt has length exactly 4
        if len(self.options['expt']) != 4:
            raise SessionException('must specify expt as 4-char using --expt=abcd');
        
        # make sure that the eop type is valid
        if self.options['eop_type'] not in ('usno','bull_b'):
            raise SessionException('eop type must be usno or bull_b');
        
        # make sure that experiment type is valid key words
        if self.options['expt_type'] not in ('baseline','relax'):
            raise SessionException('expt_type must be BASELINE or RELAX');
        
        # make sure that minspan is an integer
        try:
            # cast as integer
            int(self.options['minspan']);
        except:
            raise SessionException('specify integer minimum span between '+str(MIN_SPAN_MIN)+' and '+str(MIN_SPAN_MAX)+' hours using --minspan=');
        
        # make sure that minspan is within the appropriate ranges
        if int(self.options['minspan']) < MIN_SPAN_MIN or int(self.options['minspan']) > MIN_SPAN_MAX:
            raise SessionException('specify integer minimum span between '+str(MIN_SPAN_MIN)+' and '+str(MIN_SPAN_MAX)+' hours using --minspan=');
         
        # make sure that should_iterate is a boolean
        if self.options['should_iterate'] not in ('yes','no'):
            raise SessionException('specify iteration preference as yes/no using --should_iterate=');
            
        # make sure that sp3 ephemeris type is three characters
        if len(self.options['sp3_type']) != 3:
            raise SessionException('specify 3-char sp3 type using --sp3_type=');
        
        # make sure that sp3 ephemeris type is three characters
        if len(self.options['org']) != 3:
            raise SessionException('specify 3-char org type using --org=');
        
        if self.options['network_id'] != None:
            
            # compile regular expression to match things like: n1 n34 n4332
            regex = re.compile("(n\d+)"); 
            
            # apply regular expression to the specified network id
            match = regex.findall(self.options['network_id']);
            
            # make sure that specified network produced a match
            if len(match) == 0:
                raise SessionException('specify network id using --network_id=n123');
            
        # make sure that a metadata name space has been 
        # specified and if so that it has been specified correctly
        if self.options['dns'] is None:
            raise SessionException('must specify metadata name space using --dns=');
        
        # check that the station list has only unique station id
        if len(self.stn_list) != len(set(self.stn_list)):
            raise SessionException('duplicate stnId detected');
        
        # time for a beer after all that!
        return self;
    
    
    def dump(self):
        
        # specify the print format string
        fmt = "%-14s : %-10s";
        
        # dump the k,v options using format string
        for k,v in self.options.iteritems(): print fmt % (k,v)
            
        # print the list of stations in the same fashion 
        print fmt % ('stn_list',', '.join(self.stn_list))
        
        # print the list of stations in the same fashion 
        print fmt % ('src',', '.join(self.src))

        # print the number of stations in the run
        print fmt % ('num_stn',len(self.stn_list))

        # print out the work directory name 
        print fmt % ('work directory',self.work_dir_path);


    def is_valid(self):
        
        if self.options['year'] is None        \
            or self.options['doy'] is None     \
                or self.work_dir_path is None:
            return False;
        else:
            return True;
    
    
    def compute_work_dir_path(self):
    
        if self.options['year'] is None or self.options['doy'] is None:
            raise SessionException('invalid state: year or doy not set');
    
        # make sure year is 4 digits
        year = Utils.get_norm_year_str(self.options['year']);
        
        # make sure doy is 3 digits
        doy  = Utils.get_norm_doy_str(self.options['doy']);
        
        # figure out what our process id is
        pid      = str(os.getpid());
        
        # create the directory name
        name = '.'.join([self.options['expt'],self.options['org'],pid, year,doy]);
        
        # see if the host has defined work root
        if AGT_WORK_ROOT_ENV_VAR in os.environ:
            root = os.environ[AGT_WORK_ROOT_ENV_VAR];
        else:
            # otherwise, use default work root
            root = AGT_WORK_ROOT_DEFAULT;
        
        # return simple 
        return os.path.join(root,name)


    def relative_solution_path(self):
        
        return 'solutions';
    
    
    def get_local_solutions_dir(self):
        
        return os.path.join(self.compute_work_dir_path(),self.relative_solution_path());


    def get_resources_path(self):
        
        # make sure that work directory has been initialized
        if self.work_dir_path is None:
            raise SessionException('invalid session state: work directory has not been set');
        
        return os.path.join(self.work_dir_path, Resources.WL_RESOURCES_LOCAL);
     
     
    def get_solution_bucket(self,prog_id):
        
        return solution_bucket(                           
                             self.options['year']       , 
                             self.options['doy' ]       , 
                             prog_id                    , 
                             self.options['expt']       , 
                             self.options['org' ]       , 
                             self.options['network_id']   
                            )
 
     
    def initialize(self):
              
        # make sure that work directory has been initialized
        if not self.is_valid():
            raise SessionException('invalid session state');    
         
        # make sure the the temporary directory does not already exist
        if os.path.isdir(self.work_dir_path):
            raise SessionException(                           
                                   'temporary work directory '
                                   +self.work_dir_path        
                                   +' already exists'         
                                  );
        
        # attempt to create the work directory
        try:
            # make parent dirs also
            os.makedirs(self.work_dir_path       , 0755);
            os.makedirs(self.get_resources_path(), 0755);
        except Exception, e:
            
            # unsuccessful attempt
            raise SessionException(str(e));
        
        # get the sp3 files
        self.files['sp3'] = Resources.get_sp3(                          
                                              self.options['year'    ], 
                                              self.options['doy'     ], 
                                              self.options['sp3_type'], 
                                              self.get_resources_path() 
                                             );
        
        # get the nav files
        self.files['nav'] = Resources.get_nav(                          
                                              self.options['year'    ], 
                                              self.options['doy'     ], 
                                              'auto'                  , 
                                              self.get_resources_path() 
                                             );
        
        # get the rnx files
        self.files['rnx'] = Resources.get_rnx_parallel(
                                              self.options['year'    ],
                                              self.options['doy'     ],
                                              self.stn_list           ,
                                              self.get_resources_path()
                                             );
        
        # get the station info  files
        self.files['stn_info'] = Resources.get_stn_info(
                                              self.options['year'    ],
                                              self.options['doy'     ],
                                              self.stn_list           ,
                                              self.get_resources_path()
                                             );
                         
        # get the apr files
        self.files['apr'] = Resources.get_apr(                          
                                              self.options['year'    ], 
                                              self.options['doy'     ], 
                                              self.options['dns'     ], 
                                              self.get_resources_path() 
                                             );
     
         
    def dispose(self):
        
        if self.isDebug: os.sys.stdout.write('ignoring dispose() in debug mode ... \n'); return;
        
        if not self.work_dir_path is None:
            os.system('rm -rf '+self.work_dir_path);
       
       
    def pushSNX(self,prog_id):
        
        # define where and what 
        snx_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*snx*');
        
        # query for file listing
        snx_file_list = glob.glob(snx_file_descriptor); 
        
        # push each snx file
        for snx_file in snx_file_list:
            print "pushing solution: ",snx_file
            Resources.pushSNX(self.get_solution_bucket(prog_id), snx_file);
            
            
    def pushOUT(self,prog_id):
       
        # define where and what 
        out_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.out*');
        
        # query for file listing
        out_file_list = glob.glob(out_file_descriptor); 
        
        # push each out file
        for out_file in out_file_list:
            #print "pushing out file: ",out_file
            Resources.pushSNX(self.get_solution_bucket(prog_id), out_file);
         
            
    def getSNX(self):
       
        # define where and what 
        mat_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.snx*');
        
        # query for file listing
        return glob.glob(mat_file_descriptor); 

            
    def pushMAT(self,prog_id):
       
        # define where and what 
        mat_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.mat.gz');
        
        # query for file listing
        mat_file_list = glob.glob(mat_file_descriptor); 
        
        if len(mat_file_list) == 0:
            # define where and what 
            mat_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.mat');
        
            # query for file listing
            mat_file_list = glob.glob(mat_file_descriptor);
            
        # push each out file
        for mat_file in mat_file_list:
            #print "pushing mat file: ",mat_file
            Resources.pushSNX(self.get_solution_bucket(prog_id), mat_file);
            
            
    def pushSP3(self):
       
        # define where and what 
        sp3_file_descriptor = os.path.join(self.get_local_solutions_dir(),'*.sp3*');
        
        # query for file listing
        sp3_file_list = glob.glob(sp3_file_descriptor); 
        
        # push each out file
        for sp3_file in sp3_file_list: 
            #print "pushing sp3 file: ",sp3_file
            Resources.pushSP3(sp3_file);
        
            
    def exe(self):
        
        if self.isDebug: os.sys.stdout.write('ignoring exe() in debug mode ... \n'); return;
        
        # move to the working dir
        run_str = 'cd '+self.work_dir_path+'; ';
        
        # run setup, execution, and tear down
        run_str += './setup.sh && ./run.sh && ./teardown.sh;';
        
        # invoke the command on the system
        status = os.system(run_str);
        
        # return the status
        return status;
    
    
    def getStatus(self):
        
        # make a copy of the options
        status = self.options.copy();
        
        # add the status field (default unknown)
        status['status'] = None;
        
        # return a string since likely going to msg this 
        return status;
    
    
    def mk_mat(self,snxfile):
        
        # minimize depencencies if not interested in mat files
        import pyDate   ;
        import snxParse ;
        import snx2mat  ;
        import scipy.io ;
        import gzip     ;
        
        # get the date from the sinex file
        gpsWeek    = int(os.path.basename(snxfile)[3:7]);
        gpsWeekDay = int(os.path.basename(snxfile)[7  ]);
        
        # compute a data from the information
        date = pyDate.Date(gpsweek=gpsWeek,gpsweekday=gpsWeekDay);
        
        # parse the file path in to dir and name
        file_path,file_name = os.path.split(snxfile);
        
        # create the output file name
        file_name = file_name.split('.')[0];
                    
        # make full path for solution file
        solnFilePath = os.path.join(file_path,file_name);
        
        # init sinex parser for current sinex file   
        snxParser = snxParse.snxFileParser(snxfile).parse();
    
        # construct npvs and npvs sigma from the sinex data
        npvs,npvs_sigma = snx2mat.npv(snxParser.stationDict);
    
        # create station list from dictionary keys
        stn_list = snxParser.stationDict.keys();
        
        # compute epoch in fractional year
        epochs = date.fyear;
        
        #extract the variance factor
        var_factor = snxParser.varianceFactor;
            
        # save as a mat file
        scipy.io.savemat(solnFilePath, mdict={'stnm'      :stn_list   ,  
                                              'epochs'    :epochs     ,  
                                              'npvs'      :npvs       ,  
                                              'npv_sigma' :npvs_sigma ,  
                                              'var_factor':var_factor},  
                         oned_as = 'column');

        # if we have a mat file then gzip it
        if os.path.isfile(solnFilePath+'.mat'):

            # gzip the file up with open file handles
            with open(solnFilePath+'.mat', 'rb') as orig_file:
                with gzip.open(solnFilePath+'.mat.gz', 'wb') as zipped_file:
                    zipped_file.writelines(orig_file);

            # clean up
            os.remove(solnFilePath + '.mat')
                 
    
def main():

    # initialize a new Processing.Session
    session = Session(); 
     
    # initialization    
    try:
        
        # populate using the system input arguments
        session.configure_with_args(sys.argv).validate(); 
        
    except SessionException as err:
        
        # blab about the exception details and exit
        os.sys.stderr.write(str(err)); sys.exit();
    else:
        
        # otherwise print out the screen
        session.dump();
        
    session.initialize();


if __name__ == '__main__':
    
    main()
                       
    