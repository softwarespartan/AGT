
import unittest
import gamit,Utils,glob;

import os;

class InitializeTestFunctions(unittest.TestCase):
    
    def setUp(self):
        
        # initialize a configuration object
        self.session = gamit.Session();
        
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
                '--eop_type=usno'                                             ,\
                '--expt_type=RELAX'                                           ,\
                '--minspan=10'                                                 \
        ];
                
        # configure the object using this list of arguments
        self.session.configure_with_args(sys_argv);
        
        # initialize the session
        self.session.initialize();
    
    def tearDown(self):
        
        # i.e. delete the tmp work directory
        self.session.dispose();
       
    def test_bin_file_exists(self):
        
        # compute the generalized file name
        file_name = Utils.get_resource_delimiter().join(('gamit',os.uname()[0],'*'));
        
        # compute the file path to local work dir
        bin_file_path = os.path.join(self.session.work_dir_path,file_name);
        
        # glob for the file
        file_list = glob.glob(bin_file_path);
        
        # assert that the number of files globbed for are found
        self.assertTrue(len(file_list) == 1, 'binary files not located ');
        
    def test_bin_file_exists_2(self):
        
        # double check that the file proposed to be downloaded was actually downloaded
        self.assertTrue(os.path.isfile(self.session.files['bin']), 'binary files not located ');
        
    def test_tables_file_exists(self):
        
        # compute the generalized file name
        file_name = Utils.get_resource_delimiter().join(('gamit','tables','*'));
        
        # compute the file path to local work dir
        file_path = os.path.join(self.session.work_dir_path,file_name);
        
        # glob for the file
        file_list = glob.glob(file_path);
        
        # assert that the number of files globbed for are found
        self.assertTrue(len(file_list) == 1, 'tables files not located ');
        
    def test_tables_file_exists_2(self):
        
        # double check that the file proposed file was actually downloaded
        self.assertTrue(os.path.isfile(self.session.files['tables']), 'tables files not located ');
              
if __name__ == '__main__':
    unittest.main()