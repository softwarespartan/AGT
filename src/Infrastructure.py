
import os, threading, time, datetime, Utils, collections, Reflection;

from boto.sqs.connection import SQSConnection;
from boto.sqs.message    import Message      ;

import xml.etree.ElementTree as ET;

JOB_QUEUE        = 'edu_mbevis_osu_jobs'     ;
ERR_QUEUE        = 'edu_mbevis_osu_err'      ;
NODE_STATS_QUEUE = 'edu_mbevis_osu_nodestats';

WORKER_SLEEP_SECONDS   = 30   ;
STATS_SLEEP_SECONDS    = 60*15;
CHECKOUT_SLEEP_SECONDS = 60*25;
JOB_LEASE_SECONDS      = 60*30;


class InfrastructureException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class JobParserException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def parse_job(xmlstr):
    
    try:
        # init the element tree from xml string
        root = ET.fromstring(xmlstr);
    except:
        raise JobParserException('error parsing job text as xml: '+xmlstr);
    
    # init empty job dict
    jobs = dict();
    
    # look for job nodes
    for job in root.getiterator('job'):
             
        # (re)init arg list
        arg_list = []; 
        
        # make sure the xml specify proper shit
        if not 'name' in job.attrib.keys() :
            raise JobParserException('xml job specification did not contain name attribute.');
        
        # make sure x2 the xml specifies the command name
        if not 'command' in job.attrib.keys():
            raise JobParserException('xml job specification did not contain command attribute.');
            
        # extract the xml properties
        name    = job.attrib['name']; command = job.attrib['command'];
        
        # extrac command arguments
        for arg in job.getiterator('arg'): arg_list.append(arg.text);

        # complete the command string
        cmdstr =  command +' '+' '.join(arg_list);
        
        # add entry to jobs dict
        jobs[name] = cmdstr
        
    # that's all folks
    return jobs


class WorkerThread(threading.Thread):
    
    
    def __init__(self,jobQueue,errQueue,refl):
        
        # make sure to call super class constructor
        super(WorkerThread, self).__init__()
        
        # make workers daemon threads
        self.daemon = True;
        
        # set the work jobQueue to get messages from
        self.jobQueue = jobQueue;
        
        # set the error queue to set problem messages
        self.errQueue = errQueue;
        
        # set reflection instance
        self.reflection = refl;
        
        # create a ring buffer to store execution times
        self.exe_times = collections.deque(maxlen=100);
        
        # create a lock to guard the exe_times resource
        self.exe_times_lock = threading.Lock();
    
        # keep track of when a job is started
        self.start_time   = None;
        
        # keep track of the job being worked on
        self.job_name     = None;
        
        # keep track of pending jobs assigned
        self.pending_jobs = None;
        
        # create time thread
        self.visability_timer = None;
        
        # keep track of how many jobs executed
        self.total_job_count = 0;
    
    
    def publish_error(self,err_str):

            # generate message string
            error_message_content = self.reflection.public_hostname+': '+err_str;

            # create new empty message
            error_message = Message();

            # populate the message with content
            error_message.set_body(error_message_content);

            # write the message to the error queue
            self.errQueue.write(error_message);
        
    
    # Override
    def run(self):
        
        try:
            #print "Thread ",self.name,' is starting ...';
            
            # do this forever ...
            while True:
                
                try:
                    
                    # try to get a message from the jobQueue
                    msg = self.jobQueue.get_messages(1);
                    
                    # did we get a message from the jobQueue?
                    if len(msg) == 0:
                        
                        # if not, then just sleep for a while
                        time.sleep(WORKER_SLEEP_SECONDS);
                        
                        # move to next iteration
                        continue;
                    
                    try:
                        # if msg then process the message
                        self.handle_message(msg[0]);
                    except Exception as e:
                        os.sys.stderr.write(str(e)+'\n');
                        #raise InfrastructureException('error handling message: '+msg[0]);
                        self.publish_error('runhandle_message: '+str(e));
                    
                except Exception as e:
                        os.sys.stderr.write(str(e)+'\n');
                        #raise InfrastructureException('error in run loop for message: '+msg[0]);
                        self.publish_error('runwhile: '+str(e));
                        
                
        except Exception as e:
            os.sys.stderr.write(str(e)+'\n');
            #raise InfrastructureException('error in thread '+self.name+' while running '+msg[0]);
            self.publish_error('run: '+str(e));
    
                
    def handle_message(self,message):

        # try to parse message as job specification
        try:
            job_dict = parse_job(message.get_body());
        except Exception as e:
            
            # blab about the problem to standard error
            os.sys.stderr.write('handle_message/parse_job(message.get_body())'+str(e)+'\n');
            
            # log error message
            self.publish_error('handle_messageparse_job: '+str(e));
            
            # for now, lets remove the message from the jobQueue
            self.jobQueue.delete_message(message);
            
            # that's all
            return
        
        # make sure we have something to work with before we proceed
        if len(job_dict.keys()) == 0:
            os.sys.stderr.write(' handle_message:job_dict.keys() has zero length ... \n');
            self.jobQueue.delete_message(message);
            return;
        
        # make sure we continue to check out the message until delete
        self.change_visibility_and_reschedule(message);
        
        # assign all jobs as pending 
        self.pending_jobs = job_dict.keys();
        
        try:
            for job_name in job_dict.keys():
            
                # make note of what job we're on
                self.job_name = job_name;
                
                # remove the job from pending list
                self.pending_jobs.remove(job_name);
            
                # make note of the start time
                self.start_time = datetime.datetime.now();
                
                # blab about it
                print self.getName(),job_dict[job_name];
                
                # execute the command as system call
                os.system(job_dict[job_name]);      
                
                # update job count
                self.total_job_count += 1
                
                # compute the execution time
                dt = datetime.datetime.now() - self.start_time;
                
                # update execution times in seconds  
                with self.exe_times_lock:   
                    self.exe_times.append(dt.seconds);
                    
        except Exception as e:
            
            # blab about the problem to standard error
            os.sys.stderr.write(str(e)+'\n'); 
            
            # loog error message
            self.publish_error('handle_messageexe: '+str(e));
                
        finally:
            # stop the message lease renewal timer
            self.terminate_message_visibility_timer()
            
            # remove the message from the sqs jobQueue
            self.jobQueue.delete_message(message);
            
            # clear the start_time, job name, and pending jobs
            self.start_time   = None  ;  
            self.job_name     = None  ; 
            self.pending_jobs = list();


    def change_visibility_and_reschedule(self,message):
        
        # make message invisible in the jobQueue for 30 mins
        message.change_visibility(JOB_LEASE_SECONDS);
        
        # schedule another lease renewal 
        self.schedule_message_visibility_change(message)
        

    def schedule_message_visibility_change(self,message):
        
        # create a new timer thread to periodically renew message visibility - 25 minutes
        self.visability_timer = threading.Timer(CHECKOUT_SLEEP_SECONDS,self.change_visibility_and_reschedule,args=(message,));
        
        # start the timer thread
        self.visability_timer.start();


    def terminate_message_visibility_timer(self):
        
        # defensive check for null
        if self.visability_timer is not None:
            
            # terminate the timer thread
            self.visability_timer.cancel();


    def is_active(self):
        if self.job_name is not None:
            return True 
        else: 
            return False;
        
        
    def terminate(self):
        self.terminate_message_visibility_timer();
        self.terminate();
                
