
import os;
import re;
import sys;
import archexpl;
import string
import random;
import pyDate;

class StnInfoParseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class AprParseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class AprSigmaParseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class StnMetadataException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class StnRegistryException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def convertDate(year,doy):
    
    aDate = pyDate.Date(year=year,doy=doy);
    
    #return date(aDate.year,aDate.month,aDate.day);
    return aDate;

class Receiver():
    
    def __init__(self,type,vers,swVers,sn):
        self.type   = type;
        self.vers   = vers;
        self.swVers = swVers
        self.sn     = sn;
        
    def isValid(self):
        if self.type.startswith('-') or len(self.type) == 0:
            return False;
        
        return True;

class Antenna():
    
    def __init__(self,type,dome,ht,n,e,htCod,sn):
        self.type  = type;
        self.dome  = dome;
        self.ht    = float(ht);
        self.e     = float(e);
        self.n     = float(n);
        self.htCod = htCod;
        self.sn    = sn;
        
    def isValid(self):
        if self.type.startswith('-') or len(self.type) == 0:
            return False;
        
        return True;

class StnInfoLine():
    
    def __init__(self,string):
        
        # where it all begins 
        if string[0] != ' ':
            raise StnInfoParseException('First character of station info line must be space!');
        
        # save original line for exporting etc
        self.line = string;
        
        # get the name of the station
        self.stnName = self.line[1:5].lower();
        self.oriName = self.stnName;
        
        # get the start date of the entry
        try:
            startYear = int(self.line[25:29]);
            startDoy  = int(self.line[30:33]);
            #self.startDate = convertDate(startYear,startDoy);
            self.startDate = pyDate.Date(year=startYear,doy=startDoy);
            
            # get the stop date of the entry
            stopYear  = int(self.line[44:48]);
            stopDoy   = int(self.line[49:52]); 
        except:
            raise StnInfoParseException("Could not parse dates from station info line ["+self.stnName+"]: "+ self.line)
       
        # check that the stop date is not indefinate
        if stopYear == 9999:
            self.stopDate = pyDate.Date(year=2050,doy=1);
        else:      
            self.stopDate  = pyDate.Date(year=stopYear,doy=stopDoy);
            

        # check that start and stop date are increaseing
        if self.stopDate < self.startDate:
            raise StnInfoParseException("[%s]Invalid station info line: start date greater than stop date"%self.stnName);
            #os.sys.stderr.write('ERROR: invalid station info line '+self.line+'\n');

        # count the number of days for this entry
        self.numDays = (self.stopDate.mjd - self.startDate.mjd)+1;
         
        # next parse out antenna heighting        
        antHt    = float(self.line[64:70]);
        htCod    = self.line[72:77].strip();
        antN     = self.line[80:86];
        antE     = self.line[89:95];
        antType  = self.line[170:185].strip();
        antDome  = self.line[187:192].strip();
        antSN    = self.line[194:214].strip().split(" ")[0];
        
        if antDome.startswith("-"):
            antDome = "NONE";
        
        # parse out receiver info
        rxType   = self.line[97:117].strip();
        rxVers   = self.line[119:139].strip();
        rxSwVers = self.line[141:146].strip();
        rxSN     = self.line[148:168].strip();
        
        # assign equipment 
        self.rx  = Receiver(rxType,rxVers,rxSwVers,rxSN) 
        self.ant = Antenna(antType,antDome,antHt,antN,antE,htCod,antSN);
         
    def isValid(self):
        
        if self.rx.isValid()\
            and self.ant.isValid()\
                and self.numDays > 0:
            return True;
        
        return False;
       
    def overlapsByDate(self,otherStnInfoLineObj):
        
        objA = self;
        objB = otherStnInfoLineObj
        
        # swap to put in order if needed
        if objB.startDate < objA.startDate:
            tmp  = objA;
            objA = objB;
            objB = tmp;
        
        #  objA  start-------------stop
        #  objB            start----------stop

        if objA.startDate == objB.startDate and objA.startDate == objB.stopDate:
            return False

        if objA.stopDate <= objB.startDate:
            return False;
        return True; 
    
    def hasSameStnName(self, otherStnInfoLineObj):
             
        return self.stnName == otherStnInfoLineObj.stnName;
    
    def goesTogetherWith(self, otherStinInfoLineObj):
        
        return not self.overlapsByDate(otherStinInfoLineObj) \
                and self.hasSameStnName(otherStinInfoLineObj)
    
    def setName(self, newName):
        if len(newName) == 4:
            self.stnName   = newName.lower();
            self.line = ' '+ newName.upper() + self.line[5:];
            
    def restoreOriginalName(self):
        self.stnName  = self.oriName.lower();
        self.line[1:5]= self.oriName.upper();
        
    def Print(self,fid = None):
        
        if not self.isValid():
            return;
        
        if fid == None:
            print ' '+self.line.strip();
        else:
            fid.write(' '+self.line.strip()+'\n');
        
     
class AprObj(object):
    
    def __init__(self,input = None):
                
        self.stnName  = None;
        self.oriName  = None;
        self.X        = None;
        self.Y        = None;
        self.Z        = None;
        self.velX     = 0;
        self.velY     = 0;
        self.velZ     = 0;
        self.refEpoch = None;
        self.isValid  = False;
        
        if input == None:
            return ;
        
        if not isinstance(input,str):
            raise AprParseException('input for AprObj constructor not recognized.  must be string!');
        
        if os.path.isfile(input):
            try:
                fid = open(input,'r');
                src = fid.readline();
                fid.close();
            finally:
                fid.close();
        else:
            src = input;
            
        lineParts = re.split('\s+',src.strip());
        
        if len(lineParts) < 8:
            raise AprParseException('input line of Apr must contain at least 9 values!');
        else:
#            self.initWithValues(lineParts[0][0:4], lineParts[1], lineParts[2], lineParts[3],\
#                                     lineParts[4], lineParts[5], lineParts[6], lineParts[7]);
                                     
            self.initWithValues(lineParts[0][0:4], lineParts[1], lineParts[2], lineParts[3],\
                                     0, 0, 0, lineParts[7]);

    
    def initWithValues(self,stnName, X, Y, Z, velX, velY, velZ, refEpoch):
        
        self.isValid = False
        try:
            self.stnName  = stnName.lower();
            self.oriName  = stnName.lower();
            self.X        = float(X);
            self.Y        = float(Y);
            self.Z        = float(Z);
            self.velX     = float(velX);
            self.velY     = float(velY);
            self.velZ     = float(velZ);
            self.refEpoch = float(refEpoch);
            self.isValid  = True;
        except Exception,e:
            print sys.exc_info()
            raise AprParseException('Error initializing aprObj!!');
        
        return self
        
    def isEqual(self,anotherAprObj):

        if abs(self.X - anotherAprObj.X) == 0\
            and abs(self.Y - anotherAprObj.Y) == 0\
                and abs(self.Z - anotherAprObj.Z) == 0:
            return True;
        else:
            return False; 
        
    def setName(self,newName):
        self.stnName = newName            

    def Print(self,fid=None):
        
        if not self.isValid:
            return;
        
        line = " %s_GPS %12.3f %12.3f %12.3f %8.4f %8.4f %8.4f %9.3f" \
            % (self.stnName.upper(),\
                 self.X,self.Y,self.Z,self.velX,self.velY,self.velZ,self.refEpoch);

        if fid == None:
            print line;
        else:
            fid.write(line+'\n');
            
    def export(self,path):
        
        if not self.isValid:
            return;
        
        if not isinstance(path,str):   
            raise AprParseException('export(path): takes string as input arg');
       
