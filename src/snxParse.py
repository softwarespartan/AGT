#!/usr/bin/python

import file_ops
import os
import re
from glob import glob
import Utils


class StationData:
    
    def __init__(self,x=None,y=None,z=None):
        
        self.X = x;
        self.Y = y;
        self.Z = z;
        
        self.sigX = None;
        self.sigY = None;
        self.sigZ = None;
        
        self.velX = None;
        self.velY = None
        self.velZ = None;
        
        self.sigVelX = None;
        self.sigVelY = None;
        self.sigVelZ = None;
        
        self.refEpoch = None;
        
        self.domesNumber = None;
        
    def Print(self):
        if self.X != None:
            print '%13.4f %13.4f %13.4f ' % (self.X, self.Y, self.Z),
            
        if self.sigX != None:
            print '%2.10f %2.10f %2.10f\n' % (self.sigX, self.sigY, self.sigZ), 
        else:
            print
            
    def __repr__(self):
        
        string = "";
        
        if self.X != None:
            string+='%13.4f %13.4f %13.4f ' % (self.X, self.Y, self.Z);
            
        if self.sigX != None:
            string += '%10.8f %10.8f %10.8f ' % (self.sigX, self.sigY, self.sigZ); 
            
        if self.velX != None:
            string += '%8.5f %8.5f %8.5f ' % (self.velX, self.velY, self.velZ); 
            
        if self.sigVelX != None:
            string += '%10.8f %10.8f %10.8f ' % (self.sigVelX, self.sigVelY, self.sigVelZ);
            
        if self.refEpoch != None:
            string += '%11.6f' % (self.refEpoch);
        
        return string;
    
    def __str__(self):
        
        string = "";
        
        if self.X != None:
            string+='%13.4f %13.4f %13.4f ' % (self.X, self.Y, self.Z);
            
        if self.sigX != None:
            string += '%2.10f %2.10f %2.10f ' % (self.sigX, self.sigY, self.sigZ); 
            
        if self.velX != None:
            string += '%8.5f %8.5f %8.5f ' % (self.velX, self.velY, self.velZ); 
            
        if self.sigVelX != None:
            string += '%10.8f %10.8f %10.8f ' % (self.sigVelX, self.sigVelY, self.sigVelZ);
            
        if self.refEpoch != None:
            string += '%11.6f' % (self.refEpoch);
        
        return string;
            
            
class mergedSinexStationData():
    
    # Decorator Pattern to avoid subclassing ...
    
    def __init__(self,snxStnData = None):
        self.snxStnData = snxStnData
        self.orgNameSet     = set()
        
    def Print(self):
        
        # don't want to print the sigmaXYZ
        if self.snxStnData.X !=None:
            print '%13.4f %13.4f %13.4f ' % (self.snxStnData.X, self.snxStnData.Y, self.snxStnData.Z),
        
        # print additional org info also
        if len(self.orgNameSet)>0:
            for orgName in self.orgNameSet:
                print orgName, 
            print
        else:
            print      

