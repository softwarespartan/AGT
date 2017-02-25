#!/usr/bin/python

import os,sys;
from glob import glob
import gps_file_types
import gps_file_ops
import file_ops;
import shutil


# final raw and rinex data paths
RNX_PATH = "/media/fugu/data/gps/rinex/"
RAW_PATH = "/media/fugu/data/gps/raw/"

# cross platform junk
rnxPath = os.path.normpath(os.path.normcase(RNX_PATH))
rawPath = os.path.normpath(os.path.normcase(RAW_PATH))

def get_norm_year_str(year):
    
    # mk 4 digit year
    year = int(year);
    if year >= 80 and year <= 99:
        year += 1900
    elif year >= 0 and year < 80:
        year += 2000        
    return str(year)

def get_norm_doy_str(doy):
    doy  = str(doy)    
    # mk 3 diit doy
    if len(doy) == 1:
        doy = "00"+doy
    elif len(doy) == 2:
        doy = "0"+doy
    return doy

def get_dirs(path_list):
    
    # list init
    del_list = []
    
    # get list of all no dirs
    for path in path_list:
        if not os.path.isdir(path):
            del_list.append(path)
            
    # delete non directory paths        
    for path in del_list:
        path_list.remove(path)
        
    # return edited list of only dirs    
    return path_list

def rm_dirs(path_list):
    
    # list init
    del_list = []
    
    # get list of all no dirs
    for path in path_list:
        if os.path.isdir(path):
            del_list.append(path)
            
    # delete non directory paths        
    for path in del_list:
        path_list.remove(path)
        
    # return edited list of only dirs    
    return path_list

def get_country_list(dir=rnxPath):
    
    # look in path for 3 char directories
    path= os.path.join(dir,'[a-z][a-z][a-z]')    
    country_list = glob(path);
    
    # return the list
    return get_dirs(country_list)

def get_station_list(country_path):
    
    # look for 4-char station directories
    path = os.path.join(country_path,'[a-z0-9][a-z0-9][a-z0-9][a-z0-9]')
    stn_list = glob(path)
            
    # return the station list        
    return get_dirs(stn_list)

def get_station_path(country_list,stn_key):
    
    func= "get_stn_country_path(): "
    
    if len(stn_key) != 4:
        print "ERROR: "+func+"Station name must be 4 characters!!!"
        return ""
    
    # list init
    station_path_list = [];
    
    # get all the country paths
    for country in country_list:
        
        # get station list for each country
        for station_path in get_station_list(country):
            
            # get dir of station
            (dir,station) = os.path.split(station_path)
            
            # check station is stn_key
            if station == stn_key:
                station_path_list.append(station_path)
            
    return station_path_list

def get_rinex_station_path(stn_key):
    
    country_list = get_country_list(rnxPath);
    station_path = get_station_path(country_list,stn_key)
    
    return station_path

def get_raw_station_path(stn_key):
    
    country_list = get_country_list(rawPath);
    station_path = get_station_path(country_list,stn_key)
    
    return station_path

def filter_station_path(country_key, station_path_list):
    
    del_list = []
    country_key = "/"+country_key+"/"
    for station_path in station_path_list:
        if station_path.find(country_key) < 0:
            del_list.append(station_path)

    for station_path in del_list:
        station_path_list.remove(station_path)
        
    return station_path_list  

def existsInArchive(country_key,stn_key):
    
    if len(get_unique_rinex_station_path(country_key,stn_key)) == 1:
        return True;
    else:
        return False;

def get_unique_rinex_station_path(country_key,stn_key):
    
    station_path = get_rinex_station_path(stn_key);
    return filter_station_path(country_key,station_path)

def get_unique_raw_station_path(country_key,stn_key):
    
    station_path = get_raw_station_path(stn_key);
    return filter_station_path(country_key,station_path)

def isunique(station_path_list):
    
    # if a station has more than one path
    # then obviously it's not unique.
    if len(station_path_list) == 1:
        return True
    else:
        return False
    
def exists(station_path_list):
    # if station has at least one entry
    if len(station_path_list) >0:
        return True
    else:
        return False      

def get_year_list(station_path_list):
    
    # list init
    year_path_list = [];
    
    # for each station path
    for station_path in station_path_list:
        
        # get years for each station
        path = os.path.join(station_path,'[1-2][0-9][0-9][0-9]')
        
        # append each paths to list   
        for year_path in glob(path):
            year_path_list.append(year_path)
    
    # that's it ...                     
    return get_dirs(year_path_list)

def get_day_list(station_year_list):
    
    path = os.path.join(station_year_list,'[0-9][0-9][0-9]')
    doy_path_list = glob(path)
    
    doy_path_list = get_dirs(doy_path_list)
    
    if len(doy_path_list) == 0:
        path = os.path.join(station_year_list,'[1-2][0-9][0-9][0-9]_[0-9][0-9][0-9]')
        doy_path_list = glob(path)
        doy_path_list = get_dirs(doy_path_list)
    
    return doy_path_list
    
    
