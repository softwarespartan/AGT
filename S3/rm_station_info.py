'''
Created on Jan 28, 2013

@author: abelbrown
'''

if __name__ == '__main__':
    
    from boto.s3.key        import Key         ;
    from boto.s3.connection import S3Connection;
    
    # init vars
    namespace = 'osf.gamit'                               ;
    dirS3     = 'com.widelane.ephemerides'                ;
    tsFile    = '/Users/abelbrown/data/osf_NEW_PRIORS.mat';
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection()  ;
    bucket    = conn.create_bucket(dirS3)           ;
    bucketKey = Key(bucket)                         ;
    
    for f in bucket.list():
        print f.key;
        bucket.delete_key(f.key);