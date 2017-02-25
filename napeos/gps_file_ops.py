
import os
from file_ops import *
from gps_file_types import *

RNX2CRXPATH = ""

def rnx_rename(rnxFilePath, newName):
    
    # check input args
    if len(newName) != 4:
        print "ERROR: invalid rinex file name: "+newName
        return
    
    # check that the file exists
    if not os.path.exists(rnxFilePath) or  not os.path.isfile(rnxFilePath):
        print "ERROR:  Rinex file: " + rnxFilePath + " does not exist!!!"
        return
    
    # now, isolate the name of the rinex file
    (dir, rnxFileName) = os.path.split(rnxFilePath)
    
    # make new rinex file path
    newRnxFilePath = os.path.join(dir, newName + rnxFileName[4:] );
    
    try:
        os.system("mv "+rnxFilePath+" "+ newRnxFilePath);
    except:
        print "ERROR:  Could not rename rinex file: "+rnxFilePath+" !!!"

def rnx2crx(file):

    (dir, file_name) = os.path.split(file);
    
    cd_cmd = "cd "+ dir + ";"
    rnx2crx_cmd = "rnx2crx -f " + file_name + ";"
    
    exit_status = os.system(cd_cmd + rnx2crx_cmd)
    
    if exit_status !=0:
        print "ERROR: Could not compact [crx] the file" + file + "!!!"
        
    return exit_status    

def rnx2crz(file_path):
    
    exit_status = rnx2crx(file_path)
    
    if exit_status == 0:
        exit_status = compress(file_path[:-1]+'d');
    
    return exit_status

def o2ddotZ(dir=os.getcwd()): 
                      
    for zip_file in get_zip_file_list(dir):
        unzip(zip_file)
        
    for odotZ_file in get_odotZ_file_list(dir):
        uncompress(odotZ_file)
      
    for obs_file in get_obs_file_list(dir) :
        
        rnx2crx_exit_status = rnx2crx(obs_file)
        d_file = obs_file[0:-1]+"d"
        
        if rnx2crx_exit_status !=0:
            # rnx2crx failed :(
            try_delete(d_file)
            compress(obs_file)
        else:
            # here rnx2crx was a success :)
            compress_exit_status = compress(d_file)
            try_delete(obs_file)   
            
    for nav_file in get_nav_file_list(dir):
        try_delete(nav_file)

def test():
    
    file = '/media/fugu/data/gps/rinex/igs/alrt/2009/070/alrt0700.09o'
    rnx2crz(file);   
         
#    for stn_list in stn_file_list:
#        print stn_list;
if __name__ == "__main__":
    test()
