
import unittest
import Processing;

import os;

class InitializeTestFunctions(unittest.TestCase):
    
    def setUp(self):
        
        # initialize a configuration object
        self.session = Processing.Session();
        
        # create simulated system input arguments
        sys_argv = [                                                           \
                '/Users/abelbrown/Documents/workspace/ATG/src/Processing.py'  ,\
                '--year=2010'                                                 ,\
                '--doy=201'                                                   ,\
                '--expt=anet'                                                 ,\
                '--org=aws'                                                   ,\
                '--stn=igs.yell'                                              ,\
                '--stn=igs.p213'                                              ,\
                '--network_id=n1'                                             ,\
                '--should_iterate=no'                                         ,\
                '--sp3_type=osf'                                              ,\
                '--dns=osf.gamit'                                             ,\
                '--eop_type=bull_b'                                           ,\
                '--expt_type=RELAX'                                           ,\
                '--minspan=10'                                                 \
        ];
                
        # configure the object using this list of arguments
        self.session.configure_with_args(sys_argv);
        
        # initialize the session
        self.session.initialize();
    
    def tearDown(self):
        self.session.dispose();
    
    def test_work_dir_exists(self):
        self.assertTrue(os.path.isdir(self.session.work_dir_path), 'work directory does not exist');
        
    def test_work_dir_exists_already(self):
        with self.assertRaises(Processing.SessionException):
            self.session.initialize();   
    
    def test_bucket_dir_exists(self):
        self.assertTrue(self.session.get_resources_path(), 'bucket directory does not exist');
             
    def test_sp3_file_exists(self):
        sp3_file_path = os.path.join(self.session.get_resources_path(),'osf15932.sp3.Z');
        self.assertTrue(os.path.isfile(sp3_file_path), 'sp3 file was not located');
        
    def test_sp3_file_exists_2(self):
        self.assertTrue(self.session.files['sp3'], 'sp3 file was not located');
        
    def test_nav_file_exists(self):
        nav_file_path = os.path.join(self.session.get_resources_path(),'auto2010.10n.Z');
        self.assertTrue(os.path.isfile(nav_file_path), 'nav file was not located');
        
    def test_nav_file_exists_2(self):
        self.assertTrue(self.session.files['nav'], 'nav file was not located');
        
    def test_apr_file_exists(self):
        apr_file_path = os.path.join(self.session.get_resources_path(),'osf.gamit.2010.201.apr');
        self.assertTrue(os.path.isfile(apr_file_path), 'apr file was not located');
        
    def test_apr_file_exists_2(self):
        self.assertTrue(self.session.files['apr'], 'apr file was not located');
        
    def test_rnx_file_exists(self):
        rnx_file_path = os.path.join(self.session.get_resources_path(),'yell2010.10d.Z');
        self.assertTrue(os.path.isfile(rnx_file_path), 'rnx file was not located');
        
    def test_rnx_file_exists_2(self):
        for rnxfile in self.session.files['rnx']:
            self.assertTrue(os.path.isfile(rnxfile), 'rnx file was not located');

    def test_info_file_exists(self):
        info_file_path = os.path.join(self.session.get_resources_path(),'igs.yell.station.info');
        self.assertTrue(os.path.isfile(info_file_path), 'info file was not located'); 
        
    def test_info_file_exists_2(self):
        self.assertTrue(self.session.files['stn_info'], 'station info file was not located');
        
if __name__ == '__main__':
    unittest.main()