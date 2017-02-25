
import pyDate
import Processing
import Resources
import os;

from multiprocessing import Pool;

def run(dt,outdir):
    
    #org  = ['g06'];
    #expt = ['glbl','glbf','glbd','anet','gnet','capp','swpp','tigg','glbk'];
    #expt = ['glbk'];
    #expt = ['anet','gnet'];
    expt = ['glbk'];
    org  = ['g09'];
    
    for e in expt:
        for o in org:
            
            # construct the AWS/S3 bucket path
            soln_bucket = Processing.solution_bucket(dt.year,dt.doy,'',e,o,None);
                                                                                         
            # ok get the snx with this bucket prefix
            files = Resources.get_resources(soln_bucket, '.mat.gz', outdir);
            
            # blab about it ... maybe
            if len(files) > 0: print soln_bucket,len(files);

def action(dt):
    
    try:
        #run(dt,'/Volumes/PROMISE_PEGASUS/data/g06/data/');
        run(dt,'/Users/abelbrown/data');
    except:
        print "Unexpected error:", os.sys.exc_info()[0];
        
    
def main():
    
    # create start and stop dates for the run
    start_date = pyDate.Date(year=2016,doy=1);
    end_date   = pyDate.Date(year=2016,doy=330);
        
    # init queue for dates
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
      

if __name__ == '__main__':
    main();