#        if not os.path.isdir(path):
#            raise AprParseException('path: '+path+' does not exist!!!');
        
#        fileName = self.stnName+'.apr';
        
        filePath = path;
        
#        if path.endswith('/'):
#            filePath = os.path.join(path,fileName);

        fid = open(filePath,'w');
            
        try:
            self.Print(fid);
        finally:
            fid.close();
        

    def getName(self):
        return self.stnName;

    def setApr(self,X,Y,Z,refEpoch=2004.5):
        self.X  = float(X);
        self.Y  = float(Y);
        self.Z  = float(Z);
        self.refEpoch = float(refEpoch);
        
        # incase obliatory init from stnMetadataMgrObj
        # then init, set, export but 
        # export will not export unless isvalid = true
        self.isValid=True;

class AprCollection():
    
    def __init__(self,input=None):
        
        self.iterIndx = 0;
        self.iterList = None;
        
        self.aprDict = dict(); 
        self.pattern = re.compile('^\s(\w+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)');
        
        # empty collection
        if input == None:
            return;
        
        self.parseInput(input)
        
    def parseInput(self, input):
        
        src = None;
        shouldCloseSrc = False;
        if os.path.isfile(input):
            src = open(input,'r');
            shouldCloseSrc = True;
        else:
            src = input;        
       
        # loop through 
        for line in src:
                    
            line = line.replace('-.', '-0.');
            line = line.replace(' 0 ',' 0.0 ');
            match = self.pattern.findall(line);
        
            if match:
                
                (stnName,X,Y,Z,velX,velY,velZ,refEpoch) = match[0];
                
                stnName = stnName[0:4].lower();
                
                aprObj = AprObj().initWithValues(stnName,X,Y,Z,velX,velY,velZ,refEpoch);
                
                # make sure it's not a duplicate coord
                if self.aprDict.has_key(stnName) \
                    and not self.aprDict[stnName].isEqual(aprObj):
                    raise AprParseException('Duplicate station apr: '+stnName);
                else:
                    self.aprDict[stnName] = aprObj;
                    
        if shouldCloseSrc: 
            src.close();
        
        return self;
                        
    def add(self,input):
        self = self.parseInput(input);
        
    def contains(self,stnName):
        return self.aprDict.has_key(stnName.lower());
    
    def size(self):
        return len(self.aprDict.keys())
        
    def setName(self,oldName,newName):
        
        # format names to match keys
        oldName = oldName.lower();
        newName = newName.lower();
        
        if not self.contains(oldName):
            # goddamnit folks check this shit
            raise AprParseException('Apr Collection does not contain station' + oldName);
        
        # make copys
        aprObj = self.aprDict[oldName];
        
        # remove from dictionary 
        del self.aprDict[oldName];
        
        # set the name of the apr object to new name
        aprObj.setName(newName)
        
        # add new key + updated apr obj to the dictionary
        self.aprDict[newName] = aprObj;
         
    def getApr(self,stnName):
        stnName = stnName.lower();
        
        if not self.contains(stnName):
            # goddamnit folks check this shit
            raise AprParseException('Apr Collection does not contain station ' + stnName);
        
        return self.aprDict[stnName];
    
    # iterator protocol
    def __iter__(self):
        return self
    
    # iterator protocol
    def next(self):
        
        if self.iterList ==None:
            self.iterList = self.aprDict.keys();
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            obj = self.aprDict[self.iterList[self.iterIndx]];
            self.iterIndx += 1;
            return obj
     
class StnInfoObj():
    
    def __init__(self,input = None):
        
        # iteratoion protocol 
        self.iterIndx = 0;
        self.iterList = None;
        
        # data structure to hold the collection of lines
        self.stnInfoLineList = list();
        
        if input != None:
            self.add(input);
        
    def add(self,input):
        
        if type(input) == type(str())\
            or isinstance(input,list):
            self.addStnInfoLineSrc(input);
        elif isinstance(input,StnInfoLine):
            self.addStnInfoLineObj(input);
        else:
            print repr(type(input)) +" not recognized!"
            raise StnInfoParseException('input must be string, file path, or StnInfoLine object!!');

    def addStnInfoLineSrc(self,input):
        
        shouldCloseSrc = False;
        if isinstance(input,str) and os.path.isfile(input):
            shouldCloseSrc = True;
            src = open(input,'r');
        else:
            src = input;
        
        for line in src:
            if line[0] == ' ':
                stnInfoLineObj = StnInfoLine(line);
                self.addStnInfoLineObj(stnInfoLineObj);
                
        if shouldCloseSrc:
            src.close();
            
    def addStnInfoLineObj(self,anotherStnInfoLineObj):
        
        if not isinstance(anotherStnInfoLineObj,StnInfoLine):
            raise StnInfoParseException('Item to add must be StnInfoLine object type!');
        
        if self.canAddStnInfoLineObj(anotherStnInfoLineObj):
            self.stnInfoLineList.append(anotherStnInfoLineObj);
        else:
            raise StnInfoParseException('Station info src must contain non overlapping chronological entries for single station!!!');
         
    def canAddStnInfoLineObj(self,otherStnInfoLineObj):
        
        olineObj  = otherStnInfoLineObj;
        
        # need to check that the name of the station matches ever
        # other line in the list and that dates spans do not
        # overlap in any way
        
        for lineObj in self.stnInfoLineList:
            
            if olineObj.overlapsByDate(lineObj) \
                or not olineObj.hasSameStnName(lineObj):
                
                #print olineObj.overlapsByDate(lineObj);
                #lineObj.Print();
                #olineObj.Print();
                return False;

            #if olineObj.startDate > lineObj.stopDate:
            #    return False;
            
        return True;   
    
    def Print(self,fid = None):
        
        lineList = sorted(self.stnInfoLineList, key=lambda obj: obj.startDate);
        for line in self.stnInfoLineList:
            line.Print(fid);

    def getName(self):
        if len(self.stnInfoLineList) == 0:
            return None;
        else:
            return self.stnInfoLineList[0].stnName; 
            
    def setName(self,newName):
        
        # format names to match keys
        newName = newName.lower();

        for obj in self.stnInfoLineList:
            obj.setName(newName);  
            
    def export(self,path):
        
        if not isinstance(path,str):   
            raise StnInfoParseException('export(path): takes string as input arg');
       
