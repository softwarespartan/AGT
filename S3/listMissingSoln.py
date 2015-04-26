

import os, sys, time,re,pyDate

from boto.s3.key        import Key         ;
from boto.s3.connection import S3Connection;

# init s3 connection to the metadata bucket
conn      = S3Connection()     ;
bucket    = conn.get_bucket('com.widelane.solutions');

dt       = pyDate.Date(year=1993,doy=1);
end_date = pyDate.Date(year=1994,doy=1);

# while dt < end_date:
#  
#     # (re)init number of files for date
#     num_files = 0;
#  
#     # create the file name
#     snx_file_name = 'g03'+dt.wwwwd()+'.snx.gz';
#      
#     # create the file path 
#     snx_file_path = os.path.join(dt.yyyy(),dt.ddd(),'glbk','g03','n0',snx_file_name);
#      
#     # get the file list for this bucket + key
#     file_results = bucket.list(snx_file_path);
#      
#     # compute the number of files that match this key 
#     for f in file_results: num_files += 1;
#      
#     # print the file if no listing
#     if num_files == 0: print dt.yyyy(),dt.ddd();
#      
#     # increment the date
#     dt = dt + 1;
    
bucket    = conn.get_bucket('com.widelane.sp3');

total = 0; num_dates = 0;

while dt < end_date:
    
    # (re)init number of files for date
    num_files = 0; 

    # create the file name
    sp3_file_name = 'g05'+dt.wwwwd()+'.sp3.gz';
    
    # get the file list for this bucket + key
    file_results = bucket.list(sp3_file_name);
    
    # compute the number of files that match this key 
    for f in file_results: num_files += 1;
    
    # print the file if no listing
    if num_files == 0: 
        print dt.yyyy(),dt.ddd();
        total +=1;
    
    # increment the date
    dt = dt + 1;  num_dates = num_dates + 1;
    
print 'missing',total,'of',num_dates,'solutions';
    
    