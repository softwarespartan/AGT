
import os;
import re;
import StnInfoLib;
import pyDate;
import pyDomes;

BLQ_HEADER = """$$ Ocean loading displacement
$$
$$ Calculated by GRDTAB via pyOTL
$$
$$ COLUMN ORDER:  M2  S2  N2  K2  K1  O1  P1  Q1  MF  MM SSA
$$
$$ ROW ORDER:
$$ AMPLITUDES (m)
$$   RADIAL
$$   TANGENTL    EW
$$   TANGENTL    NS
$$ PHASES (degrees)
$$   RADIAL
$$   TANGENTL    EW
$$   TANGENTL    NS
$$
$$ Displacement is defined positive in upwards, South and West direction.
$$ The phase lag is relative to Greenwich and lags positive. The
$$ Gutenberg-Bullen Greens function is used. In the ocean tide model the
$$ deficit of tidal water mass has been corrected by subtracting a uniform
$$ layer of water with a certain phase lag globally.
$$
$$ Complete <model name> : No interpolation of ocean model was necessary
$$ <model name>_PP       : Ocean model has been interpolated near the station
$$                         (PP = Post-Processing)
$$
$$ CMC:  NO  (corr.tide centre of mass)
$$
$$ Ocean tide model: FES2004
$$
$$ END HEADER
""";


class pyOTLException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
    
