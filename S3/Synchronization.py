
import os, datetime;

class ProcessLockException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class ProcessLock():
    
    def __init__(self,lockKey):
        self.lockKey = lockKey+'.lock';
        
    def aquire(self):        
        status = os.system('lockfile '+self.lockKey);
        
        if status != 0:
            raise ProcessLockException('Could not aquire ProcessLock '+self.lockKey);
            
    def release(self):        
        status = os.system('rm -f '+self.lockKey);
        if status != 0:
            raise ProcessLockException('Could not release ProcessLock '+self.lockKey);
        