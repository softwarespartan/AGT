#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
import threading;
import os,re,copy;
import JobSpecification;
import Queue;

class _sqs_load_Exception(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

JOB_QUEUE = 'com_widelane_jobs';

from boto.sqs.connection import SQSConnection
from boto.sqs.message    import Message


class WorkerThread(threading.Thread):
    
    
    def __init__(self, args, queue, command):
        
        # make sure to call super class constructor
        super(WorkerThread, self).__init__()
        
        # init args
        self.args = copy.deepcopy(args);
        
        # init queue
        self.file_queue = queue;
        
        # init sqs connection
        self.job_queue = SQSConnection().get_queue(JOB_QUEUE);
    
        # initialize new job specification
        self.spec = JobSpecification.JobSpecification(command);
        
    # @Override
    def run(self):
        
        #print "Thread ",self.name,' is starting ...';
        
        while self.file_queue.qsize() > 0:
            
            try:
                try:
                    # get item from the file queue
                    file = self.file_queue.get_nowait()
                except Exception as e:
                    os.sys.stderr.write(str(e)+'\n');
                    return;
                
                # make a file command line argument
                file_arg = '--file='+file;
                
                # make copy of current sys args
                args = copy.deepcopy(self.args);
                
                # add the file arg
                args.append(file_arg);
                                
                # create new job template
                job = self.spec.job_template(args);
                
                # do it
                jobXML =  self.spec.asXML(job);
                
                # push job to sqs
                self.push_job_sqs(jobXML)
                
            except Exception as e:
                # blab about it
                os.sys.stderr.write(str(e)+'\n');
                
            finally:
                # notify queue that we're done
                self.file_queue.task_done();

    def push_job_sqs(self,xml):
        
        # create a new message
        m = Message();
    
        # set the payload
        m.set_body(xml);
        
        # publish the message to SQS
        self.job_queue.write(m);
    
    
def find_stn_lists(dir,match=None):
    
    pattern1 = re.compile('^stn_list\.\d\d\d\d\.\d\d\d$');
    pattern2 = re.compile('^stn_list\.\d\d\d\d\.\d\d\d\.n\d+$');
    pattern3 = None;
    
    if match is not None: pattern3 = re.compile(match);
    
    # init list to hold the station list files
    stn_list_files = list();
        
    # walk the current directory to find the station list files
    for root, dirs, files in os.walk(dir): # Walk directory tree
        for f in files:
            if pattern1.match(f) or pattern2.match(f):
                if pattern3 is not None:
                    if pattern3.match(f):
                        stn_list_files.append(os.path.join(root,f));
                else:
                    stn_list_files.append(os.path.join(root,f));
                
    # that's all
    return stn_list_files;

def load_stn_lists(afile,match=None):

    pattern1 = re.compile('^stn_list\.\d\d\d\d\.\d\d\d$');
    pattern2 = re.compile('^stn_list\.\d\d\d\d\.\d\d\d\.n\d+$');
    pattern3 = None;

    if match is not None: pattern3 = re.compile(match);

    # init list to hold the station list files
    stn_list_files = list();

    # walk the current directory to find the station list files
    with open(afile) as fid:
        for f in fid.readlines():
            f = f.strip();
            if pattern1.match(os.path.basename(f)) or pattern2.match(os.path.basename(f)):
                 if pattern3 is not None:
                     if pattern3.match(os.path.basename(f)):
                         stn_list_files.append(f);
                 else:
                     stn_list_files.append(f);
    # that's all
    return stn_list_files;

if __name__ == "__main__":

    # init new queue for files
    file_queue = Queue.Queue();

    # get the input args (without progname)
    sys_args = os.sys.argv[1:];

    # see if the file as been specified
    dir_arg = [arg for arg in sys_args if arg.startswith('--indir')];

    # see if file with station lists has been specified
    file_arg = [arg for arg in sys_args if arg.startswith('--file')];

    # make sure that we have the input directory to load
    if len(dir_arg) != 1 and len(file_arg) != 1:
        raise _sqs_load_Exception('must specify --indir= or --file= as command line arg');

    if len(dir_arg) == 1 and len(file_arg) == 1:
         raise _sqs_load_Exception('must specify --indir= OR --file= as command line arg but not both');
    
    # see if the station list match arg has been specified
    match_arg = [arg for arg in sys_args if arg.startswith('--match')];
    
    # turn match arg into list or set as none
    if len(match_arg) > 0: 
        
        match_arg = match_arg[0];
        
        # make sure only two parts to the file arg
        if len(re.split('=',match_arg)) != 2:
            raise _sqs_load_Exception('invalid file arg: '+match_arg); 
        
        # isolate file pattern
        match_str = re.split('=',match_arg)[1];
        
        # remove from system args
        sys_args.remove(match_arg);
        
    else: match_arg = None; match_str = None;


    # init station list
    stn_lists = list();

    if len(dir_arg) == 1:
        # convert from list to string
        dir_arg = dir_arg[0];

        # make sure only two parts to the file arg
        if len(re.split('=',dir_arg)) != 2:
            raise _sqs_load_Exception('invalid file arg: '+dir_arg);

        # isolate file path
        dir_path = re.split('=',dir_arg)[1];

        # make sure to remove from sys args
        sys_args.remove(dir_arg);

        # build list of files
        stn_lists = find_stn_lists(os.path.expanduser(dir_path),match_str);

    if len(file_arg) == 1:

        # convert from list to string
        file_arg = file_arg[0];

        # make sure only two parts to the file arg
        if len(re.split('=',file_arg)) != 2:
            raise _sqs_load_Exception('invalid file arg: '+file_arg);

        # isolate file path
        file_path = re.split('=',file_arg)[1];

        # make sure to remove from sys args
        sys_args.remove(file_arg);

        # build list of files
        stn_lists = load_stn_lists(os.path.expanduser(file_path),match_str);
    
    # if no station lists found then complain about it to the user
    if len(stn_lists) == 0:
        os.sys.stderr.write('no station lists found');
        os.sys.exit(2);
    
    # blab to the user
    print "mapping",len(stn_lists),'jobs'
    
    #for f in stn_lists: print f;
    
    # populate queue
    for f in stn_lists:
        file_queue.put_nowait(f);
    
    # init empty list of threads
    threads = list();

    # launch N threads 
    for i in range(0,20):
        
        # add the thread to the list of workers
        threads.append(WorkerThread(sys_args,file_queue,'wl_gamit'))
    
        # make deamon
        threads[i].daemon = True;
        
    for i in range(0,20):
        
        # start the thread
        threads[i].start();
        
    file_queue.join();
        