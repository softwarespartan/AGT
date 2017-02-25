'''
Created on Jan 28, 2013

@author: abelbrown
'''

if __name__ == '__main__':

    import pyStk;
    import pyDate;
    
    from boto.s3.key        import Key         ;
    from boto.s3.connection import S3Connection;

    import boto;
    from boto.s3.connection import OrdinaryCallingFormat

    # init vars
    namespace = 'g08c.gamit'
    bucketId  = 'com.widelane.apr'
    inFile    = '/Users/abelbrown/Dropbox/stk/data/apr/g08c_apr.mat'
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())
    bucket    = conn.get_bucket(bucketId)
    bucketKey = Key(bucket)
    
    # open the mat file with the apr 
    ts = pyStk.pyTS().initFromMatFile(inFile);
    
    for epoch in ts.epochs:
        
        d      = pyDate.Date(fyear=epoch)
        aprstr =  str(epoch)+'\n'
        
        numstn = 0;
        
        for stnId,xyz,sigXYZ in ts.spvsWithSigmaForEpoch(epoch):
            
            # getting sig ENU from mike, GAMIT wants neu
            n = sigXYZ[1]; e = sigXYZ[0]; u = sigXYZ[2];
            
            # xyz to ned trasformation matrix
            #xTn    = np.mat(  pyCoords.xTn(xyz)      ); 
            
            # convert to neu trasofrmation matrix
            #xTn[2,:] = -xTn[2,:];
            
            # compute the "covariance" matrix
            #C      = np.mat(  np.diag( sigXYZ*sigXYZ ));
            
            # compute sigmas in local neu coordinate frame
            #sigENU = np.sqrt( np.diag( xTn*C*xTn.T   ));
                        
            # compute the full path to the file
            file_key = ".".join([namespace,str(d.year),d.ddd(),'apr']);
            
            # normalize the station id
            stnId = stnId.lower().replace("_",".");
            
            # create format string from xyz and sigma
            xyz    = "%14.4f %14.4f %14.4f" % tuple(xyz   );
            sigENU = "%9.4f %9.4f %9.4f"    % tuple((n,e,u));
            #sigXYZ = "%9.4f %9.4f %9.4f"    % tuple(sigXYZ);
            
            aprstr += stnId + " " + xyz + " " + sigENU +"\n";
            
            # update station count
            numstn += 1; 
            
        print "exporting ",str(numstn),' stns to file ',file_key;

        # create the S3 object
        bucketKey.key = file_key; bucketKey.set_contents_from_string(aprstr);