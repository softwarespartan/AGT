

CPU_THRESHOLD = 1.0;

import boto,datetime,os;

# connect to EC2 service
ec2_conn = boto.connect_ec2       ();
cw_conn  = boto.connect_cloudwatch();

# get list of reservations
reservations = ec2_conn.get_all_instances();

# initialize count of instances
inst_count = 0;

# go through each instance
for r in reservations:
    
    for inst in r.instances:
        
        # if not running the don't bother getting metric    
        if inst.state != 'running': continue
            
        # update the instance count
        inst_count += 1;
        
        # get list of cloud watch metrics for this instance
        metrics = cw_conn.list_metrics(                                     \
                                       dimensions={'InstanceId' : inst.id}, \
                                       metric_name='CPUUtilization'         \
                                      )
        
        # if we got a metric return for this query then try que ry for data
        if len(metrics) == 1:
            
            TERM='terminate'
            
            # initialize cpu usage to really large number
            cpu_avg_usage = float('inf');
            
            # extract the metric from the list 
            m = metrics[0];
            
            # get the end datetime in UTC
            dt_end = datetime.datetime.utcnow();
            
            # compute the start datetime for 30 mins ago UTC
            dt_start = dt_end - datetime.timedelta(minutes=10);
            
            # query for average cpu utilization over periods of 5 mins
            cpu_usage_results = m.query(dt_start, dt_end, 'Average', period=60*5)
            
            # compute the max average
            if len(cpu_usage_results) > 0:
                cpu_avg_usage = max([e['Average'] for e in cpu_usage_results]);  
                
                # defensive conversion to float
                try:
                    cpu_avg_usage = float(cpu_avg_usage);
                except:
                    
                    # blab at the user about the problem
                    os.sys.stderr.write('could not parse cpu usage for instance',inst.id);
                    
                    # but continue onto next instance rather than raise error
                    continue
            
            # if the average cpu usage is OK then don't print termination
            if cpu_avg_usage >= CPU_THRESHOLD: TERM='';
                
            # print off some interesting information
            print '%10s  %10s  %10s  %7.3f %10s' % (inst.id,             \
                                                    inst.instance_type,  \
                                                    inst.placement,      \
                                                    cpu_avg_usage,       \
                                                    TERM);
                                                  
            # it has got to be done!
            if cpu_avg_usage < CPU_THRESHOLD:
                inst.terminate();
        
# print the total number of running instances
print "number of running instances: ",inst_count