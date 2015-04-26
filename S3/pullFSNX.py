'''
Created on Mar 30, 2013

@author: abelbrown
'''

import Utils,pyDate,os;

from boto.s3.key        import Key         ;
from boto.s3.connection import S3Connection; 

from multiprocessing import Pool;

class TargetFile():
    
    def __init__(self,year,doy,bucket):
        
        self.year   = year;
        self.doy    = doy;
        self.bucket = bucket;
        
        
    def get_path(self):
        return '';
    
    def download(self,outdir=None):
        
        # set outdir to current directory if not set
        if outdir == None: outdir = '.';
        
        # make sure to expand any user symbols
        outdir = os.path.expanduser(outdir);
        
        # compute the path for this file
        file_path = self.get_path();
        
        # create the output path
        out_path = os.path.join(outdir,os.path.basename(file_path));
        
        # init s3 connection to the metadata bucket
        bucketKey = self.bucket.get_key(self.get_path());
    
        if bucketKey == None:
            #os.sys.stderr.write('fsnx resource: '+file_path+' could not be located\n');
            return;
    
        # create the s3 object
        bucketKey.key = file_path;  
        
        # pull the file
        bucketKey.get_contents_to_filename(out_path);
    
    
class file_fsnx(TargetFile):
    
    def get_path(self):
        
        # create a date object
        # initialize a date object
        date = pyDate.Date(year=self.year, doy=self.doy);
        
        # create string version of the gps week
        gps_week_str = str(date.gpsWeek);
        
        # make sure that the string is 5 characters
        if date.gpsWeek < 1000: gps_week_str = '0'+gps_week_str;
        
        file_name = 'g05'+gps_week_str+str(date.gpsWeekDay)+'.mat.gz'

        doy = Utils.get_norm_doy_str(date.doy);
        
        return os.path.join(str(date.year),doy,'','boss','g05','n1',file_name)
    
class file_sp3(TargetFile):
    
    def get_path(self):
        
        # create a date object
        # initialize a date object
        date = pyDate.Date(year=self.year, doy=self.doy);
        
        # create string version of the gps week
        gps_week_str = str(date.gpsWeek);
        
        # make sure that the string is 5 characters
        if date.gpsWeek < 1000: gps_week_str = '0'+gps_week_str;
        
        file_name = 'g04'+gps_week_str+str(date.gpsWeekDay)+'.sp3.Z'
                
        return file_name

def action(ft):
    
    ft.download('/Users/abelbrown/data/g05/tmp');
    
if __name__ == '__main__':
    
    conn      = S3Connection()     ;
    bucket    = conn.get_bucket('com.widelane.solutions');
    
    file_targets = list();
        
    date = pyDate.Date(year=1993,doy=1);    
    
    while True:
        file_targets.append(file_fsnx(date.year,date.doy,bucket))
        #print date.year,date.doy;
        date = pyDate.Date(mjd=date.mjd+1);
        if date.year == 2014 and date.doy == 101: break;
        
    print len(file_targets)
    
    pool = Pool(10);
    
    pool.map(action, file_targets)