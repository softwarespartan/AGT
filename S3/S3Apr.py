'''
Created on Jan 28, 2013

@author: abelbrown
'''

if __name__ == '__main__':

    import pyStk;
    
    from boto.s3.key        import Key         ;
    from boto.s3.connection import S3Connection;
    
    # init vars
    namespace = 'osf.gamit'                               ;
    dirS3     = 'com.widelane.apr'                        ;
    tsFile    = '/Users/abelbrown/data/osf_NEW_PRIORS.mat';
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection()  ;
    bucket    = conn.create_bucket(dirS3)           ;
    bucketKey = Key(bucket)                         ;
    
    # open the mat file with the apr 
    ts = pyStk.pyTS().initFromMatFile(tsFile);
    
    # for each station ...
    for stn in ts.stn_list:
        
        # compute the file name
        stn_key = stn.lower().replace("_",".")+".apr";
        
        # export apr for each station day
        for xyz,sig,d in ts.spvsWithSigma(stn):
            
            # compute the full path to the file
            file_key = str(d.year)+"/"+d.doystr()+"/"+namespace+"/"+stn_key;
            
            # compute value to store in the file
            file_value = " ".join(map(str,xyz))+" "+ " ".join(map(str,sig))+" "+str(d.fyear);
            
            # create the S3 object
            bucketKey.key = file_key; bucketKey.set_contents_from_string(file_value);