# default values    
OTL_GRID_PATH   = "/processing/local_tables/gamit/otl.grid";
WORK_DIR        = '.';
OTL_OUTPUT_FILE = "otl.blq";
GRDTAB_PATH = "grdtab"
LFILE = "lxyz.apr";
DFILE = 'dtemp0.000';
    
    
class pyOTL:
    
    def __init__(self,**kwargs):
        
        self.otlGridPath    = OTL_GRID_PATH;
        self.workDir        = WORK_DIR;
        self.otlOutputFile  = OTL_OUTPUT_FILE;
        self.metadata       = None;
        self.domesMgr       = pyDomes.Domes();
        self.date           = None;
        self.grdtabPath     = GRDTAB_PATH;
        
        dateIsSet = False;
        
        # parse args
        for key in kwargs:
            
            arg = kwargs[key];
            key = key.lower();
            
            if key in ("otlgridpath","otl_grid_path"):
                self.otlGridPath = os.path.abspath(os.path.expanduser(arg));
                
            elif key in ("workdir","work_dir"):
                self.workDir = os.path.abspath(os.path.expanduser(arg));
                
            elif key in ("otloutputfile","otl_output_file"):
                self.otlOutputFile = os.path.abspath(os.path.expanduser(arg)); 
                
            elif key in ("metadata","metadatacollection"):
                self.metadata = arg;
                
            elif key in ("domesmgr",'domes','pydomes'):
                self.domesMgr = arg;
                
            elif key in ("date","pydate"):
                dateIsSet = True;
                self.date = arg;
                
            elif key in ("grdtabpath","grdtab_path"):
                if os.path.isfile(arg):
                    self.grdtabPath = arg;
                else:
                    raise pyOTLException("path to GRDTAB: "+arg +" does not exist");  
            
            elif key in ("stnlist","stn_list"):
                
                stnNameRegistry = StnInfoLib.StnNameRegistry().initWithStnList(arg);
             
                # get list of station from the registry
                stnList = list(stnNameRegistry.stnIdSet);
                
                # make sure we have a date for the metadata (and grdtab call)
                if not dateIsSet:
                    raise pyOTLException("must provide date to use stnList as input to compute OTL");
                    
                # init metadata
                if dateIsSet:
                    self.metadata = StnInfoLib                  \
                        .StnMetadataCollection() \
                        .initFromStnList(stnList,str(self.date.year)+"::"+str(self.date.doy));
            else:
                os.sys.stderr.write("PYOTL: Unrecognized key-word arg "+key+"\n");
                
        # the final working dir for the run
        self.tempDir = os.path.join(self.workDir,str(os.getpid())+".otl.tmp");
        
    def willComputeOTL(self):
        
        if not os.path.isdir(self.tempDir):
            # try to make the working dir yell if problem
            try:
                #print "PYOTL:  creating temporary working directory: "+self.tempDir;
                os.makedirs(self.tempDir);
            except Exception, e:
                print e;
                raise pyOTLException("Could not make temporary working directory: "+self.tempDir);
        
    def didComputOTL(self):
        
        # clean up the working dir
        try:
            os.system("rm -rf "+ self.tempDir);
        except Exception, e:
            print e;
            raise pyOTLException("Could not remove temporary working directory: "+self.tempDir);
       
    def mkDfile(self, stnList = None):
        
        numStns = 0;
        dfileStnList = "";
        
        dfilePath = os.path.join(self.tempDir,DFILE); 
        dfileFid  = open(dfilePath,'w');
        
        dfileFid.write(" 1\n 1\n");
        dfileFid.write(LFILE+"\n");
        dfileFid.write("\n\n\n");
        
        if stnList == None:
            
            # go through stations one by one in the metadata
            for stn in self.metadata:
                
                # get the name of the station
                stnName = stn.getName();
                
                # write the station to dfile 
                dfileStnList += "x"+stnName+"0.000\n";
                
                numStns = numStns + 1;
        else:
            
            # so instead get stns from stnList
            for stn in stnList:
                
                # make sure there is metadata for the station
                if not self.metadata.exists(stn):
                    continue;
                
                # get metadata for the station
                mdo = self.metadata.get(stn);
                
                # get whatever name the metadata thinks it's using
                # becase igs::algo could map to _cik for example 
                # due to a name conflict
                stnName = mdo.getName();
                
                # add the station to be written to the dfile
                dfileStnList += "x"+stnName+"0.000\n";
                
                # increment the number of stations to be computed
                numStns = numStns + 1;
                
        # finally, complete the rest of the dfile
        dfileFid.write(str(numStns)+"\n");
        dfileFid.write(dfileStnList);
                    
        
    def mkLfile(self,stnList = None):
        
        # open the lfile for the xyz coords
        aprFid = open(os.path.join(self.tempDir,LFILE),'w');
        
        if stnList == None:
        
            for stn in self.metadata:
                
                # get the name of the station
                stnName = stn.getName();
                
                # write apr
                mdo = stn.stnMetadataObj;
                mdo.aprObj.Print(aprFid);
                
        else:
            
            # so instead get stns from stnList
            for stnid in stnList:
                
                # make sure there is metadata for the station
                if not self.metadata.exists(stnid):
                    continue;
                
                # get metadata for the station
                stn = self.metadata.get(stnid);
                
                # get the name of the station
                stnName = stn.getName();
                
                # write apr
                mdo = stn.stnMetadataObj;
                mdo.aprObj.Print(aprFid);
            
        # close the apr file
        aprFid.close();
        
    def exeOTL(self):
        
        startDir = os.curdir;
        
        #../grdtab.bin dtemp0.000 2008 207 1.25  otl.grid 
        os.chdir(self.tempDir);
        
        # make date strings
        yearStr = str(self.date.year);
        doyStr  = str(self.date.doy);
        
        # make link to otl.grid file
        if not os.path.isfile('otl.grid'):
            os.symlink(self.otlGridPath, 'otl.grid');
         
        # make the command to execute
        exeStr = self.grdtabPath +' ' + DFILE +' ' + yearStr + ' ' + doyStr + ' '  '1.25 ' + 'otl.grid' + ' >> grdtab.out'
                                   
        # finally execute the grdtab
        os.system(exeStr);
        
        # restore starting direcotry
        os.chdir(startDir);
        
        # parse the ufile to blq file for NAPEOS
        self.parseU();
    
    def parseU(self):
        
        # make path the the ufile just created by grdtab
        uFile = os.path.join(self.tempDir,'u');
        
        # make sure that the ufile actually exists
        if not os.path.isfile(uFile):
            raise pyOTLException("ufile: "+uFile+" does not exist");
        
        # initialize the output file
        outfid = open(self.otlOutputFile,'a');
        
        # print the header
        # don't write header since we might
        # need to concatonate many ufiles
        #outfid.write(BLQ_HEADER);
        
        # for each line in the ufiles
        for line in open(uFile,'r').readlines():
            
            # clean up the line
            line = line.strip();
            
            if line.startswith("STATION"):
                #print line;
                
                lineParts = re.split("\W+",line);
                stnName   = lineParts[1].lower();
                stnId = stnName
                #stnId     = self.metadata.stnNameRegistry.resolve(stnName);
                #print "PYOTL: stnName ", stnName, "has domes: ",self.domesMgr.containsStnId(stnId);
                #print "PYOTL: stnId   ", stnId, "has domes: ", self.domesMgr.containsStnId(stnId);
                
                if self.domesMgr.containsStnId(stnId):
                    domesNumber = self.domesMgr.domesForStnId(stnId);
                else:
                    stnName,domesNumber = self.domesMgr.addStn(stnId);
                    
                # construct the entry header
                
                outfid.write("$$\n")
                entryHeader = "  %-9s      %4s\n" % (domesNumber[0:5],stnName.upper())
                outfid.write(entryHeader);
                #outfid.write("$$  M2     S2     N2     K2     K1     O1     P1     Q1     Mf     Mm     Ssa\n")
                
                # initialize the data row index
                indx = 1;
                
            # see if we're at a data line    
            if line.startswith("OCEANLOD") and not line.startswith("OCEANLOD MODEL"):
                
                data = list();
                
                # break up the line into parts
                lineParts = re.split("\s+",line);
                
                # remove the row header
                lineParts.remove("OCEANLOD");
                
                # convert the data to numbers
                data = map(float,lineParts);
                                
                # need to convert the first 3 lines to meters
                if indx <= 3:
                    # update data indexs
                    indx += 1;
                    
                    # convert to meters
                    data = [d/1000 for d in data[:]];
                    
                    # convert to strings for shitty format print
                    data = map(str,data);
                    
                    # remove e-5 and e-6 exponential format
                    for i in range(0,len(data)):
                        if data[i].endswith("e-05"):
                            data[i] = "0.0000"+data[i][0];
                        elif data[i].endswith("e-06"):
                            data[i] = "0.00000"+data[i][0];
                    
                    # ok, now window each number to remove leading zero
                    data = [d[1:7] for d in data[:]];
                    
                    # finally, zero pad any number thats too short
                    for i in range(0,len(data)):
                        if len(data[i])<6:
                            data[i] = data[i]+"0"*(6-len(data[i]));
                        
                    # make format string                    
                    fmtStr = "  "+"%6s "*11+"\n";
                else:
                    # lol, the easy case here
                    fmtStr = "  "+"%6.1f "*11+"\n";
                    
                # finally, write the string to the output file
                outfid.write(fmtStr % tuple(data));
                
        #outfid.write("$$ENDTABLE\n");
        #outfid.write("$$ENDTABLE\n");
        outfid.close();
                        
    def computeOTL(self,**kwargs):
        
        # initialize station list
        stnList = [];
        for stn in self.metadata:
            stnList.append(stn.getName());
        
        for key in kwargs:
            
            arg = kwargs[key];
            key = key.lower();
            
            if key in ("stnlist","stn_list"):
                stnList = arg;
        
        # prepare to compute OTL        
        self.willComputeOTL();
        
        # compute OTL
        for stn in stnList:
            self.mkDfile([stn]);
            self.mkLfile([stn]);
            self.exeOTL();
        
        # clean up
        #self.didComputOTL()
                
def main():
    
    #stnList      = ['igs::algo','igs::thu3','igs::alrt','igs::yell','igs::p213','igs::zimm','igs::palm','igs::vesl'];
    stnList      = open('/Users/abelbrown/Documents/workspace/pyNapeos/data/pyOTL/stn_list.test').readlines();
    date         = pyDate.Date(year=2009,doy=207);
    pathToGrdtab = "/media/fugu/processing/src/gamit_OSX/gamit/bin/grdtab";
    pathToGrdtab = "/Users/abelbrown/Documents/workspace/pyNapeos/data/pyOTL/grdtab.bin";
    
    pyotl        = pyOTL(work_dir="~/Documents/workspace/pyNapeos/data/pyOTL",        \
                         otl_output_file="~/Documents/workspace/pyNapeos/data/pyOTL/otl.blq", \
                         stn_list=stnList,                 \
                         date=date,                        \
                         grdtab_path=pathToGrdtab);
    
    pyotl.computeOTL(stnList = ['igs::algo','igs::thu3','igs::alrt']);
                    
if __name__ == '__main__':
    
    main() 
                    
                    