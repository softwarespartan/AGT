#!/Library/Frameworks/EPD64.framework/Versions/Current/bin/python

import scipy.io;
import numpy as np
import os;
import sys;
import getopt;
import pyDate;
import snxParse;
import Utils;

class ParseSinexException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

help_short_arg        = "h"
help_long_arg         = "help="

outdir_short_arg      = "o:"
outdir_long_arg       = "outdir="

file_short_arg        = "f:"
file_long_arg         = "file="

# shlep'em all together
short_args = help_short_arg    + \
             outdir_short_arg  + \
             file_short_arg    ;
             
long_args = []
long_args.append(help_long_arg)
long_args.append(outdir_long_arg)
long_args.append(file_long_arg);

def usage():
    
    print
    print "USAGE:  snx2mat -f /path/to/snx/file"
    print 
    print "options: "
    print
    print "-f, --file=         path to sinex file"
    print "-o, --outdir=       specify output directory for .soln file.  DEFAULT: pwd"
    print "-h, --help          show this help message and exit"
    print 
    
def get_input_args():
    
    # defaults
    file            = None;
    outdir          = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_args, long_args)
        
    except getopt.GetoptError, err:
        
        # print help information and exit:
        print str(err)
        usage()
        sys.exit(2)
        
    if len(opts)==0:
        usage();
        sys.exit();
        
    for option,arg in opts:
        
        # help arg actions
        if option in ("-h","--help"):
                usage()
                sys.exit(1)

        elif option in ("-o","--outdir"):
            
            # assign outdir
            outdir = arg
            
            # cross platform junk
            outdir = os.path.normcase(outdir)
            outdir = os.path.normpath(outdir)
            
            # make sure to expand shell vars
            outdir = os.path.expanduser(outdir);
                        
            # verify 
            if not os.path.isdir(outdir):
                raise ParseSinexException("outdir "+outdir+" does not exist")
                
        elif option in ("-f","--file"):
            file = arg;
            if not os.path.isfile(file):
                raise ParseSinexException("file "+file+" does not exist");
             
    return (file,outdir)
    
def getOutFileName(snxFile):
    
    snxFile = os.path.basename(snxFile);
    
    gpsWeek    = int(snxFile[3:7]);
    gpsWeekDay = int(snxFile[7  ]);
    
    date = pyDate.Date(gpsweek=gpsWeek,gpsweekday=gpsWeekDay);
    
    year = str(date.year); doy  = str(date.doy);

    return snxFile[0:3]+year+Utils.get_norm_doy_str(doy);

def npv(coordDict):
    
    stn_list = coordDict.keys();
    
    N = 3*len(stn_list);
    
    # mem alloc
    npv       = np.arange(N)[:,np.newaxis]*np.nan;
    npv_sigma = np.arange(N)[:,np.newaxis]*np.nan;
    
    # loop through the stnList and extract coords where possible
    for i in range(len(stn_list)):
        
        # the i'th station name in the list
        stn = stn_list[i].upper();
        
        # if the dataObj contains this station then
        if coordDict.has_key(stn):
            
            # get coordinates from dataObj 
            xyz     = np.array((coordDict[stn].X   ,coordDict[stn].Y   ,coordDict[stn].Z   ));
            sig_xyz = np.array((coordDict[stn].sigX,coordDict[stn].sigY,coordDict[stn].sigZ)); 
            
            # that's it ... pack'em away
            npv      [3*i:3*i+3] = xyz    [:,np.newaxis];
            npv_sigma[3*i:3*i+3] = sig_xyz[:,np.newaxis];
                                 
    return npv,npv_sigma;

def main():
    
    (file,outdir) = get_input_args();
    
    # get the date from the sinex file
    gpsWeek    = int(os.path.basename(file)[3:7]);
    gpsWeekDay = int(os.path.basename(file)[7  ]);
    
    # compute a data from the information
    date = pyDate.Date(gpsweek=gpsWeek,gpsweekday=gpsWeekDay);
    
    # check outdir    
    # if out dir is none then put soln file 
    # in same directory as snx files
    if outdir == None: outdir = '.';
                
    # make full path for solution file
    solnFilePath = os.path.join(outdir,getOutFileName(file));
    
    # init sinex parser for current sinex file   
    snxParser = snxParse.snxFileParser(file).parse();

    # construct npvs and npvs sigma from the sinex data
    npvs,npvs_sigma = npv(snxParser.stationDict);

    # create station list from dictionary keys
    stn_list = snxParser.stationDict.keys();
    
    # compute epoch in fractional year
    epochs = date.fyear;
    
    #extract the variance factor
    var_factor = snxParser.varianceFactor;

    # save as a mat file
    scipy.io.savemat(solnFilePath, mdict={'stnm'      :stn_list   ,  \
                                          'epochs'    :epochs     ,  \
                                          'npvs'      :npvs       ,  \
                                          'npv_sigma' :npvs_sigma ,  \
                                          'var_factor':var_factor},  \
                     oned_as = 'column');
    

if __name__ == "__main__":
    
    main() 