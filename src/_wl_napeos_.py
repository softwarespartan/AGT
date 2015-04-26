#!/usr/bin/python
'''
Created on Mar 29, 2013

@author: abelbrown
'''

#!/usr/bin/python

import os, JobSpecification;

class _wl_gamit_Exception(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def main():
    
    # get the input arguments without program name
    args = os.sys.argv[1:];
    
    # initialize new job specification
    spec = JobSpecification.JobSpecification('wl_napeos');
    
    # create new job template
    job = spec.job_template(args);

    # blab about it to standard out
    os.sys.stdout.writelines(spec.asXML(job));
    
    
if __name__ == "__main__":
    
    main()