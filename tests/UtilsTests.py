import Utils;
import unittest

class TestFunctions(unittest.TestCase):

    def test_YY_to_YYYY_2000(self):
        year = Utils.get_norm_year_str('02')
        self.assertEqual(year,'2002','failed to convert YY to YYYY');
        
    def test_YY_to_YYYY_1900(self):
        year = Utils.get_norm_year_str('93')
        self.assertEqual(year,'1993','failed to convert YY to YYYY');
        
    def test_YYYY_to_YYYY(self):
        year = Utils.get_norm_year_str('1993')
        self.assertEqual(year,'1993','failed to pass through YYYY to YYYY');
    
    def test_YY_as_int(self):
        year = Utils.get_norm_year_str(05);
        self.assertEqual(year,'2005','failed to convert integer to string');
        
    def test_YYYY_as_int(self):
        year = Utils.get_norm_year_str(2012);
        self.assertEqual(year,'2012','failed to convert integer to string');
        
    def test_YYYY_nan(self):
        with self.assertRaises(Utils.UtilsException):
            Utils.get_norm_year_str('M85h337');
            
    def test_YYYY_negative(self):
        with self.assertRaises(Utils.UtilsException):
            Utils.get_norm_year_str('-1998');
            
    def test_D_to_DDD_lt_ten(self):
        doy = Utils.get_norm_doy_str('3');
        self.assertEqual(doy, '003', 'failed to convert D to DDD');
        
    def test_DD_to_DDD_lt_ten(self):
        doy = Utils.get_norm_doy_str('07');
        self.assertEqual(doy, '007', 'failed to convert DD to DDD');
        
    def test_DDD_to_DDD_lt_ten(self):
        doy = Utils.get_norm_doy_str('001');
        self.assertEqual(doy, '001', 'failed to convert DDD to DDD');
        
    def test_DD_to_DDD_lt_hundred(self):
        doy = Utils.get_norm_doy_str('86');
        self.assertEqual(doy, '086', 'failed to convert DD to DDD');
        
    def test_DDD_to_DDD_lt_hundred(self):
        doy = Utils.get_norm_doy_str('019');
        self.assertEqual(doy, '019', 'failed to convert DDD to DDD');
        
    def test_DDD_to_DDD(self):
        doy = Utils.get_norm_doy_str('201');
        self.assertEqual(doy, '201', 'failed to convert DDD to DDD');
        
    def test_D_to_DDD_int(self):
        doy = Utils.get_norm_doy_str(7);
        self.assertEqual(doy, '007', 'failed to convert int D to str DDD');
        
    def test_DD_to_DDD_int(self):
        doy = Utils.get_norm_doy_str(93);
        self.assertEqual(doy, '093', 'failed to convert int DD to str DDD'); 
        
    def test_DDD_to_DDD_int(self):
        doy = Utils.get_norm_doy_str(344);
        self.assertEqual(doy, '344', 'failed to convert int DDD to str DDD');   
        