import Processing;
import unittest

class TestFunctions(unittest.TestCase):

    def setUp(self):
        
        # initialize a configuration object
        self.session = Processing.Session();
        
        # init session object properly
        self.session.options['year'] = 2012;
        self.session.options['doy' ] = 201;

    def test_validate_year_none(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = None; self.session.validate();
            
    def test_validate_year_not_int(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = 'someint'; self.session.validate();
            
    def test_validate_year_small(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = 1847; self.session.validate();
    
    def test_validate_year_yy(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = 01; self.session.validate();
            
    def test_validate_year_big(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = 2047; self.session.validate();
            
    def test_validate_doy_none(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['doy'] = None; self.session.validate();
            
    def test_validate_doy_not_int(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['doy'] = '29yi'; self.session.validate();
            
    def test_validate_doy_small(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['doy'] = -1; self.session.validate();
            
    def test_validate_doy_big(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['year'] = 481; self.session.validate();
            
    def test_validate_expt_too_long(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['expt'] = 'antarctica'; self.session.validate();
            
    def test_validate_expt_too_short(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['expt'] = 'ant'; self.session.validate();
            
    def test_validate_eop_wrong_type(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['eop_type'] = 'bull_a'; self.session.validate();
            
    def test_validate_expt_type_wrong(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['expt_type'] = 'ephem'; self.session.validate();
            
    def test_validate_minspan_too_big(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['minspan'] = '134'; self.session.validate();
            
    def test_validate_minspan_too_small(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['minspan'] = '0'; self.session.validate();
            
    def test_validate_minspan_not_int(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['minspan'] = 'ag12'; self.session.validate();
            
    def test_validate_should_iterate(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['should_iterate'] = '1'; self.session.validate();
            
    def test_validate_sp3_type_too_big(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['sp3_type'] = 'igs1'; self.session.validate();
            
    def test_validate_sp3_type_too_small(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['sp3_type'] = 'i1'; self.session.validate();
            
    def test_validate_org_too_big(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['org'] = 'anet'; self.session.validate();
            
    def test_validate_org_too_small(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['org'] = 'at'; self.session.validate();
            
    def test_validate_net_id_wrong(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['network_id'] = 'net12'; self.session.validate();
            
    def test_validate_dns_none(self):
        with self.assertRaises(Processing.SessionException):
            self.session.options['dns'] = None; self.session.validate();
            
    def test_validate_stn_list_duplicates(self):
        with self.assertRaises(Processing.SessionException):
            self.session.stn_list = ['igs.yell','igs.algo','igs.yell']; 
            self.session.validate();

if __name__ == '__main__':
    unittest.main()