def get_rinex_file_list(stn_key):
    
    rnx_file_list = []
    
    station_path = get_rinex_station_path(stn_key)
        
    for year_path in get_year_list(station_path):
        
        for doy_path in get_day_list(year_path):
            
            rnx_file_list += gps_file_types.get_rinex_file_list(doy_path)
            
    return rnx_file_list        
                
def get_raw_file_list(stn_key):
    
    raw_file_list = []
    
    station_path = get_raw_station_path(stn_key)
        
    for year_path in get_year_list(station_path):
        
        for doy_path in get_day_list(year_path):
            
            raw_file_list += gps_file_types.get_raw_file_list(doy_path)
            
    return raw_file_list

def get_unique_rinex_file_list(country_key,stn_key):
    
    rnx_file_list = []
    
    station_path = get_unique_rinex_station_path(country_key,stn_key)
        
    for year_path in get_year_list(station_path):
        
        for doy_path in get_day_list(year_path):
            
            rnx_file_list += gps_file_types.get_rinex_file_list(doy_path)
            
    return rnx_file_list        
                
def get_unique_raw_file_list(country_key,stn_key):
    
    raw_file_list = []
    
    station_path = get_raw_station_path(stn_key)
        
    for year_path in get_year_list(station_path):
        
        for doy_path in get_day_list(year_path):
            
            raw_file_list += gps_file_types.get_raw_file_list(doy_path)
            
    return raw_file_list

def get_rinex_file(country,stn,year,doy):
        
    year = get_norm_year_str(year)
    doy  = get_norm_doy_str(doy)
    
    rnx_file_path = os.path.join(RNX_PATH,country)
    rnx_file_path = os.path.join(rnx_file_path,stn)
    rnx_file_path = os.path.join(rnx_file_path,year)
    rnx_file_path = os.path.join(rnx_file_path,doy)
    
    rnx_file_path = gps_file_types.get_rinex_file_list(rnx_file_path)
    
    # if there is more than 1 rnx file found
    # just return the first in the list
    if len(rnx_file_path) >= 1:
        return rnx_file_path[0]
    else:
        return None
    
def get_raw_file(country,stn,year,doy):
        
    year = get_norm_year_str(year)
    doy  = get_norm_doy_str(doy)
    
    raw_file_path = os.path.join(RAW_PATH,country)
    raw_file_path = os.path.join(raw_file_path,stn)
    raw_file_path = os.path.join(raw_file_path,year)
    raw_file_path = os.path.join(raw_file_path,doy)
    
    raw_file_path = gps_file_types.get_raw_file_list(raw_file_path);
    
    if len(raw_file_path) == 1: 
        return raw_file_path[0]
    else:
        return 
       
       
def get_rinex_start_date(country_code,stn_key):
    
    station_path = get_unique_rinex_station_path(country_code,stn_key)
    
    yearList = [];
    minYear = 2099;
    minYearPath = None;
    minDoy = 366;
       
    # look for min year    
    for year_path in get_year_list(station_path):
        (path,year) = os.path.split(year_path);
        year = int(year)
        if year < minYear:
            minYear = year;
            minYearPath = year_path;
        
    # look for min doy in min year        
    for day_path in get_day_list(minYearPath):
        (path,doy) = os.path.split(day_path);
        doy = int(doy);
        if doy < minDoy:
            minDoy=doy;
            
            
    return (minYear,minDoy)  

def get_rinex_stop_date(country_code,stn_key):
    
    station_path = get_unique_rinex_station_path(country_code,stn_key)
    
    yearList = [];
    maxYear = 1900;
    maxYearPath = None;
    maxDoy = None;
       
    # look for min year    
    for year_path in get_year_list(station_path):
        (path,year) = os.path.split(year_path);
        year = int(year)
        
        if year > maxYear and len(get_day_list(year_path)) > 0:
            maxYear = year;
            maxYearPath = year_path;
        
    # look for min doy in min year        
    for day_path in get_day_list(maxYearPath):
        (path,doy) = os.path.split(day_path);
        doy = int(doy);
        if doy > maxDoy:
            maxDoy=doy;
            
            
    return (maxYear,maxDoy) 

def stationDoesExist(countryCode,stationName):
    
    if len(get_unique_rinex_station_path(countryCode,stationName)) == 1:
        return True;
    else:
        return False;
    
def initStation(countryCode,stationName): 
    
    if len(countryCode) != 3:
        sys.stderr.write("Error: countryCode must be exactly 3 characters!\n");
        raise;
    
    if len(stationName) !=4:
        sys.stderr.write("stationName must be exactly 4 characters!\n");
        raise
    
    path = os.path.join(rnxPath,countryCode);
    path = os.path.join(path,stationName);
    
    if os.path.isdir(path):
        sys.stderr.write("station path: "+path+" already exists!\n");
        raise;
    else:
        try:
            os.makedirs(path,0775);
        except Exception, e:
            print e;
            raise;
   
