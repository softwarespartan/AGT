
import os, shutil, datetime, Synchronization;

# specify some large file copy
src = "/Users/abelbrown/Downloads/test.tar"
dst = "/Users/abelbrown/Downloads/test.cpy"

lockfile='copy';

# init new lock
lock = Synchronization.ProcessLock(lockfile);

# blab about aquiring the lock
print datetime.datetime.now(),os.getpid(),'will aquire lock ...';

# aquire lock
lock.aquire();

try:
    
    # if the dst does not exist make a copy of it
    if not os.path.isfile(dst):
        
        # blab to the user what's going on
        print datetime.datetime.now(),os.getpid(),'will copy file';
        
        # do the file copy
        shutil.copyfile(src, dst);
        
        print datetime.datetime.now(),os.getpid(),'did copy the file'
    else:
        
        # blab to the user that we found what we're looking for
        print datetime.datetime.now(),os.getpid(), 'found the file';
finally:
    
    # more blabing
    print datetime.datetime.now(),os.getpid(),'will release lock'
    
    # don't forget!
    lock.release();