#        if not os.path.isdir(path) or os.path.isfile(path):
#            raise StnInfoParseException('path: '+path+' does not exist!!!');
        
        fileName = self.getName()+'.station.info';
        
        if path.endswith('.station.info'):
            filePath = path;
        else:
            filePath = os.path.join(path,fileName);
        
        fid = open(filePath,'w');
        
        try:
            self.Print(fid);
        finally:
            fid.close();
            
    def getStnInfo(self,date):
        for line in self.stnInfoLineList:
            if line.startDate <= date <= line.stopDate:
                return line
        return None

    def stnInfoForYearDoy(self,year,doy):
        return self.getStnInfo(pyDate.Date(year=year,doy=doy))
    
    def __iter__(self):
        return self
    
    # iterator protocol
    def next(self):
        
        if self.iterList is None:
            self.iterList = sorted(self.stnInfoLineList, key=lambda obj: obj.startDate);
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            obj = self.iterList[self.iterIndx];
            self.iterIndx += 1;
            return obj;
        
    def size(self):
        return len(self.stnInfoLineList);
        
class StnInfoCollection():
    
    def __init__(self, input = None):
        
        # iteration protocol variables
        self.iterIndx = 0;
        self.iterList = None;
        
        # init the data structrue
        self.stnInfoDict = dict();
        
        if input != None:
            self.add(input);
        
    def add(self,input):
        
        if type(input) == type(str())\
            or isinstance(input,list):
            self.parseInput(input);
        elif isinstance(input,StnInfoObj):
            self.addStnInfoObj(input);
        else:
            print repr(type(input)) +" not recognized!"
            raise StnInfoParseException('input must be string, file path, or StnInfoCollection object!!');
        
    def addStnInfoObj(self,obj):
        
        name = obj.getName();
        
        if self.stnInfoDict.has_key(name):
            raise StnInfoParseException('Station already exists in station info collection!!');
        else:
            self.stnInfoDict[name] = obj;
        
    def parseInput(self,input):
        
        src = None;
        shouldCloseSrc = False;
        if isinstance(input,str) and os.path.isfile(input):
            src = open(input,'r');
            shouldCloseSrc = True;
        else:
            src = input;        
       
        lockList = list();
       
        # loop through 
        prevStnName = '';
        for line in src:
            
            if line[0] == ' ' and line[1] != '*':
                stnInfoLine = StnInfoLine(line);
            else:
                continue
            
            if prevStnName == '':
                prevStnName = stnInfoLine.stnName;
            
            if stnInfoLine.stnName != prevStnName:
                lockList.append(prevStnName)
                
            if stnInfoLine.stnName in lockList:
                raise StnInfoParseException('Duplicate station '+stnInfoLine.stnName+' found in src!!!' );
            
            # no entry yet for this station
            if not self.contains(stnInfoLine.stnName):
                self.stnInfoDict[stnInfoLine.stnName] = StnInfoObj(stnInfoLine);

            else:
                # have entries for this station now have to make sure we can add the line
                # to the station info object 
                if self.stnInfoDict[stnInfoLine.stnName].canAddStnInfoLineObj(stnInfoLine):
                    self.stnInfoDict[stnInfoLine.stnName].add(stnInfoLine);
                else:
                    #self.stnInfoDict[stnInfoLine.stnName].Print()
                    raise StnInfoParseException('Could not add station.info line : '\
                                                +line);
            # update 
            prevStnName = stnInfoLine.stnName
                     
        # close file if src was a file                           
        if shouldCloseSrc:
            src.close();
        
    def contains(self,stnName):
        stnName = stnName.lower();
        return self.stnInfoDict.has_key(stnName);
    
    def getStnInfo(self,stnName):
        
        return self.stnInfoDict[stnName.lower()];
    
        # iterator protocol
    def __iter__(self):
        return self
    
    # iterator protocol
    def next(self):
        
        if self.iterList ==None:
            self.iterList = self.stnInfoDict.keys();
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            key = self.iterList[self.iterIndx];
            obj = self.stnInfoDict[key];
            self.iterIndx += 1;
            return obj
  
    def size(self):
        return len(self.stnInfoDict.keys());
    
    def numberOfLines(self):
        nLines = 0;
        for stnInfo in self:
            nLines = nLines + stnInfo.size();
        return nLines
            
  
class AprSigmaObj():
    
    def __init__(self, input = None):
        
        self.line = None;
    
        self.oriName = None;
        self.stnName = None;
        self.sigX = 30;
        self.sigY = 30;
        self.sigZ = 30;
        
        if input != None:
            self.parseInput(input);
        
        
    def initWithValues(self,stnName,sigX,sigY,sigZ):
        
        if len(stnName) != 4:
            raise AprSigmaParseException('new name must be 4 char long');
        
        self.stnName = stnName.lower();
        self.oriName = self.stnName;
        
        try:
            self.sigX    = float(sigX);
            self.sigY    = float(sigY);
            self.sigZ    = float(sigY);
        except:
            raise AprSigmaParseException('invalid sigma values!');

        return self;
             
    def parseInput(self,input):
        
        if not isinstance(input,str):
            raise AprSigmaParseException("input must be a string or file path!")
        
        if  os.path.isfile(input):
            src = open(input,'r');
            shouldCloseSrc = True;
            line = src.readline().strip();
            src.close();
        else:
            line = input;
        
        self.line = line;
        lineParts = re.split('\s+',line.strip());
        
        if len(lineParts) != 6:
            raise AprSigmaParseException('Line '+line +' is invalid format!');
        
        self.stnName = lineParts[0].lower();
        self.oriName = self.stnName;
        
        try:
            self.sigX    = float(lineParts[3]);
            self.sigY    = float(lineParts[4]);
            self.sigZ    = float(lineParts[5]);
        except:
            raise AprSigmaParseException('Line '+line +' is invalid format!');
        
        return self;
    
    def setAprSigma(self,sigX,sigY,sigZ):
        
        try:
            self.sigX = float(sigX);
            self.sigY = float(sigY);
            self.sigZ = float(sigZ);
        except:
            raise StnMetadataException('Could not convert sigX sigY sigZ to float');
        
    def setLessThan(self,sigX,sigY,sigZ):
        
        try:
            sigX = float(sigX);
            sigY = float(sigY);
            sigZ = float(sigZ);
        except:
            raise StnMetadataException('Could not convert sigX sigY sigZ to float');
            
        if sigX < self.sigX and sigY < self.sigY and sigZ < self.sigZ:

            self.sigX = sigX;
            self.sigY = sigY;
            self.sigZ = sigZ;
                
    
    def Print(self,fid = None):
        
        # defult values
        wX = "%5.3f";
        wY = "%5.3f";
        wZ = "%5.3f";
        
        # apr over or at 10 [m]
        if self.sigX >= 10:
            wX = "%5.2f"
            
        if self.sigY >= 10:
            wY = "%5.2f"
            
        if self.sigZ >= 10:
            wZ = "%5.2f"
            
        # for apr sigma over 100 [m] 
        # should never happen but who knows
        if self.sigX >= 100:
            wX = "%5.1f"
            
        if self.sigY >= 100:
            wY = "%5.1f"
            
        if self.sigZ >= 100:
            wZ = "%5.1f"
            
        line = "%s %s_GPS     NNN    "+wX+" "+wY+" "+wZ;
        line = line \
            % (self.stnName.upper(),self.stnName.upper(),\
                    float(self.sigX),float(self.sigY),float(self.sigZ));
        
        if fid == None:
            print line;
        else:
            fid.write(line + "\n");
            
    def setName(self,newName):
        
        if len(newName) != 4:
            raise AprSigmaParseException('new name must be 4 char long');
        
        if self.line != None:
            self.line    = newName.upper()+self.line[4:];
        self.stnName = newName.lower();
        
        if self.oriName == None:
            self.oriName = self.stnName;
        
        return self;
    
    def setSigmasTo30cm(self):
        
        self.sigX = 0.30;
        self.sigY = 0.30;
        self.sigZ = 0.30;
        
        return self;
 
    def export(self,path):
        
        if not isinstance(path,str):   
            raise StnInfoParseException('export(path): takes string as input arg');
       
