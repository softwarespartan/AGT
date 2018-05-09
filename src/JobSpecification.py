#!/usr/bin/python

import os,re;

class _wl_gamit_Exception(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class JobSpecification():
    
    def __init__(self,command):
        self.command = command;
    
    def getXmlHeader(self,jobName=None):
        
        if jobName == None:
            header = "<jobSpecification>\n";
        else:
            header = "<jobSpecification name=\""+jobName+"\">\n";
        return header

    def getXmlBody(self, jobDict):
        
        ws="\t";
        jobString = ws+"<job name=\""+jobDict['name']+"\" command=\""+jobDict['command']+"\">\n";
        
        for arg in jobDict['argList']:
            jobString += ws*2+"<arg>"+arg+"</arg>\n";
                
        jobString += ws+"</job>\n";
        
        return jobString;

    def getXmlFooter(self):
        
        header = "</jobSpecification>"    
        return header
 
    def asXML(self,jobDict):
        
        xmlstr  = self.getXmlHeader();
        xmlstr += self.getXmlBody(jobDict);
        xmlstr += self.getXmlFooter();
        
        return xmlstr
    
    def job_template(self,sys_args):
        
        # init new job dict with some basic infomation
        job = dict(); job['command']  = self.command; job['argList'] = list();
        
        # see if the file as been specified
        file_arg = [arg for arg in sys_args if arg.startswith('--file')];
        
        if len(file_arg) == 1:
            
            # convert from list to string
            file_arg = file_arg[0];
            
            # make sure only two parts to the file arg
            if len(re.split('=',file_arg)) != 2:
                raise _wl_gamit_Exception('invalid file arg: '+file_arg);
            
            # isolate file path
            file_path = re.split('=',file_arg)[1];
            
            # extract the lines from the file
            with open(file_path,'r') as fid: stn_list = fid.readlines();
                
            # clean up stn_id entries
            stn_list = [stnId.strip() for stnId in stn_list];
                
            # replace old resource delimiter with existing delimiter
            stn_list = [stnId.replace('::','.') for stnId in stn_list];
            
            # trun stnIds into command line args
            stn_list = ['--stn='+stnId for stnId in stn_list];
            
            # add command line args to job specification
            for arg in stn_list: job['argList'].append(arg);
            
            # now, remove entry from arg list fo does not get re-added
            sys_args.remove(file_arg);
            
            # isolate the stn list file name
            file_name = os.path.basename(file_path);
                    
            # compute the year and day of year from stn list file
            if len(re.split('\.',file_name))==5:
                
                # init
                (org,expt,year,doy,net_id) = re.split('\.',file_name);

                # set the year for the job
                job['argList'].append('--year=' + str(year));

                # set the day of year for the job
                job['argList'].append('--doy=' + str(doy));

                # set the network id for the job
                job['argList'].append('--network_id=' + net_id);

                # set the org arg
                job['argList'].append('--org='+org);

                # set the expt arg
                job['argList'].append('--expt='+expt);
                        
        # forward all remaining args from the command line
        for arg in sys_args: job['argList'].append(arg);
        
        # construct a job name default job name
        expt = 'no'; org = 'name'; year = ''; doy = ''; net = None;
        
        #  see if we can populate from args
        for arg in job['argList']:
            
            if arg.startswith('--expt='):
                expt = re.split('=',arg)[1];
                
            elif arg.startswith('--org='):
                org = re.split('=',arg)[1];
            
            elif arg.startswith('--year='):
                year = re.split('=',arg)[1];
                
            elif arg.startswith('--doy='):
                doy = re.split('=',arg)[1];
                
            elif arg.startswith('--network_id='):
                net = re.split('=',arg)[1];
                
        # set the job name
        job['name'] = '.'.join((org,expt,year,doy));
        
        # add network id if defined
        if net != None:
            job['name'] = '.'.join((job['name'],net));
    
        # that's all  
        return job;


def main():
    
    # get the input arguments without program name
    args = os.sys.argv[1:];
    
    # initialize new job specification
    spec = JobSpecification('wl_globk');
    
    # create new job template
    job = spec.job_template(args);

    # blab about it to standard out
    os.sys.stdout.writelines(spec.asXML(job));
    
    
if __name__ == "__main__":
    
    main()
