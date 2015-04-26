
import os
import zipfile

def inflate(file):
    
    if file[-2:] == '.Z':
        uncompress(file);
        return file[:-2];
    if file[-3:] == '.gz':
        gunzip(file);
        return file[:-3];
    if file[-4:] == '.zip':
        unzip(file);
        return file[:-4];
    
    # no compression
    return file;

def unzip(file):
    (dir, file_name) = os.path.split(file);
    try:
        zfobj = zipfile.ZipFile(file)
        for name in zfobj.namelist():
            if name.endswith('/'):
                os.mkdir(os.path.join(dir, name))
            else:
                outfile = open(os.path.join(dir, name), 'wb')
                outfile.write(zfobj.read(name))
                outfile.close
        try_delete(file)  
    except:
        print "ERROR: Could not unzip the file: "+file+"!!!"
                         
def compress(file):
    exit_status = os.system("compress -f " + file)
    
    if exit_status !=0:
        print "ERROR: Could not compress file " + file + " !!!"
        
    return exit_status

def uncompress(file):
    exit_status = os.system("compress -fd " + file)
    
    if exit_status !=0:
        print "ERROR: Could not uncompress file " + file + " !!!"
        
    return exit_status

def try_delete(file):
    if os.path.exists(file) and os.path.isfile(file):
        try:
            os.remove(file)
        except:
            print "ERROR:  The file: "+ file +" could not be deleted!!!"

def gunzip(file):

    exit_status = os.system('gunzip -f '+file)
    
    if exit_status !=0:
        print "ERROR: Could not gunzip file " + file + " !!!"
        
    return exit_status            

def gzip(file):
    exit_status = os.system('gzip -f '+file)
    
    if exit_status != 0:
        print "ERROR: Could not gzip file " + file + " !!!"
        
    return exit_status