#        if not os.path.isdir(path):
#            raise StnInfoParseException('path: '+path+' does not exist!!!');
        
#        fileName = self.stnName+'.apr.sigma';
        
        filePath = path;
        
#        if path.endswith('/'):
#            filePath = os.path.join(path,fileName);
        
        fid = open(filePath,'w');
        
        try:
            self.Print(fid);
        finally:
            fid.close();
            
    def getName(self):
        return self.stnName;

class AprSigmaCollection():
    
    def __init__(self,file):
        
        self.aprSigmaDict = dict();
        
        fid = open(file,'r');
        
        for line in fid:
            lineParts = re.split('\s+',line.strip());
            
            if len(lineParts) != 6:
                continue;
            
            stnName = lineParts[0].lower();
            
            self.aprSigmaDict[stnName] = AprSigmaObj(line)
#            if not self.aprSigmaDict.has_key(stnName):
#                self.aprSigmaDict[stnName] = AprSigmaObj(line);
#            else:
#                raise AprSigmaParseException('Duplicate station: '+stnName+' found in sittbl!!');
#            
    def getAprSigma(self,stnName):
        
        if self.contains(stnName):
            return self.aprSigmaDict[stnName.lower()];
        else:
            return AprSigmaObj().initWithValues(stnName, 30.0, 30.0, 30.0);

    def contains(self,stnName):
        return self.aprSigmaDict.has_key(stnName.lower());
    
    def setName(self,oldName,newName):
        
        oldName = oldName.lower();
        newName = newName.lower();
        
        if self.contains(oldName):
            
            # make copy of old name under new name
            self.aprSigmaDict[newName] = self.aprSigmaDict[oldName];
            
            # apply the new name settings
            self.aprSigmaDict[newName].setName(newName);
            
            # delete the old name object
            del self.aprSigmaDict[oldName];
        else:
            raise AprSigmaParseException('Station: '+oldName\
                                         +' does not exist in AprSigmaCollection object!!!');
            
    
class StnMetadataObj():
    
    def __init__(self):
        
        
        self.stnInfoObj = None;
        self.aprObj = None;
        self.aprSigmaObj = None;
        
    def initFromFilePaths(self,stnInfoPath, aprPath,  aprSigmaPath = None):
        
        if not os.path.isfile(stnInfoPath):
            raise StnMetadataException('station.info file not found: '+stnInfoPath ); 
        
        # this guy is a must
        self.stnInfoObj = StnInfoObj(stnInfoPath);
        
        # check that the station info object is properly initialized
        # for instance it could be empty etc etc
        if self.stnInfoObj.getName() == None:
            raise StnMetadataException('station.info '+stnInfoPath+' not properly initialized' ); 

        # notice here that if no apr file is found then just use
        # an empty apr.  must initiaize without apr
        if os.path.isfile(aprPath):
            self.aprObj = AprObj(aprPath);
        else:
            # use empty apr object
            self.aprObj = AprObj();
            
            # set the name to same as stnInfo 
            self.aprObj.stnName = self.stnInfoObj.getName();
            self.aprObj.oriName = self.stnInfoObj.getName();
               
        # might have apr constraints file but might not
        #  3 different situations:
        #    1. no apr file path given , that is, the apr constraint file dne
        #    2. the path given for the apr constrain file  dose not exist
        #    3. the apr object was not initialized and so constraints should be ignored 
        if aprSigmaPath == None \
            or not os.path.isfile(aprSigmaPath) \
                or not self.aprObj.isValid :
            self.aprSigmaObj   = AprSigmaObj();
            self.aprSigmaObj.stnName = self.stnInfoObj.getName();
            self.aprSigmaObj.oriName = self.stnInfoObj.getName();
            
        else:
            self.aprSigmaObj   = AprSigmaObj(aprSigmaPath);
        
        # make sure that the files refer to the same station
        #print self.stnInfoObj.getName();
        #print self.aprObj.getName();
        if self.stnInfoObj.getName() != self.aprObj.getName():
            raise StnMetadataException('station name: '+self.stnInfoObj.getName()\
                                            +' in station.info does not match station name: '+self.aprObj.getName()\
                                                +' in apr file!!');
        
        if aprSigmaPath == None:
            # manually set the apr sigmas name
            self.aprSigmaObj.setName(self.stnInfoObj.getName());
        else:
            # make sure that the name of the apr constraints file matches apr file
            if self.aprSigmaObj.getName() != self.aprObj.getName():
                raise StnMetadataException('station name in apr.sigma file does not match station name in apr file!!');
        
        return self;
    
    def initFromObjects(self,stnInfoObj,aprObj,aprSigmaObj):
        
        # make sure all the godamn name match ...
        if stnInfoObj.getName() == aprObj.getName()\
             and aprObj.getName() == aprSigmaObj.getName():
            self.stnInfoObj = stnInfoObj;
            self.aprObj     = aprObj;
            self.aprSigmaObj= aprSigmaObj;
            return self;
            
        else:
            print stnInfoObj.getName();
            print aprObj.getName();
            print aprSigmaObj.getName();
            print stnInfoObj.getName() == aprObj.getName();
            
            raise StnMetadataException('names do not match!!!');
            return None;
                
    def export(self, path):
        self.stnInfoObj.export(path);
        self.aprObj.export(path);
        self.aprSigma.export(path);
        
    def Print(self,fid = None):
        
        self.stnInfoObj.Print(fid);
        self.aprObj.Print(fid);
        self.aprSigmaObj.Print(fid);
        
    def printObjectStreams(self,stnInfoFid,aprFid,aprSigmaFid):
        self.stnInfoObj.Print(stnInfoFid);
        self.aprObj.Print(aprFid);
        self.aprSigmaObj.Print(aprSigmaFid);
        
    def setName(self,newName):
        
        if len(newName) != 4:
            raise StnMetadataException('New name must be 4 char!');
        
        newName = newName.lower();
        self.stnInfoObj.setName(newName);
        self.aprObj.setName(newName);
        self.aprSigmaObj.setName(newName);
        
    def getName(self):
        return self.stnInfoObj.getName();
        
        
