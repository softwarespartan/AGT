
import pyDate;
import Processing;
import Resources;
import os;

from multiprocessing import Pool, Manager;

def run(fileName):
    
    org  = ['g06'];
    expt = ['odot'];
    
    fparts = fileName.split('.');
    
    # defensive check
    if len(fparts) != 4: return; 
    
    for e in expt:
        for o in org:
            
            # construct the AWS/S3 bucket path
            soln_bucket = Processing.solution_bucket(fparts[1],fparts[2],'',e,o,fparts[3]);
                                                                                         
            # ok get the snx with this bucket prefix
            files = Resources.list_resources(soln_bucket,'.mat.gz');
            
            # blab about it ... maybe
            if len(files) == 0:  print 'no solution for',fileName;

def action(afile):
    
    try:
        run(afile);
    except:
        print "Unexpected error:", os.sys.exc_info()[0];
        
    
def main():
    
    # where to look for station lists
    indir = "/Volumes/PROMISE_PEGASUS/data/networks/g06/odot"
        
    # init
    files = list();
        
    # loop over all files in the directory
    for root, dirs, lfiles in os.walk(indir):
        for f in lfiles: files.append(f);
    
    # create a pool of worker threads
    pool = Pool(16);
    
    # map the action function to each date in the queue
    pool.map(action,files);


if __name__ == '__main__':
    main();