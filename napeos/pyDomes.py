
import re;
import os;
import random;

class domesException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Domes:

    def __init__(self, domesFile=None):
        
        self.domes = dict();
        self.file  = None;
        
        if domesFile != None:
            
            # save for later export
            self.file = domesFile;
            
            if os.path.isfile(domesFile):
                self.parseDomesFile(domesFile);
              
    def parseDomesFile(self,domesFile):
        
        # make sure the file exists before try to parse it
        if not os.path.isfile(domesFile):
            raise domesException("file "+domesFile+" does not exist");
                        
        for line in open(domesFile,'r'):
            
            # remove the white spaces from both ends
            line = line.strip()
        
            # split the line into two parts (hopefully)
            lineParts = re.split('\W+',line)
            
            # check that the line is two parts
            if len(lineParts) != 2:
                os.sys.stderr.write("line: "+line+ " has invalid format and is being rejected\n")
                continue
            
            # assign the items
            stnId       = lineParts[0]
            domesNumber = lineParts[1].upper()
            
            self.addStnWithDomes(stnId, domesNumber); 
        
    def size(self):
        return len(self.domes.keys());
    
    def containsStnId(self,stnId):
        return self.domes.has_key(stnId);
    
    def containsDomes(self, domesNumber):
        return domesNumber.upper() in self.domes.values();
    
    def generateDomesNumber(self):
        
        d5=  str(random.randint(0, 9)) \
           + str(random.randint(0, 9)) \
           + str(random.randint(0, 9)) \
           + str(random.randint(0, 9)) \
           + str(random.randint(0, 9));
        
        d = d5+"M"+"001";
        
        while self.containsDomes(d):
            
            d5=  str(random.randint(0, 9)) \
               + str(random.randint(0, 9)) \
               + str(random.randint(0, 9)) \
               + str(random.randint(0, 9)) \
               + str(random.randint(0, 9));
        
            d = d5+"M"+"001";
            
        return d;
               
    def addStn(self,stnId):

        if not self.containsStnId(stnId):
            self.domes[stnId] = self.generateDomesNumber();

        return stnId,self.domes[stnId]

    def addStnWithDomes(self,stnId,domesNumber):
        
        # make sure that the station does not already exist
        if self.containsStnId(stnId):
            raise domesException("stnId "+ stnId                   \
                                 + " already exists with DOMES# "  \
                                 + self.domesForStnId(stnId)); 
        
        # make sure that the domes number does not already exist
        if self.containsDomes(domesNumber):
            raise domesException("DOMES # "                     \
                                 +domesNumber+                  \
                                 " already exists for station " \
                                 + self.stnIdForDomes(domesNumber));
        
        self.domes[stnId] =  domesNumber;

    def stnIdForDomes(self,domesNumber):

        # do the reverse look up
        for k in self.domes.keys():
            if self.domes[k] == domesNumber:
                return k;
            
        return None;
        
    def domesForStnId(self,stnId):
        domes = None
        if self.domes.has_key(stnId):
            domes = self.domes[stnId];
        return domes

    def __iter__(self):
        for k in self.domes.keys():
            yield (k,self.domes[k])

    def export(self,exportPath=None):
        
        # make sure that there is some file to export to 
        if self.file == None and exportPath == None:
            raise domesException(" no path for export");
        
        dst = None;
        if exportPath != None:
            dst = exportPath;
        else:
            dst = self.file;
        
        fid = open(dst,'w');
        
        for key in self.domes.keys():
            fid.write(key + " " + self.domes[key]+"\n");
            
        fid.close();

    def stn_list(self):
        return self.domes.keys()