class StnMetadataMgr():

    def __init__(self,stnIdentifier,date=None,dns=None):
        
        self.dns = dns;
        
        if date !=None:
            try:
                (self.year,self.doy) = date.split('::'); 
            except:
                raise StnMetadataException('Invalid date format!');
                
            self.year = archexpl.get_norm_year_str(self.year);
            self.doy  = archexpl.get_norm_doy_str(self.doy);
        else:
            self.year = None;
            self.doy  = None;
        
        
        self.stnMetadataObj      = None;
        
        self.aprPath             = None;
        self.aprInitPath         = None;
        self.aprSigmaPath        = None;
        self.aprSigmaInitPath    = None;
        self.stnInfoPath         = None;
        self.stnName             = None;
        self.oriName             = None;
        self.nameSpace           = None;
        
        self.defaultAprPath      = None;
        self.defaultAprSigmaPath = None;
        
        # keep track of original station identifier
        self.stnId = stnIdentifier;
        
        # parse the name space and the station name
        (self.nameSpace,self.stnName) = stnIdentifier.split('::');
        
        # make sure to save the original name so that can always revert back for exports
        self.oriName = self.stnName;
        
        # make sure to format them ...
        self.stnName   = self.stnName.lower();
        self.nameSpace = self.nameSpace.lower();
        
        # figure out where archive explorer would/does put this station
        #rnxPath = archexpl.rnxPath;
        #path = os.path.join(rnxPath,self.nameSpace);
        #self.stnRoot = os.path.join(path,self.stnName);
        self.stnRoot = archexpl.build_stn_path(self.nameSpace,self.stnName);
        
        # construct the default paths (no name space here)
        self.defaultAprPath      = os.path.join(self.stnRoot,self.stnName+'.apr');
        self.defaultAprSigmaPath = os.path.join(self.stnRoot,self.stnName+'.apr.sigma');
        
        self.aprInitPath      = os.path.join(self.stnRoot,self.stnName+'.apr');
        self.aprSigmaInitPath = os.path.join(self.stnRoot,self.stnName+'.apr.sigma');
        
        self.aprPath          = os.path.join(self.stnRoot,self.stnName+'.apr');
        self.aprSigmaPath     = os.path.join(self.stnRoot,self.stnName+'.apr.sigma');
                
        # compute the station info path
        self.stnInfoPath = os.path.join(self.stnRoot,self.stnName+'.station.info');
        
        # construct output path
        if self.year != None and self.doy !=None:
            
            # try to get year and day apr files if given year and doy
            path              = archexpl.build_rnx_path(self.nameSpace, self.stnName, self.year, self.doy);
            
            # where we will export the metadata to if they do not exist already
            self.aprPath      = os.path.join(path,self.stnName+'.apr');
            self.aprSigmaPath = os.path.join(path,self.stnName+'.apr.sigma');
            
        # now add domain name space
        if self.dns != None:
            
            self.aprPath          = self.aprPath          + '.' + self.dns;
            self.aprSigmaPath     = self.aprSigmaPath     + '.' + self.dns;
        
        
        
        # OK, have 4 possible situations for constructing input path
        #  1. stn/year/doy/stn.apr.ns
        #  2. stn/year/doy/stn.apr
        #  3. stn/stn.apr.ns
        #  4. stn/stn.apr
        
        # look for input in reverse order
        
        # 4. stn/stn.apr
        if os.path.isfile(os.path.join(self.stnRoot,self.stnName+'.apr')):
            self.aprInitPath      = os.path.join(self.stnRoot,self.stnName+'.apr');
            self.aprSigmaInitPath = os.path.join(self.stnRoot,self.stnName+'.apr.sigma');
        
        # 3. stn/stn.apr.ns
        if self.dns != None and os.path.isfile(os.path.join(self.stnRoot,self.stnName+'.apr'+'.'+self.dns)):
            self.aprInitPath      = os.path.join(self.stnRoot,self.stnName+'.apr'+'.'+self.dns);
            self.aprSigmaInitPath = os.path.join(self.stnRoot,self.stnName+'.apr.sigma'+'.'+self.dns);
        
        if self.year != None and self.doy != None:
            
            # path = stn/year/doy/
            path  = archexpl.build_rnx_path(self.nameSpace, self.stnName, self.year, self.doy);
            
            # 2 stn/year/doy/stn.apr
            if os.path.isfile(os.path.join(path,self.stnName+'.apr')):
                self.aprInitPath      = os.path.join(path,self.stnName+'.apr');
                self.aprSigmaInitPath = os.path.join(path,self.stnName+'.apr.sigma');
                
            # 1 stn/year/doy/stn.apr.ns
            if self.dns != None and os.path.isfile(os.path.join(path,self.stnName+'.apr'+'.'+self.dns)):
                self.aprInitPath      = os.path.join(path,self.stnName+'.apr'+'.'+self.dns);
                self.aprSigmaInitPath = os.path.join(path,self.stnName+'.apr.sigma'+'.'+self.dns);            
        
        #os.sys.stdout.write("initAprPath: "     +self.aprInitPath         +"\n");    
        #os.sys.stdout.write("aprPath:     "     +self.aprPath             +"\n");
        
        #os.sys.stdout.write("initAprSigmaPath: "+self.aprSigmaInitPath    +"\n");    
        #os.sys.stdout.write("aprSigmaPath:     "+self.aprSigmaPath        +"\n");
        
        

    def initFromArchive(self):
        
        # this is when loading the objects from the archive for gamit run
        #
        #  stnMetadataMgr('igs::algo').initFromArchive();
        #
        
#        if os.path.isfile(self.stnInfoPath)  \
#            and os.path.isfile(self.aprPath) \
#                and os.path.isfile(self.aprSigmaPath):
            
        # initialize the object ... finally
        #if os.path.isfile(self.aprInitPath):
        self.stnMetadataObj = StnMetadataObj().initFromFilePaths(self.stnInfoPath,  \
                                                                 self.aprInitPath,  \
                                                                 self.aprSigmaInitPath); 
#        else: 
#            # yell about missing files to the user
#            raise StnMetadataException("Missing initialzation files for StnMetadataMgr object!");
        
        return self;
        
    def initFromObjects(self,stnInfoObj,aprObj,aprSigmaObj):
        
        # initialize using the objects given.  
        # notice that [export] paths might not exist at this point
        # so do not want to check them ...
        # might be discritizing the jumbo station.info etc. 
        # 
        # So basically you wanted this obj 
        # to generate the export paths for you 
        self.stnMetadataObj = StnMetadataObj().initFromObjects(stnInfoObj,\
                                                               aprObj,    \
                                                               aprSigmaObj);
        
        return self;
        
    def setName(self, newName):
        self.stnMetadataObj.setName(newName);
        self.stnName = newName;
        
    def getName(self):
        return self.stnMetadataObj.getName();
    
    def Print(self,fid = None):
        self.stnMetadataObj.Print(fid);
        
    def printObjectStreams(self,stnInfoFid,aprFid,aprSigmaFid):
        self.stnMetadataObj.printObjectStreams(stnInfoFid,aprFid,aprSigmaFid);
        
    def export(self):
        
        shouldRestoreName = False;
        savedName  = '';
