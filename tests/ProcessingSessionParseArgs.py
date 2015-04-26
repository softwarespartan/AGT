
import Processing;
import unittest

class ArgParseTest(unittest.TestCase):
    
    def setUp(self):
        
        # initialize a configuration object
        self.session = Processing.Session();
        
        # create simulated system input arguments
        sys_argv = [                                                           \
                '/Users/abelbrown/Documents/workspace/ATG/src/Processing.py'  ,\
                '--year=2013'                                                 ,\
                '--doy=201'                                                   ,\
                '--expt=anet'                                                 ,\
                '--org=aws'                                                   ,\
                '--stn=igs.yell'                                              ,\
                '--stn=igs.p213'                                              ,\
                '-stn=igs.yell'                                               ,\
                '--network_id=n1'                                             ,\
                '--should_iterate=no'                                         ,\
                '--sp3_type=osf'                                              ,\
                '--dns=napeos'                                                ,\
                '--eop_type=bull_b'                                           ,\
                '--expt_type=RELAX'                                           ,\
                '--minspan=10'                                                 \
        ];
                
        # configure the object using this list of arguments
        self.session.configure_with_args(sys_argv);

class TestFunctions(ArgParseTest):
                
    def test_parse_args_year(self):        
        self.assertEqual(self.session.options['year'], '2013', 'incorrect year');
        
    def test_parse_args_doy(self):        
        self.assertEqual(self.session.options['doy'], '201', 'incorrect doy');
        
    def test_parse_args_expt(self):        
        self.assertEqual(self.session.options['expt'], 'anet', 'incorrect expt');
        
    def test_parse_args_org(self):        
        self.assertEqual(self.session.options['org'], 'aws', 'incorrect org');
        
    def test_parse_args_stn(self):
        self.assertEqual(self.session.stn_list, ['igs.yell','igs.p213'], 'incorrect station list');
        
    def test_parse_args_network_id(self):
        self.assertEqual(self.session.options['network_id'],'n1','incorrect network id');
    
    def test_parse_args_minspan(self):
        self.assertEqual(self.session.options['minspan'],'10','incorrect minspan');
        
    def test_parse_args_should_iterate(self):
        self.assertEqual(self.session.options['should_iterate'], 'no', 'incorrect iterate flag');
        
    def test_parse_args_sp3_type(self):
        self.assertEqual(self.session.options['sp3_type'], 'osf', 'incorrect sp3 type');
        
    def test_parse_args_dns(self):
        self.assertEqual(self.session.options['dns'], 'napeos', 'incorrect metadata namespace');
        
    def test_parse_args_eop_type(self):
        self.assertEqual(self.session.options['eop_type'], 'bull_b', 'incorrect eop type');
        
    def test_parse_args_expt_type(self):
        self.assertEqual(self.session.options['expt_type'], 'relax', 'incorrect experiment type');
        
        
if __name__ == '__main__':
    unittest.main()