class JobDeamon():
    
    def __init__(self,num_threads):
        
        # figure out who(m) we are
        self.hostname = os.uname()[1];
        
        # make a note of when we launched
        self.start_time = datetime.datetime.now();
        
        # create a connection to SQS
        conn = SQSConnection();
        
        # ask for the JOB_QUEUE
        self.jobQueue = conn.get_queue(JOB_QUEUE);
        
        # ask for the ERR_QUEUE
        self.errQueue = conn.get_queue(ERR_QUEUE);
        
        # setup reflection for error logging etc
        self.reflection = Reflection.Reflect();
        
        # init empty list of threads
        self.threads = [];
        
        # make note of the number of requested threads
        self.num_threads = num_threads;

        # empty node states timer until we get job
        self.node_stats_timer = None;
       
    def start(self):
        
        # launch N threads 
        for i in range(0,self.num_threads):
            
            # add the thread to the list of workers
            self.threads.append(WorkerThread(self.jobQueue,self.errQueue,self.reflection));
 
            # start the thread
            self.threads[i].start();
          
        # start timer to publish node stats
        self.schedule_node_stats();
        
    def uptime_str(self):
        
        # compute the time difference from launch time
        dt = (datetime.datetime.now() - self.start_time).seconds;
        
        # compute hours
        hours = dt/3600; 
        
        # compute mins
        mins = (dt - hours*3600)/60;
        
        # compute seconds 
        secs = dt - hours*3600 - mins*60;
        
        # create string versions of each quantity
        (hourstr,minstr,secstr) = [str(e) for e in [hours,mins,secs]];
        
        # make sure they are all 2 digit
        if hours < 10:
            hourstr = '0'+hourstr;
            
        if mins < 10: 
            minstr = '0' +minstr ;
            
        if secs < 10:
            secstr = '0' +secstr ;
        
        return ':'.join((hourstr,minstr,secstr));
        
    def schedule_node_stats(self):
        
        # create a timer that periodically provides node statistics  
        self.node_stats_timer = threading.Timer(STATS_SLEEP_SECONDS,self.publish_node_stats);
  
        # start the node stats time
        self.node_stats_timer.start();
  
    def get_total_num_jobs_executed(self):
        
        total_num_jobs = 0;
        
        # ask each thread for total jobs executed
        for t in self.threads:
            total_num_jobs += t.total_job_count;
            
        return total_num_jobs;
  
    def get_avg_job_exe_time_in_seconds(self):
        
        # init
        avg_job_exe_time = float('inf'); exe_times = list();
        
        # compute the total number of jobs and avg exe times
        for t in self.threads:            
            if len(t.exe_times) > 0:
                exe_times.append(sum(t.exe_times)/float(len(t.exe_times)))
        
        # compute the overall average execution time
        if len(exe_times) > 0:
            avg_job_exe_time = sum(exe_times)/float(len(exe_times));
            
        return avg_job_exe_time;
  
    def node_stats(self):

        stats = '';

        os.sys.stderr.write('computing node stats ... \n');
            
        try:
            # initialization the host name
            if self.reflection.public_hostname is None:
                stats = os.uname()[1]+':'; 
            else:
                stats = "%-45s %12s  %6.3f" % (
                                               self.reflection.public_hostname   ,
                                               self.reflection.instance_type     ,
                                               self.reflection.current_spot_price
                                              );

            os.sys.stderr.write('initialized stats ... '+stats+'\n');

            # figure out how many jobs have been executed
            total_job_count = self.get_total_num_jobs_executed();
            
            # get the average job execution time
            avg_exe_time = self.get_avg_job_exe_time_in_seconds();
            
            # make sure this is non zero
            if avg_exe_time == 0: avg_exe_time = float('nan');
            
            # create a more human readable version of this number
            avg_exe_time_str,exe_unit = Utils.human_readable_time(avg_exe_time);
            
            # get the amount of time this scheduler has been active
            uptime = self.uptime_str();
            
            # compute the estimated number of jobs per hour from this node
            jph = ( 3600.0/float(avg_exe_time) ) * self.num_threads;

            # add the execution metadata to the stats
            stats += '  %s  %5d  %4.1f%s %6.1f\n' % ( uptime                ,
                                                      total_job_count       ,
                                                      avg_exe_time_str      ,
                                                      exe_unit[0]           ,
                                                      jph                     )
            
            # start the job counter
            i = 1;
            
            # gather stats thread by thread
            for t in self.threads:
                
                # if the thread is inactive then don't include it
                if not t.is_active(): continue;
                    
                # compute number of seconds on job
                work_time = (datetime.datetime.now() - t.start_time).seconds;
                
                # make a more human readable version of this
                work_time,unit = Utils.human_readable_time(work_time)
                
                # append stats to the stats string
                stats += '%2d  %-23s  %6.1f  %5s \n' % (i,t.job_name,work_time,unit);
                
                # update job counter 
                i += 1
                
        except Exception as e:

            os.sys.stderr('ERROR computing node_stats()\n');

            # blab about the problem on cmd line
            os.sys.stderr.write(str(e)+'\n');
            
            # note the situation in the status
            stats = 'ERROR: '+str(e)+'\n';
            
            # log error message to the error queue
            self.publish_error('publish_node_stats: '+str(e));
          
        finally:
            # all done folks
            return stats;
    
    def publish_node_stats(self):
        
        try:
        
            # create a connection to SQS
            conn = SQSConnection();
        
            # ask for the QUEUE
            q = conn.get_queue(NODE_STATS_QUEUE);
            
            # create a new message
            m = Message();
            
            # populate the message with stats
            m.set_body(self.node_stats());
            
            # publish the message to SQS
            q.write(m);
            
            # schedule another publish
            self.schedule_node_stats();
            
        except Exception as e:
            
            # blab about the err on std err
            os.sys.stderr.write(str(e)+'\n');
            
            # log error message to the error queue
            self.publish_error('publish_node_stats: '+str(e));

    def publish_error(self,err_str):

            # generate message string
            error_message_content = self.reflection.public_hostname+': '+err_str;

            # create new empty message
            error_message = Message();

            # populate the message with content
            error_message.set_body(error_message_content);

            # write the message to the error queue
            self.errQueue.write(error_message);


def main():
    
    try:
        
        # get the processor count for this machine
        num_cpu = Utils.get_processor_count();
        
        # init number of threads to the number of CPU/cores available
        num_threads = num_cpu;
        
        # if the user has requested specific number of threads
        if len(os.sys.argv) == 2:
            
            # parse requested number as an integer
            try:
                num_cpu_usr = int(os.sys.argv[1]);
            except:
                raise InfrastructureException('error parsing command line arg as int');
            
            # make sure the requested number is less than number of actual processors
            if num_cpu_usr > num_cpu:
                raise InfrastructureException('number of requested threads must be less than number of CPU/cores')
            
            # ok, now set number of threads to user specified quantity
            num_threads = num_cpu_usr;
        
    except Exception as e:
        
        # oh, crap.  blab about the exception
        os.sys.stderr.write(str(e)+'\n');
        
        # nothing else we can do 
        raise InfrastructureException('error initializing job daemon');
    else:
        
        # init
        scheduler = JobDeamon(num_threads);

        # comfort signal
        os.sys.stdout.write('Starting scheduler with '+str(num_threads)+'\n');
        
        # do the damn thing 
        scheduler.start();
      
if __name__ == '__main__':
    
    main();  