#        
#        print self.stnName
#        print self.getName()
#        print self.oriName;
        
        if self.stnName != self.oriName:
            shouldRestoreName = True;
            savedName = self.stnName;
            self.setName(self.oriName);

        # export the files to wherever they were originally loaded
        self.stnMetadataObj.stnInfoObj.export(self.stnInfoPath);
        
        if os.path.isdir(os.path.split(self.aprPath)[0]):
#            print "Exporting APR to: "+self.aprPath;
            self.stnMetadataObj.aprObj.export(self.aprPath);
        
        # not sure if this is the right thing to do here
        # the benefit is that other days processing in save vacinity could
        # boot strap off what should be close updated coord.
#        if self.aprPath != self.aprInitPath:
#            
#            if os.path.isdir(os.path.split(self.aprInitPath)[0]):
#                # update initialization path also
##                print "Exporting APR to: "+self.aprInitPath;
#                self.stnMetadataObj.aprObj.export(self.aprInitPath);
            
        # only export sigma if we have valid apr 
        if self.stnMetadataObj.aprObj.isValid and \
                os.path.isdir(os.path.split(self.aprSigmaPath)[0]):
            self.stnMetadataObj.aprSigmaObj.export(self.aprSigmaPath);
        
#        # should we do this?
#        if self.stnMetadataObj.aprObj.isValid and \
#                self.aprSigmaPath != self.aprSigmaInitPath:
#            
#            if os.path.isdir(os.path.split(self.aprSigmaInitPath)[0]):
#                # update initialization path also
#                self.stnMetadataObj.aprSigmaObj.export(self.aprSigmaInitPath)
        
        if shouldRestoreName:
            self.setName(savedName);
            
    def getStnId(self):
        return self.stnId;
       
    def isValidForDate(self,year,doy):
        
        isValid = False; 
        
        # make python date object
        targetDate = convertDate(year,doy);
        
        # loop over lines of the station info and check for inclusion
        for line in self.stnMetadataObj.stnInfoObj.stnInfoLineList:
            if targetDate >= line.startDate \
                    and targetDate <= line.stopDate:
                isValid = True;
                break;
            
        return isValid;
                 
         
class StnMetadataCollection():
    
    def __init__(self,stnNameRegistry = None, dns=None):
        
        # iterator protocol
        self.iterIndx = 0;
        self.iterList = None;
        
        # collection objs
        self.stnMetadataMgrDict = dict();

        # and so it begins ...
        if stnNameRegistry == None:
            #self.stnNameRegistry = StnNameRegistry();
            self.stnNameRegistry = None;
        else:
            self.stnNameRegistry = stnNameRegistry;
            
        self.dns = dns;
            
    def initFromStnList(self,stnList, date=None):
        
        # initialize the stn name registry first for name conflict resolution
        if self.stnNameRegistry == None:
            self.stnNameRegistry = StnNameRegistry().initWithStnList(stnList);
        
        for stnId in stnList:
            
            #print "ori stn id: "+stnId
            
            stnId = stnId.strip();
            
            try:
                # break into id parts
                (nameSpace,stnName) = stnId.split('::');
            except:
                
                os.sys.stderr.write("STATION METADATA COLLECTION: station id "+stnId+" is not valid format\n");
                
                # fuck it ...
                continue;
            
            if nameSpace == 'pub':
                initStnId = 'igs::'+stnName;
            else:
                initStnId = stnId;
            
            # gather up the metadata from around the archive
            #metadataObj = StnMetadataMgr(initStnId,date).initFromArchive();
            try:
                metadataObj = StnMetadataMgr(initStnId,date,self.dns).initFromArchive();
            except Exception,e :
                print 'Error initializing station: '+ stnId;
                print e;
                sys.exc_info();
                continue;

            # apply any station renaming from name registry
            metadataObj.setName(self.stnNameRegistry.resolve(stnId));
            
            if not self.stnMetadataMgrDict.has_key(stnId):
                #rint 'adding station: ' + stnId;
                #print stnId
                self.stnMetadataMgrDict[stnId] = metadataObj;
        
        return self;
    
    # iterator protocol
    def __iter__(self):
        return self
    
    # iterator protocol
    def next(self):
        
        if self.iterList ==None:
            self.iterList = self.stnMetadataMgrDict.keys();
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            key = self.iterList[self.iterIndx];
            obj = self.stnMetadataMgrDict[key];
            self.iterIndx += 1;
            return obj
        
    def get(self,key):
        
        # must resolve key to forward mapping key
        stnId = key;
        if not self.stnNameRegistry.isForwardMappingKey(key):
            
            # have reverse mapping key so resolve it
            stnId = self.stnNameRegistry.resolve(key);
            
        #print stnId
#        print self.stnMetadataMgrDict.has_key(stnId)
        if stnId != None and self.stnMetadataMgrDict.has_key(stnId):
            return self.stnMetadataMgrDict[stnId];
        else:
            # this should never happen!  this means that registry is stale/out of sync with collection!!
            raise StnMetadataException(key+' is not defined in metadata collection!!');
  
    def exists(self,key):
        return self.stnNameRegistry.contains(key);
    
    def contains(self,key):
        return self.exists(key);
  
    def put(self,key,stnMetadataMgrObj):
        
        if not isinstance(stnMetadataMgrObj,StnMetadataMgr):
            raise StnMetadataException('Can only assign StnMetadataMgr objects to StnMetadataCollections');
        
        # must resolve key to forward mapping key
        stnId = key;
        if not self.stnNameRegistry.isForwardMappingKey(key):
            
            # have reverse mapping key so resolve it
            stnId = self.stnNameRegistry.resolve(key);
            
        if stnId != None and self.stnMetadataMgrDict.has_key(stnId):
            self.stnMetadataMgrDict[stnId] = stnMetadataMgrObj;
        else:
            # this should never happen!  this means that registry is stale/out of sync with collection!!
            raise StnMetadataException(key+' is not defined in metadata collection!!');
    
    def size(self):
        #return self.stnNameRegistry.size();
        return len(self.stnMetadataMgrDict.keys());
        
        