def exists_rnx_for_stn_on_date(nameSpace,stnName,year,doy):
    
    rnx_path = build_rnx_path(nameSpace,stnName,year,doy);
    
    rnx_file_list = gps_file_types.get_rinex_file_list(rnx_path);
    
    if len(rnx_file_list) > 0:
        return True;
    else:
        return False;
        
def build_stn_path(nameSpace,stnName):

    rnx_path = os.path.join(RNX_PATH,nameSpace);
    rnx_path = os.path.join(rnx_path,stnName);
    
    return rnx_path+os.path.sep;    
    
def build_dynamic_stn_path(nameSpace,stnName):
   
    # here need to send out structure of archive for things like down loader
    # not it's important to do this here since could change the archive structure
    # to say, putting all the rnx files in rnxRoot/nameSpace/stnName/
    # or upgrading to dynamic name space such as chi::sag/stnName etc etc
    # would need only edit this function 
    stn_root = build_stn_path(nameSpace, stnName);
    dynamic_rnx_path = os.path.join(stn_root,'yyyy/doy/');
    
    return dynamic_rnx_path;

#def getRinexFileStructureAsRegex(nameSpace,stnName):
#    
#    stn_root = build_stn_path(nameSpace, stnName);
#    structure = os.path.join(nameSpace,stnName);
#    structure = os.path.join(structure,'[0-9][0-9][0-9][0-9]');
#    structure = os.path.join(structure,'[0-9][0-9][0-9]');
#    return os.path.join(stn_root,structure);
#
#def getRinexFileStructureAsSymbols(nameSpace,stnName):
#    
#    stn_root = build_stn_path(nameSpace, stnName);
#    return os.path.join(stn_root,os.path.join('yyyy','ddd'));

#def getAllStnBasePaths():
#    
#    return 
    
    
def build_rnx_path(nameSpace,stnName,year,doy,fileName = None):
    
    rnx_path = build_stn_path(nameSpace,stnName);
    
    # normalize the date info
    year = get_norm_year_str(year);
    doy  = get_norm_doy_str(doy);

    rnx_path = os.path.join(rnx_path,year);
    rnx_path = os.path.join(rnx_path,doy);
    
    if fileName != None:
        rnx_path = os.path.join(rnx_path,fileName);
    else:
        rnx_path += os.path.sep;
    
    return rnx_path;
    
def build_rnx_path_from_file_name(nameSpace,rnx_file):
    
    # strip off any path components
    rnx_file = os.path.basename(rnx_file);
    
    stnName = rnx_file[0:4];
    doy     = rnx_file[4:7];
    year    = get_norm_year_str(rnx_file[9:11]);
    
    rnx_path = build_rnx_path(nameSpace,stnName,year,doy,rnx_file);
    
    return rnx_path;
    
    
def archive_rnx_file(nameSpace,src):
    
    # remove any compression, now have o-file
    src = file_ops.inflate(src);
    
    # next, compress the src ... now have d.Z file
    gps_file_ops.rnx2crz(src);
    
    # fit with new suffix 09o --> 09d.Z
    src = src[:-1]+'d.Z'
    
    # compute the destination
    dest = build_rnx_path_from_file_name(nameSpace, src);
    
    # do not overwrite existing data no matter what
    if os.path.isfile(dest):
        return;
        
    # finally, do the copy
    parent, rnx_file = os.path.split(dest);
    
    if not os.path.isdir(parent):
        os.makedirs(parent, 0775);
    
    # do the damn thing already ...
    shutil.copy(src, dest);
    
def yearDoyFromRnxPath(path):
    
    (path,rnxFile)  = os.path.split(path);
    (path,doy) = os.path.split(path);
    (path,year) = os.path.split(path);
    
    return (year,doy);
    
def main():
    print stationDoesExist('chi','amun');
    
    print build_rnx_path('igs','algo',2008,298)
    print build_rnx_path_from_file_name('igs','algo2980.08d.Z'); 
    
    archive_rnx_file('igs','/Users/abel/Desktop/alrt0700.09o');
    
if __name__ == '__main__':
    
    main()   
    
    
#for country in get_country_list():
#    for station in get_station_list(country):
#        print station
#
#country_list = get_country_list();
#for station_path in get_station_path(country_list,"rogm"):
#    print station_path

#country_list = get_country_list();
#station_path = get_station_path(country_list,"cfag")
#    
#year_path_list = get_station_years(station_path)
#for year_path in year_path_list:
#    print year_path

#station_path = get_raw_station_path("cfag")
#for year_path in get_station_years(station_path):
#    
#    for doy_path in get_station_days(year_path):
#        
#        for file_path in get_raw_file_list(doy_path):

#country_list = get_country_list()
#for path in get_station_list(country_list):
#    print path
    
#for file in get_rinex_file_list("sio3"):
#    print file, os.path.getsize(file)/(1024),"K"
    
#print get_rinex_file("arg","alar",2008,34)
#print get_raw_file("arg","fuck",2008,34)