class snxFileParser:
    
    def __init__(self,snxFilePath = None):
        
        self.snxFilePath = snxFilePath
        self.snxFileName = os.path.basename(snxFilePath)
        self.stationDict = dict();
        self.orgName     = None; 
        self.varianceFactor = 1;
        
        # iter protocol shit
        self.iterIndx = 0;
        self.iterList = None;    
        
    def parse(self):
        
        foundSolutionEstimate = False
        inSolutionEstimateSection = False
        isHeaderLine = False;
        
        foundSiteId     = False;
        inSiteIdSection = False;
        
        # if there's a file to parse
        if self.snxFilePath != None:
            
            # flag to rezip at end
            wasZipped     = False
            wasCompressed = False
            
            # check for gzip
            if self.snxFilePath[-2:] == "gz":
                file_ops.gunzip(self.snxFilePath)
                self.snxFilePath = self.snxFilePath[0:-3]
                wasZipped = True
            
            # check for unix compression
            elif self.snxFilePath[-1:] == "Z":
                file_ops.uncompress(self.snxFilePath)
                self.snxFilePath = self.snxFilePath[0:-2]
                wasCompressed = True
                
            # open the file
            try:
                snxFileHandle = open(self.snxFilePath,'r')
            except:
                print "snxFileParser ERROR:  Could not open file " + self.snxFilePath + " !!!" 
                raise
            
            #make pattern to match to snx organization ...
            self.snxFileName = os.path.basename(self.snxFilePath)
            
            orgPattern   = re.compile('^([a-zA-Z]+).*\.f?snx$')
            orgMatch     = orgPattern.findall(self.snxFileName)
            self.orgName = orgMatch[0].upper()

            # make pattern to look for SiteId start tag
            siteIdStartPattern = re.compile('^\+SITE\/ID$');
            
            # make pattern to look for end of siteId section
            siteIdEndPattern   = re.compile('^\-SITE\/ID$');
            
            # make pattern to parse the siteId lines
            # Example:
            #
            #     TROM  A 82397M001 P , USA                   18 56 18.0  69 39 45.9   135.4
            #
            siteIdPattern      = re.compile('^\s+(\w+)\s+\w\s+(\w+).*$');
            
            # variance factor patther
            # Example:
            #
            # VARIANCE FACTOR                    0.048618461936712
            #
            #
            varianceFactorPattern = re.compile('^ VARIANCE FACTOR\s+([\d+]?\.\d+)$');
            
            # Make pattern to look for solution estimate start tag
            startSolutionEstimatePattern = re.compile('^\+SOLUTION/ESTIMATE.*');
            
            # make pattern to look for solution estimate end tag
            endSolutionEstimatePattern = re.compile('^\-SOLUTION\/ESTIMATE.*');
            
            # make pattern to look for station coordinates
            # Example:
            #
            #   1 STAX   ALGO  A ---- 05:180:43200 m    2 .91812936331043008E+6 .2511266E-2
            #
            stationCoordinatePattern = re.compile('^\s+\d+\s+STA(\w)\s+(\w+)\s+(\w).*\d+\s+(-?[\d+]?\.\d+[Ee][+-]?\d+)\s+(-?[\d+]?\.\d+[Ee][+-]?\d+)$')
            
            # make pattern to look for station velocities
            # Example:
            #
            # 916 VELX   YAKA  A    1 00:001:00000 m/y  2 -.219615010076079E-01 0.13728E-03
            #
            stationVelocityPattern = re.compile('^\s+\d+\s+VEL(\w)\s+(\w+)\s+\w\s+....\s+(\d\d:\d\d\d).*\d+\s+(-?[\d+]?\.\d+[Ee][+-]?\d+)\s+(-?[\d+]?\.\d+[Ee][+-]?\d+)$')
                        
            for line in snxFileHandle:
                
                varianceFactorMatch = varianceFactorPattern.findall(line);
                
                siteIdStartMatch = siteIdStartPattern.findall(line);
                siteIdEndMatch   = siteIdEndPattern.findall(line);
                
                startSolutionEstimateMatch = startSolutionEstimatePattern.findall(line);
                endSolutionEstimateMatch   = endSolutionEstimatePattern.findall(line);
                
                if siteIdStartMatch:
                    inSiteIdSection = True;
                    continue;
                
                if siteIdEndMatch:
                    inSiteIdSection = False;
                    continue;
                
                # check for solution estimate section
                if startSolutionEstimateMatch:
                    inSolutionEstimateSection = True
                    continue
                    
                elif endSolutionEstimateMatch:
                    inSolutionEstimateSection = False
                    break
                
                if varianceFactorMatch:
                    self.varianceFactor = float(varianceFactorMatch[0]);                    
                
                if inSiteIdSection:
                    
                    # parse the siteID line
                    siteIdMatch = siteIdPattern.findall(line);
                    
                    # blab about it
                    #print siteIdMatch;
                    
                    # if the line does not contain a match then move along
                    if not siteIdMatch:
                        continue;
                    
                    # extract the parsed info
                    (stationName, domesNumber) = siteIdMatch[0];
                    
                    # make sure the name is upper case
                    stationName = stationName.upper();
                    
                    # initialize station data if not seen this station before
                    if not stationName in self.stationDict.keys():
                            self.stationDict[stationName] = StationData();
                            
                    self.stationDict[stationName].domesNumber = domesNumber;
                    
                    #print "set domes number "+ domesNumber +" for station "+stationName;
                        
                
                # if in the solution estimate section
                if inSolutionEstimateSection:
                    
                    # check for station coordinate match
                    stationCoordinateMatch = stationCoordinatePattern.findall(line);
                    
                    # check for station velocity match
                    stationVelocityMatch = stationVelocityPattern.findall(line);
                    
                    
                    #print line
                    #print stationCoordinateMatch
                                        
                    # if match then store result                    
                    if stationCoordinateMatch:
                        (             \
                         coordID,     \
                         stationName, \
                         pointCode,   \
                         coord,       \
                         sigCoord     \
                         ) = stationCoordinateMatch[0]
                        
                        if pointCode != 'A': 
                            os.sys.stderr.write('ignoring solution/estimate STA'+coordID \
                                                +' for station: '+stationName            \
                                                +', point code = '+pointCode             \
                                                +', file = '+ self.snxFileName           \
                                                +'\n'                                    \
                            );
                            continue
                         
                        # make sure station name is upper case 
                        stationName = stationName.upper();
                        
                        if not stationName in self.stationDict.keys():
                            self.stationDict[stationName] = StationData()
                            
                        if coordID == 'X':
                            self.stationDict[stationName].X    = float(coord)
                            self.stationDict[stationName].sigX = float(sigCoord)
                            
                        elif coordID == 'Y':
                            self.stationDict[stationName].Y    = float(coord)
                            self.stationDict[stationName].sigY = float(sigCoord)
                            
                        else:
                            self.stationDict[stationName].Z    = float(coord)
                            self.stationDict[stationName].sigZ = float(sigCoord)
                            
                    if stationVelocityMatch:
                        
                        (             \
                         coordID,     \
                         stationName, \
                         refEpoch,    \
                         vel,         \
                         sigVel       \
                        ) = stationVelocityMatch[0];
                                                 
                        stationName = stationName.upper();
                        
                        # parse refEpoch String
                        (year,doy) = refEpoch.split(':');
                        
                        # convert from string
                        doy = float(doy);
                        
                        # normalize the year and convert to float
                        year = float(Utils.get_norm_year_str(year));
                                        
                        #compute fractional year to match matlab round off
                        fractionalYear = year+((doy-1)/366.0)+ 0.001413;
                        
                        # init if not already in dict
                        if not stationName in self.stationDict.keys():
                            self.stationDict[stationName] = StationData()
                            
                        # set the reference epoch for the velocity    
                        self.stationDict[stationName].refEpoch    =  fractionalYear;
                            
                        if coordID == 'X':
                            self.stationDict[stationName].velX    = float(vel)
                            self.stationDict[stationName].sigVelX = float(sigVel)
                            
                        elif coordID == 'Y':
                            self.stationDict[stationName].velY    = float(vel)
                            self.stationDict[stationName].sigVelY = float(sigVel)
                            
                        else:
                            self.stationDict[stationName].velZ    = float(vel)
                            self.stationDict[stationName].sigVelZ = float(sigVel)
        
        # regzip the file is was .gz
        if wasZipped:
            file_ops.gzip(self.snxFilePath)
            
        # recompress the file if was .Z    
        if wasCompressed:
            file_ops.compress(self.snxFilePath)
                            
        return self
                            
    def Print(self,key=None,fid=None):
        
        if key != None and self.contains(key):
            print key,self.orgName,
            self.stationDict[key].Print();
        
        # loop through each station print info
        for stationName in self.stationDict.keys():                
            print stationName,self.orgName,
            self.stationDict[stationName].Print();
            
    def size(self):
        return len(self.stationDict);
    
    def __iter__(self):
        self.iterList = list(self.stationDict.keys());
        return self
    
    # iterator protocol
    def next(self):
        
        #if self.iterList ==None:
        #    self.iterList = list(self.stnIdSet);
        
        if self.iterIndx > len(self.iterList)-1:
            
            # reset iteration parameters
            self.iterList = None;
            self.iterIndx = 0;
            
            # halt iteration
            raise StopIteration;
        else:
            key = self.iterList[self.iterIndx];
            self.iterIndx += 1;
            return key;
        
    def contains(self,key):
        return self.stationDict.has_key(key.upper());
        
    def get(self,key):
        if self.contains(key):
            return self.stationDict[key.upper()];
        else:
            return None;

