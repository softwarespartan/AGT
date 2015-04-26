#!/usr/bin/python


import os, sys, time

from boto.s3.key        import Key         ;
from boto.s3.connection import S3Connection;

def usage():
             
    print "USAGE:  pushS3 bucket file"
    sys.exit(1);

def main():
    
    # check the input args
    if len(sys.argv) != 3:
        usage()
        sys.exit();
    
    # get date and file info from command line
    bucketName          = sys.argv[1]
    filePath            = sys.argv[2]
    
    # parse the name of the file
    fileName = os.path.basename(filePath);
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection()  ;
    bucket    = conn.create_bucket(bucketName)      ;
    bucketKey = Key(bucket)                         ;
    
    # create the s3 object
    bucketKey.key = fileName;  bucketKey.set_contents_from_filename(filePath);
    
    # blab about 
    print fileName,"-->",bucketName;
        
if __name__ == "__main__":
    main()