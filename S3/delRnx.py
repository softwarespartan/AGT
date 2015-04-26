

from boto.s3.key        import Key         ;
from boto.s3.connection import S3Connection;

import re,os,pyDate,Utils;

from multiprocessing import Pool;

WL_BUCKET     = 'resources';
WL_RNX_BUCKET = 'rinex'    ;

def del_rnx_path(year,doy,stn_list):
    
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    # init
    rnx_file_list = list();
    
    for stnId in stn_list:
    
        # parse the station id and extract the 4-char station code
        (ns,code) = Utils.parse_stnId(stnId);
    
        # create the file name of the sp3
        rnx_file_name = code+doy+'0.'+year[2:]+'d.Z';
        
        # create key path to file in rnx
        rnx_key_path = '/'.join([ns,year,doy,rnx_file_name]);
        
        # init s3 connection to the metadata bucket
        conn      = S3Connection()  ;
        bucket    = conn.get_bucket(WL_RNX_BUCKET)        ;
        bucketKey = bucket.get_key(rnx_key_path)          ;
        
        if bucketKey == None:
            # create the file name of the rnx with session 1
            rnx_file_name = code+str(doy)+'1.'+str(year)[2:]+'d.Z';
            
            # create key path to file in s3
            rnx_key_path = '/'.join([ns,str(year),str(doy),rnx_file_name]);
            
            # check for session 1 file
            bucketKey = bucket.get_key(rnx_key_path);
            
            if bucketKey == None:
                #os.sys.stderr.write('rnx resource: '+stnId+' could not be located for '+year+' '+doy+'\n');
                continue;
        
        # create the s3 object
        bucketKey.key = rnx_key_path;  
        
        # delete the path from the bucket
        bucket.delete_key(rnx_key_path);
        
        # add the rinex file path to the file list
        rnx_file_list.append(rnx_key_path);
        
        # comfort signal 
        print rnx_key_path;
        
    return rnx_file_list;

def action(dt):
    
    # list of stations to delete
    stn_list = ['chg.anto','ans.bell','chc.cast','bra.mana','bol.marg','bra.mcla','chu.pcha','chu.agui'];
    
    # delete the stations for this date
    del_rnx_path(dt.year, dt.doy, stn_list);

if __name__ == '__main__':
    
    # create start and stop dates for the run
    start_date = pyDate.Date(year=2015,doy=1);
    end_date   = pyDate.Date(year=2015,doy=365);
    
    # init list of dates to work on
    dates = list();
    
    # init date
    dt = start_date;
    
        # populate the date queue
    while(dt <= end_date):
                
        # add the date to the queue
        dates.append(dt);
        
        # increment the data
        dt += 1;
        
    # create a pool of worker threads
    pool = Pool(16);
    
    # map the action function to each date in the queue
    pool.map(action,dates);
    