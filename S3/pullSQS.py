
JOB_QUEUE = 'com_widelane_nodestats';

from boto.sqs.connection import SQSConnection
from boto.sqs.message    import Message
import ast;
import threading;

#class WorkerThread(threading.Thread):
#    
#    
#    def __init__(self):
#        
#        # make sure to call super class constructor
#        super(WorkerThread, self).__init__()
#
#        
#        # init sqs connection
#        self.job_queue = SQSConnection(ACCESS_KEY,SECRET_KEY).get_queue(JOB_QUEUE);
#
#        
#    # @Override
#    def run(self):
#        
#        print "Thread ",self.name,' is starting ...';
#        
#        while True:
#            try:
#                m = self.job_queue.get_messages();
#                
#                if len(m) == 0:
#                    print "queue ",JOB_QUEUE,' is empty'
#                    return; 
#    
#                # dereference the list
#                m = m[0];
#                    
#                self.job_queue.delete_message(m);
#                print self.name,"deleting message ..."
#            except:
#                print 'error getting or deleting msg'
#            

def main():
    
    # create a connection to SQS
    conn = SQSConnection();
    
    # ask for the JOB_QUEUE
    q = conn.get_queue(JOB_QUEUE);
 
    while True:
        # snag a mutha fuckin message
        m = q.get_messages()
    
        # empty queue check
        if len(m) == 0: 
            print "queue ",JOB_QUEUE,' is empty'
            return; 
    
        # dereference the list
        m = m[0];
    
        # blab
        print m.get_body();
    
        # remove the message from the queue
        #q.delete_message(m)
        
        #status_msg = ast.literal_eval(m.get_body());
        
        #print status_msg['expt'],status_msg['year'],status_msg['doy'],status_msg['status'];
        
        # check if job failed
        #if status_msg['status']:
        #    print status_msg['expt'],status_msg['year'],status_msg['doy'],status_msg['status'];
            

#def main():
#    
#    # init empty list of threads
#    threads = list();
#
#    # launch N threads 
#    for i in range(0,20):
#        
#        # add the thread to the list of workers
#        threads.append(WorkerThread())
#    
#        # make deamon
#        threads[i].daemon = True;
#        
#    for i in range(0,20):
#        
#        # start the thread
#        threads[i].start();
#        
#    threads[0].join();
             
if __name__ == "__main__":
    
    main()