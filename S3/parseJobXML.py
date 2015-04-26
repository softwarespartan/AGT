

import xml.etree.ElementTree as ET

import Infrastructure

xml = """
<jobSpecification>
    <job name="glbd.aws.2007.333.n3" command="wl_gamit">
        <arg>--stn=igs.cast</arg>
        <arg>--stn=igs.ceda</arg>
        <arg>--stn=igs.coon</arg>
        <arg>--stn=igs.egan</arg>
        <arg>--stn=igs.elko</arg>
        <arg>--stn=igs.eout</arg>
        <arg>--stn=igs.foot</arg>
        <arg>--stn=igs.gabb</arg>
        <arg>--stn=igs.garl</arg>
        <arg>--stn=igs.gosh</arg>
        <arg>--stn=igs.lewi</arg>
        <arg>--stn=igs.lmut</arg>
        <arg>--stn=igs.mine</arg>
        <arg>--stn=igs.naiu</arg>
        <arg>--stn=igs.news</arg>
        <arg>--stn=igs.rbut</arg>
        <arg>--stn=igs.ruby</arg>
        <arg>--stn=igs.shin</arg>
        <arg>--stn=igs.smel</arg>
        <arg>--stn=igs.tung</arg>
        <arg>--stn=igs.upsa</arg>
        <arg>--stn=igs.farb</arg>
        <arg>--stn=igs.harv</arg>
        <arg>--stn=igs.sio3</arg>
        <arg>--stn=igs.drao</arg>
        <arg>--stn=igs.uclu</arg>
        <arg>--stn=igs.quin</arg>
        <arg>--stn=igs.slid</arg>
        <arg>--stn=igs.tono</arg>
        <arg>--stn=igs.orvb</arg>
        <arg>--stn=igs.ybhb</arg>
        <arg>--stn=igs.burn</arg>
        <arg>--stn=igs.lkwy</arg>
        <arg>--stn=igs.redm</arg>
        <arg>--stn=igs.tmgo</arg>
        <arg>--stn=igs.mbww</arg>
        <arg>--stn=igs.pltc</arg>
        <arg>--stn=igs.amc2</arg>
        <arg>--year=2007</arg>
        <arg>--doy=333</arg>
        <arg>--network_id=n3</arg>
        <arg>--expt=glbd</arg>
        <arg>--org=aws</arg>
        <arg>--minspan=6</arg>
        <arg>--sp3_type=osf</arg>
    </job>

</jobSpecification>
"""

class JobParserException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def parse_job(xmlstr):
    
    # init the element tree from xml string
    root = ET.fromstring(xmlstr);
    
    # init empty job dict
    jobs = dict();
    
    # look for job nodes
    for job in root.getiterator('job'):
             
        # (re)init arg list
        arg_list = []; 
        
        # make sure the xml specifiy proper shit
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
    
if __name__ == '__main__':
    
    #jobs = parse_job(xml);
    
    jobs = Infrastructure.parse_job(xml)
    
    for j in jobs.keys():
        print j, jobs[j];