class snxStationMerger:
    
    def __init__(self):
        self.snxObjectList     = list()
        self.mergedStationDict = dict()
        self.orgList           = set()
        self.maxMetersApart    = 1
        
        # init the stationDict iwht level one stations
        # level one holds all stations that appear only once
        self.mergedStationDict['1'] = dict()
        
    def compareUsingCoordinates(self,snxStationDataA, snxStationDataB):
        
        diffX = snxStationDataB.X - snxStationDataA.X
        diffY = snxStationDataB.Y - snxStationDataA.Y
        diffZ = snxStationDataB.Z - snxStationDataA.Z
        
        radialDistanceApart = (diffX**2 + diffY**2 + diffZ**2)**(0.5)
        
        if radialDistanceApart <= self.maxMetersApart:
            return True
        else:
            #print 'station with same name found but different coords!!!  Radial Distance Apart:',radialDistanceApart
            return False
        
    def stationExistsWithNumberOfOccurrences(self,stationName,numberOfOccurences):
        
        # first make sure numberOfOccurences is an integer at least zero
        try:
            numberOfOccurrences = int(numberOfOccurences)
        except:
            print 'number of occurrences is not an integer!!!'
            raise
        
        if numberOfOccurrences < 0:
            print 'number of occurrences must be at least zero!!'
            raise
        
        # finally, convert to string for merged station dictionary key
        numberOfOccurrences = str(numberOfOccurrences)
        
        # empty station dictionary case
        if len(self.mergedStationDict.keys()) == 0:
            return False
        
        # check that numberOfOccurances even is in dictionary
        if not numberOfOccurrences in self.mergedStationDict.keys():
            return False
        
        elif not stationName in self.mergedStationDict[numberOfOccurrences]:
            return False
        
        else: 
            return True
        
    def maxLevel(self):
                
        return int(sorted(list(self.mergedStationDict.keys()))[-1])

    def addStation(self, level, orgName, stationName, snxStnData):
        
        # add instance of mergedSinexStationData to mergedStationDict at level
        self.mergedStationDict[level][stationName] = \
            mergedSinexStationData(snxStnData)
            
        # add org data                
        self.mergedStationDict[level][stationName].orgNameSet.add(orgName)
        
                
    def addStationsFromSinexObject(self,snxObj):
        
        stationAdded = False
        
        # add sinex to list
        self.snxObjectList.append(snxObj)
        
        for stationName in snxObj.stationDict.keys():
            
            for level in self.mergedStationDict.keys():
            
                # first check if station is in level one station dictionary
                if not stationName in self.mergedStationDict[level].keys():
                    
                    # add the station to this level since it does not exist
                    self.addStation(level, snxObj.orgName, stationName, snxObj.stationDict[stationName])
                    
                    # update list of all unique orgs associated with station merge
                    self.orgList.add(snxObj.orgName)
                    
                    # note that we added the station here
                    stationAdded = True
                    
                    # no point looking through other levels since we've added it here
                    break
                    
                else:
                    
                    # station with same name should be compared by coordinate(s)
                    if self.compareUsingCoordinates(                                            \
                                                    self.mergedStationDict[level][stationName].snxStnData, \
                                                    snxObj.stationDict[stationName]             \
                                                   ):
                        # update org list for station to reflect the orgs that process this station
                        self.mergedStationDict[level][stationName].orgNameSet.add(snxObj.orgName)
                        
                        # nothing left to do, since they are the same station within 1 meter
                        # Notice here that if false then station check goes to next level
                        stationAdded = True
                        break
                
            # if station not added at any level
            # then need to make new level and add station    
            if not stationAdded:
                
                # get max level + 1
                nextLevel = str(self.maxLevel() + 1)
                
                # init the level/numberOfOccurrences
                self.mergedStationDict[nextLevel] = dict()
                
                # add the station with correct number of unique occurrences
                self.addStation(nextLevel, snxObj.orgName, stationName, snxObj.stationDict[stationName])
        
            # reset station added for next station
            stationAdded = False
            
        return self
            
    def Print(self):
        for level in self.mergedStationDict.keys():
            for stationName in self.mergedStationDict[level].keys():
                print stationName, level, 
                self.mergedStationDict[level][stationName].Print()
    
    

