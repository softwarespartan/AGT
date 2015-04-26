
import os, sys, time,re

from boto.s3.key        import Key         ;
from boto.s3.connection import S3Connection;

# init s3 connection to the metadata bucket
conn      = S3Connection()     ;
bucket    = conn.get_bucket('com.widelane.sp3');
bucketKey = Key(bucket) 

pattern = re.compile('ig1.*');

for f in bucket.list():
    if pattern.match(f.key): print f.key, f.last_modified;
    