class StnNameRegistry(): 
    
    def __init__(self):
        
        # iterator protocol
        self.iterIndx = 0;
        self.iterList = None;
        
        # store original entries
        # use set to ensure unique entries
        self.stnIdSet      = set();
        
        # unique mapping for stations and namespaces
        self.stnDict        = dict();
        
        # forward and reverse name lookups
        self.fowardNameMap  = dict();
        self.reverseNameMap = dict();
        
        # for now to keep copy of the conflicted stations
        self.conflictSet = set();
        
    def getRandom4Chars(self):
        
        r = '';
        for i in range(0,4):
            r += random.choice(string.ascii_lowercase);
        
        r = r[0:3]+'_';
        return r;
        
    def initWithStnList(self,stnList):
        
        self.conflictSet = set();
        
        # priorizitize by key
        priorityKey = 'pub:'
        pubList = list();
        for stnId in stnList[:]:
            if stnId.startswith(priorityKey):
                pubList.append(stnId);
                stnList.remove(stnId);
        
        # put back together with public stations at the front
        # this is to prioritize public stations so they do not get 
        # renamed since can not control how the downloader will download
        # into rinex dir
        stnList = pubList + stnList;
        
        for stnId in stnList:
            
            stnId = stnId.strip();
            
            # check this shit folks!
            if stnId in self.stnIdSet:
                raise StnRegistryException('Station identity: '+stnId +' already defined in registry!');
            
            # save original listing
            self.stnIdSet.add(stnId);
            
            # parse the id into namespace and name
            try:
                (nameSpace,stnName) = stnId.strip().split('::');
            except:
                raise StnRegistryException('Entry: '+stnId+' has invalid station list format!');
            
            if self.stnDict.has_key(stnName):
                # name conflict resolution folks
                # we can't deal with this here
                # b/c we have to wait until we have seen all 
                # the other names so that we can generate unique 
                # new name for sure, otherwise could just cause needless aditional 
                # name conflicts
                self.conflictSet.add(stnId);
                
            else:
                self.stnDict[stnName] = nameSpace;
                
                # should we do this here for stn names that do not conflict?
                # simplifies logic downstream since don't have to care once map is mad
                # just used forward name map in code and reverse for export???
                #  we'll see
                self.setNameMapping(stnId, stnName);                        
                
        for stnId in self.conflictSet:
            
            # generate a new station name/alias
            # if the name already exists in the stnDict
            # choose another one and so on ...
            newStnName = self.getRandom4Chars();
            while(self.stnDict.has_key(newStnName)):
                newStnName = self.getRandom4Chars();
            
            # set the mapping using new station name    
            self.setNameMapping(stnId, newStnName); 
            
        return self;
    
    def size(self):
        return len(self.stnIdSet);
    
    def setNameMapping(self, stnId, stnName):
        
        # check it and check it again ...
        if self.fowardNameMap.has_key(stnId):
            raise StnRegistryException('Entry: '+stnId+' is already defined in forwardNameMap!');
        
        if self.reverseNameMap.has_key(stnName):
            raise StnRegistryException('Entry: '+stnName+' is already defined in reverseNameMap!');
            
        # do it ...
        self.fowardNameMap[stnId] = stnName
        self.reverseNameMap[stnName] = stnId;
        
    def resolve(self, key):
        
        # self symetric
        if key == None:
            return None
        
        shouldLookForAltKey = False
        if key.startswith('pub:'):
            (nameSpace,stnName) = key.split('::');
            altKey = 'igs::'+stnName;
            shouldLookForAltKey = True;
        
        if key.startswith('igs:'):
            (nameSpace,stnName) = key.split('::');
            altKey = 'pub::'+stnName;
            shouldLookForAltKey = True
        
        if self.fowardNameMap.has_key(key):
            return self.fowardNameMap[key];
        elif self.reverseNameMap.has_key(key):
            return self.reverseNameMap[key];
        elif shouldLookForAltKey and self.fowardNameMap.has_key(altKey):
            return self.fowardNameMap[altKey];
        elif shouldLookForAltKey and self.reverseNameMap.has_key(altKey):
            return self.reverseNameMap[altKey];
        else:
            return None;
    
    def contains(self,key):
        
        if self.resolve(key)!=None:
            return True;
        else:
            return False;
    
    def isForwardMappingKey(self,key):
        
        if not self.contains(key):
            raise StnRegistryException('Could not resolve '+key);
        
        return self.fowardNameMap.has_key(key)
    
    def isReverseMappingKey(self,key):
        if not self.contains(key):
            raise StnRegistryException('Could not resolve '+key);
        
        return self.reverseNameMap.has_key(key);
        
    def getForwardMappingKey(self,key):
        
        if not self.contains(key):
            raise StnRegistryException('Could not resolve '+key);
        
        if self.isForwardMappingKey(key):
            return key;
        else:
            return self.resolve(key);    
    
    def getReverseMappingKey(self,key):
        
        if not self.contains(key):
            raise StnRegistryException('Could not resolve '+key);
        
        if self.isReverseMappingKey(key):
            return key;
        else:
            return self.resolve(key);
    
    def updateNameMapping(self,forwardKey,stnName):
        
        # a little trickier than might first appear
        if not self.contains(forwardKey) :
            raise StnRegistryException('Could not resolve '+forwardKey);
        
        # if pub::algo is not a forwardkey then resolve it forward to algo
        # then resolve it back again to igs::algo and visa versa
        if not self.isForwardMappingKey(forwardKey):
            if self.isForwardMappingKey(self.resolve(self.resolve(forwardKey))):
                forwardKey = self.resolve(self.resolve(forwardKey));
            else:
                raise StnRegistryException('Registry does not contain mapping for '+forwardKey);
            
        # first things first make sure that stnName does not resolve!
        # if the updated stn anem resolves then some other stationID already 
        # points to this alias.  
        if self.resolve(stnName) !=None:
            raise StnRegistryException('alias: '+stnName+' already in use!');
        
        #
        # For example f[igs::algo] --> skox AND r[skox] --> igs::algo
        #
        # You could change f[igs::algo] --> qooj 
        #
        #            BUT NOT r[skox] --> chi::algo
        # 
        # Thus if update forward mapping f[igs::algo] --> qooj, then 
        # need to update reverse map
        #
        #    1. delete r[skox] mapping
        #    2. assign r[qooj] --> igs::algo
        #
        if not self.isForwardMappingKey(forwardKey):
            raise StnRegistryException('Can not update reverse mapping key!');
        
        # delete whatever the forward key points at
        del self.reverseNameMap[self.resolve(forwardKey)];
        
        # set new/updated reverse map for forwardKey
        self.reverseNameMap[stnName] = forwardKey;
        
        # update the forward mapping for forwardKey
        self.fowardNameMap[forwardKey] = stnName;

    # iterator protocol
    
    def __iter__(self):
        return self
    
    # iterator protocol
    
    def next(self):
        
        if self.iterList ==None:
            self.iterList = list(self.stnIdSet);
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            key = self.iterList[self.iterIndx];
            self.iterIndx += 1;
            return key

    def merge(self,registry):
        
        # the idea here is to combine two stationNameRegistries into one
        #
        #   since the registries are usually tied to some underlying data
        #   if there is a forward or reverse conflict here we must abort
        #
        
        # make sure that the input is actually another StnNameRegistry
        if not isinstance(registry,StnNameRegistry):
            raise StnRegistryException('input is not of type stnInfoLib.StnNameRegistry');
        
        # get forward name mappings
        fKeys1 = set(    self.fowardNameMap.keys());
        fKeys2 = set(registry.fowardNameMap.keys());
        
        # get the reverse name mappings
        rKeys1 = set(    self.reverseNameMap.keys());
        rKeys2 = set(registry.reverseNameMap.keys());
                
        # for each common forward key make sure they point to same value
        for key in set.intersection( fKeys1, fKeys2 ):
            
            # get both forward mappings 
            f1 =     self.fowardNameMap[key];
            f2 = registry.fowardNameMap[key];
            
            # make sure both forward mappings are equal
            if f1 != f2:
                os.sys.stderr.write('key: '+f1+', '+f2);
                raise StnRegistryException('must resolve name conflicts before merge');
        
        # for each common reverse key make sure they point to same value    
        for key in set.intersection( rKeys1, rKeys2 ):
            
            # get both reverse mappings
            r1 =     self.reverseNameMap[key];
            r2 = registry.reverseNameMap[key];
            
            # check that both reverse mappings are equal
            if r1 != r2:
                os.sys.stderr.write(key+': '+r1+', '+r2);
                raise StnRegistryException('must resolve name conflicts before merge');        
            
        # OK, now bring on each of missing forward maps from registry
        for key in set.difference( fKeys2, fKeys1 ):
            self.fowardNameMap[key] = registry.fowardNameMap[key];
            
        # now, ingest all the missing reverse name maps from registry
        for key in set.difference( rKeys2, rKeys1 ):
            self.reverseNameMap[key] = registry.reverseNameMap[key];
            
        # finally, update stnIdset
        self.stnIdSet = set.union(self.stnIdSet,registry.stnIdSet);
                