def main():
    
#    esaFile = '../esa13297.snx'
#    emrFile = '../emr13297.snx'
#    gfzFile = '../gfz13297.snx'
#    jplFile = '../jpl13297.snx'
#    ngsFile = '../ngs13297.snx'
#    sioFile = '../sio13293.snx'
#    
#    # init the sinex objects
#    snxParserESA = snxFileParser(esaFile)
#    snxParserEMR = snxFileParser(emrFile)
#    snxParserGFZ = snxFileParser(gfzFile)
#    snxParserJPL = snxFileParser(jplFile)
#    snxParserNGS = snxFileParser(ngsFile)
#    snxParserSIO = snxFileParser(sioFile)
#    

#    
#    # add stations from each sinxe object
#    snxMerge.addStationsFromSinexObject(snxParserESA.parse())
#    snxMerge.addStationsFromSinexObject(snxParserEMR.parse())
#    snxMerge.addStationsFromSinexObject(snxParserGFZ.parse())
#    snxMerge.addStationsFromSinexObject(snxParserJPL.parse())
#    snxMerge.addStationsFromSinexObject(snxParserNGS.parse())
#    snxMerge.addStationsFromSinexObject(snxParserSIO.parse())

    # get list of sinex files 
    #snxFileList = glob('/Users/abel/itrf/itrf2008_trf.snx');
    
    #snxParser = snxFileParser(snxFileList[0]).parse();
    
    #for stn in snxParser:
    #    print 'COORD',stn, snxParser.get(stn); 
    
    # init the sinex station merger
    #snxMerge = snxStationMerger();
    
    # uncomment the following to set
    # the position fileter manually
    #snxMerge.maxMetersApart = 1.1
    
#    for snxFile in snxFileList:
#        os.sys.stdout.write("Processing snx: "+snxFile+"\n");
#        snxMerge.addStationsFromSinexObject(snxFileParser(snxFile).parse())
#
#    # print the data
#    snxMerge.Print()


    file = '/media/fugu/processing/projects/osuGLOBAL/napeos/orbit/solutions/2006/304/o12/o1213992.snx.gz';
    file = '/work/napeos/374.1994.222/solution/o1207613.snx.gz'
    
    sigXYZ = 1.0;
    
    snxParser = snxFileParser(file).parse();
    
    # print the header line
    os.sys.stdout.write('STATION COORDINATES AT EPOCH  2002.0\n');
    
    # organize the coordinates for the data object
    for stn in snxParser:

        # get the snx data from the parser
        stnData = snxParser.get(stn);
        
        #print stn, stnData.domesNumber, stnData.X, stnData.Y, stnData.Z;

        xyzStr =  "%9s %4s %9s     GPS %4s                  %12.3f %12.3f %12.3f %5.3f %5.3f %5.3f OSU" % (stnData.domesNumber, stn, stnData.domesNumber, stn, stnData.X, stnData.Y, stnData.Z, sigXYZ, sigXYZ, sigXYZ)
        velStr =  "%9s %4s %9s         %4s                  %12.3f %12.3f %12.3f %5.3f %5.3f %5.3f OSU" % (stnData.domesNumber, "", "", "", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)    
    
        os.sys.stdout.write(xyzStr+"\n");
        os.sys.stdout.write(velStr+"\n");

    
    
                    
if __name__ == "__main__":
    
    main()
                
                
                