if __name__ == "__main__":
    print "FUCK GAMIT"
    
#    line2 = ' 2353  Wairakei          1990 337 00 00 00  1991 332 00 00 00   1.4077  DHPAB   0.0000   0.0000  TRIMBLE 4000SST       4.11                   4.11  --------------------  TRM14532.00      -----  --------------------'
#    line1 = ' 2353  Wairakei          1991 332 00 00 00  9999 999 00 00 00   1.4130  DHPAB   0.0000   0.0000  TRIMBLE 4000SST       4.53                   4.53  --------------------  TRM14532.00      -----  --------------------'
#    
#    line1 = ' 7ODM  Seven Oaks Dam    2005 052 00 00 00  2005 052 20 00 00   0.0083  DHPAB   0.0000   0.0000  ASHTECH Z-XII3        CD00                   9.20  LP02909               ASH701945B_M     SCIT   CR519991856         '
#    line2 = ' 7ODM  Seven Oaks Dam    2005 052 20 00 00  9999 999 00 00 00   0.0083  DHPAB   0.0000   0.0000  ASHTECH Z-XII3        CD00                   9.20  LP02909               ASH701945B_M     SCIT   CR519991856         '
#    
#    sil1 = StnInfoLine(line1);
#    sil2 = StnInfoLine(line2);
#    
#    sil1.setName('FUCK');
#    sil2.setName('FUCK');
#    print sil1.overlapsByDate(sil2);
#    print sil2.overlapsByDate(sil1);

#    StnInfoObj(open('../ykro.station.info','r').readlines());

#    print sil.stnName
#    print sil.rx.type, sil.rx.vers
#    print sil.ant.type, sil.ant.dome,sil.ant.sn, sil.ant.ht, sil.ant.htCod, sil.ant.n, sil.ant.e;
#    
#    print sil1.rx.isValid(), sil1.ant.isValid(); 
#    
#    if sil.isValid():
#        print sil.stnName, "is valid entry with "+str(sil.numDays)+" days of data"
#    else:
#        print sil.stnName, "entry not valid"
#        
#    apr = AprCollection('../itrf.apr');
#    print apr.contains('ZIMM')
#    print apr.size();
#    
#    apr.setName('ZIMM', 'FUCK');
#    print apr.contains('FUCK')
#    print apr.contains('ZIMM')
#    
#    #apr.getApr('FUCK').Print();
#    
#    for stn in apr:
#        stn.Print();

#    
#    for stn in stnInfo:
#        stn.export('../stnInfoFiles');        
#    aprSigmas = AprSigmaObj('../auck.apr.sigma');
#    aprSigmas.Print();
#    aprSigmas.setSigmasTo30cm().Print();
#    aprSigmas.export('../')
    
#    AprSigmaObj().initWithValues('yass', 0.04, 0.73, 0.348).Print();
    
#    stn = 'AUCK';
#    StnInfoCollection('../station.info').getStnInfo(stn).export('../');
#    AprCollection('../itrf.apr').getApr(stn).export('../')
#    AprSigmaObj().initWithValues(stn, 0.05, 0.05, 0.05).export('../');
#    
#    smo = StnMetadataObj('../auck.station.info','../auck.apr','../auck.apr.sigma');
#    smo.Print()
#    smo.export('../')

#    smm = StnMetadataMgr('igs::auck','2003::103').initFromArchive();
#    smm.setName('fuck')
#    smm.Print();
#    smm.export();
    
#    file = '/media/fugu/processing/projects/osuGLOBAL/gamit/orbit/networks/stn_list.1999.330';
#    fid = open(file,'r');
#    stnList = fid.readlines();
#    fid.close();
#    reg = StnNameRegistry().initWithStnList(stnList);
#    metadata = StnMetadataCollection(reg).initFromStnList(stnList);
#    s = set();
#    i = 0;
#    stnInfoFid = open('../junk.stn.info','w');
#    aprFid     = open('../junk.apr','w');
#    aprSigmaFid= open('../junk.apr.sigma','w');
#    
#    for stn in metadata:
#        stn.printObjectStreams(stnInfoFid,aprFid,aprSigmaFid);
#    stnInfoFid.close();
#    aprFid.close();
#    aprSigmaFid.close();


#    file = '../stn_list.2010.171';
#    fid = open(file,'r');
#    stnList = fid.readlines();
#    fid.close();
#    SNR = StnNameRegistry().initWithStnList(stnList);
##    for stn in SNR.conflictSet:
##        print stn;
##        print SNR.resolve(stn)
##        print SNR.resolve(SNR.resolve(stn))
#    
#    # test updating name mapping
#    stnId = 'igs::lamp';
#    aliasOri = SNR.resolve(stnId);
#    print stnId +" resolves to "+SNR.resolve(stnId);
#    SNR.updateNameMapping( stnId,SNR.getRandom4Chars())
#    print stnId +" resolves to "+SNR.resolve(stnId);
#    print SNR.resolve(stnId) +" resolves to "+SNR.resolve(SNR.resolve(stnId))
#    print aliasOri + " resolves to",SNR.resolve(aliasOri)
#    
#
    file = '../stnList';
    fid = open(file,'r');
    stnList = fid.readlines();
    fid.close();

    reg = StnNameRegistry().initWithStnList(stnList);
    for stnId in reg:
        print stnId,'-->', reg.resolve(stnId);
    print "gre::algo resolves to "+ reg.resolve('gre::algo');
    metadata = StnMetadataCollection(reg).initFromStnList(stnList);
    
    for stn in metadata:
        stn.Print();
#        
#    metadata.get(reg.resolve('gre::algo')).stnMetadataObj.aprSigmaObj.setSigmasTo30cm();  
#    metadata.get('gre::algo').export();
        
        
        
