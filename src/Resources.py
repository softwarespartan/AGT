from boto.s3.key        import Key
from boto.s3.connection import S3Connection,OrdinaryCallingFormat

import re,os,pyDate,Utils;

import multiprocessing

WL_SP3_BUCKET = 'com.widelane.sp3'         ;
WL_NAV_BUCKET = 'com.widelane.nav'         ;
WL_RNX_BUCKET = 'rinex'                    ;
WL_STN_BUCKET = 'com.widelane.station.info';
WL_APR_BUCKET = 'com.widelane.apr'         ;
WL_RES_BUCKET = 'com.widelane.resources'   ;
WL_SOLN_BUCKET= 'com.widelane.solutions'   ;

WL_RNX_BUCKET = 'com.widelane.data'
#WL_STN_BUCKET = 'com.widelane.data'
#WL_APR_BUCKET = 'com.widelane.data'

# local dir relative work_dir for resources
WL_RESOURCES_LOCAL  = 'resources'          ;
    
    
class ResourceException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
def get_sp3(year,doy,org,outdir=None):
    
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    # initialize a date object
    date = pyDate.Date(year=year, doy=doy);
    
    # create string version of the gps week
    gps_week_str = str(date.gpsWeek);
    
    # make sure that the string is 5 characters
    if date.gpsWeek < 1000: gps_week_str = '0'+gps_week_str;
    
    # create the file name of the sp3
    sp3_file_name_base = org+gps_week_str+str(date.gpsWeekDay)+'.sp3';
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())   ;
    bucket    = conn.get_bucket(WL_SP3_BUCKET)         ;
    bucketKey = Key(bucket)                            ;                       
   
    file_list = [];
    for f in bucket.list(prefix=sp3_file_name_base) : file_list.append(f.key);
    
    # check if the sp3 file listing was empty
    if len(file_list) == 0: 
        raise ResourceException('sp3 resource: '+sp3_file_name_base+' could not be located');
    
    # make sure no more than a single match occurred
    if len(file_list) > 1:
        raise ResourceException('sp3 resource: '+sp3_file_name_base+' matches multiple files');
    
    # just be explicit about it
    sp3_file_name = file_list[0];
    
    # create the full path to file on local system
    sp3_file_path = os.path.join(outdir,sp3_file_name);
    
    # create the s3 object
    bucketKey.key = sp3_file_name;  
    
    # pull the file
    bucketKey.get_contents_to_filename(sp3_file_path);
    
    # that's all
    return sp3_file_path;
    
def get_nav(year,doy,org,outdir=None):
    
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    # create the file name of the nav
    nav_file_name = org+doy+'0.'+year[2:]+'n.Z';
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # create the sp3 file path
    nav_file_path = os.path.join(outdir,nav_file_name);
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_NAV_BUCKET)     ;
    bucketKey = bucket.get_key(nav_file_name)         ;
    
    if bucketKey is None:
        raise ResourceException('nav resource: '+nav_file_name+' could not be located');
    
    # create the s3 object
    bucketKey.key = nav_file_name;  
    
    # pull the file
    bucketKey.get_contents_to_filename(nav_file_path);
    
    # that's all
    return nav_file_path;
    
def get_rnx(year,doy,stn_list,outdir=None):
    
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    # init
    rnx_file_list = list();

    # init s3 connection to the metadata bucket
    conn = S3Connection(calling_format=OrdinaryCallingFormat());
    bucket = conn.get_bucket(WL_RNX_BUCKET);
    
    for stnId in stn_list:
    
        # parse the station id and extract the 4-char station code
        #(ns,code) = Utils.parse_stnId(stnId);

        # no more namespaces
        code = stnId;

        # create the file name of the sp3
        rnx_file_name = code+doy+'0.'+year[2:]+'d.Z';
        
        # set outdir to current directory if not set
        if outdir is None: outdir = '.';
        
        # create the sp3 file path
        rnx_file_path = os.path.join(outdir,rnx_file_name);
        
        # create key path to file in rnx
        #rnx_key_path = '/'.join([ns,year,doy,rnx_file_name]);
        rnx_key_path = rnx_file_name;

        bucketKey = bucket.get_key(rnx_key_path)       ;
        
        if bucketKey is None:
            # create the file name of the rnx with session 1
            rnx_file_name = code+str(doy)+'1.'+str(year)[2:]+'d.Z';
            
            # create key path to file in s3
            #rnx_key_path = '/'.join([ns,str(year),str(doy),rnx_file_name]);
            rnx_key_path = rnx_file_name;
            
            # check for session 1 file
            bucketKey = bucket.get_key(rnx_key_path);
            
            if bucketKey is None:
                os.sys.stderr.write('rnx resource: '+stnId+' could not be located for '+year+' '+doy+'\n');
                continue;
        
        # create the s3 object
        bucketKey.key = rnx_key_path;  
        
        # pull the file
        bucketKey.get_contents_to_filename(rnx_file_path);
        
        # add the rinex file path to the file list
        rnx_file_list.append(rnx_file_path);
        
    return rnx_file_list;

def action(params):
    params[0].get_contents_to_filename(params[1])

def get_rnx_parallel(year, doy, stn_list, outdir=None):

    year = Utils.get_norm_year_str(year);
    doy = Utils.get_norm_doy_str(doy);

    # init
    rnx_file_list = list();

    # init s3 connection to the metadata bucket
    conn = S3Connection(calling_format=OrdinaryCallingFormat());
    bucket = conn.get_bucket(WL_RNX_BUCKET);

    list_of_bucket_keys = list()

    for stnId in stn_list:

        # parse the station id and extract the 4-char station code
        (ns, code) = Utils.parse_stnId(stnId);

        # create the file name of the sp3
        rnx_file_name = code + doy + '0.' + year[2:] + 'd.Z';

        # set outdir to current directory if not set
        if outdir is None: outdir = '.';

        # create the sp3 file path
        rnx_file_path = os.path.join(outdir, rnx_file_name);

        # create key path to file in rnx
        rnx_key_path = '/'.join([ns, year, doy, rnx_file_name]);

        bucketKey = bucket.get_key(rnx_key_path);

        if bucketKey is None:
            # create the file name of the rnx with session 1
            rnx_file_name = code + str(doy) + '1.' + str(year)[2:] + 'd.Z';

            # create key path to file in s3
            rnx_key_path = '/'.join([ns, str(year), str(doy), rnx_file_name]);

            # check for session 1 file
            bucketKey = bucket.get_key(rnx_key_path);

            if bucketKey is None:
                os.sys.stderr.write('rnx resource: ' + stnId + ' could not be located for ' + year + ' ' + doy + '\n');
                continue;

        # create the s3 object
        bucketKey.key = rnx_key_path;

        # enqueue bucket key for download
        list_of_bucket_keys.append((bucketKey,rnx_file_path));

        # update list of rinex file procesed
        rnx_file_list.append(rnx_file_path);


    poolsz = max(1,min(16,len(rnx_file_list)))
    pool = multiprocessing.Pool(poolsz);
    pool.map(action, list_of_bucket_keys)
    pool.close()
    pool.join()

    # pull the file
    #bucketKey.get_contents_to_filename(rnx_file_path);

    # add the rinex file path to the file list

    return rnx_file_list;
        
def get_stn_info(year,doy,stn_list,outdir=None):
    
    # init
    file_list = list();

    # init s3 connection to the metadata bucket
    conn = S3Connection(calling_format=OrdinaryCallingFormat());
    bucket = conn.get_bucket(WL_STN_BUCKET);

    list_of_bucket_keys = list()
    
    for stnId in stn_list:
    
        # parse the station id and extract the 4-char station code
        (ns,code) = Utils.parse_stnId(stnId);
        
        # set outdir to current directory if not set
        if outdir is None: outdir = '.';
    
        # set the file name for the station info
        stn_info_file_name = '.'.join((ns,code,'station','info'));
        
        # next, create the path for the station info file
        stn_info_file_path = os.path.join(outdir,stn_info_file_name);

        bucketKey = bucket.get_key(stn_info_file_name)    ;
        
        # let the user know that the file does not exist and continue
        if bucketKey is None:
            os.sys.stderr.write('station info resource: '+stnId+' could not be located\n');
            continue;
        
        # create the s3 object
        bucketKey.key = stn_info_file_name;

        # enqueue
        list_of_bucket_keys.append((bucketKey,stn_info_file_path))

        # add to list of files
        file_list.append(stn_info_file_path);

        # pull the file
        bucketKey.get_contents_to_filename(stn_info_file_path);

    poolsz = min(16, len(file_list))
    pool = multiprocessing.Pool(poolsz);
    pool.map(action, list_of_bucket_keys)
    pool.close()
    pool.join()
        
    return file_list;
        
def get_apr(year,doy,dns,outdir=None):
    
    year = Utils.get_norm_year_str(year);
    doy  = Utils.get_norm_doy_str (doy );
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # set the file name for the station info
    apr_file_name = '.'.join((dns,year,doy,'apr'));
    
    # next, create the path for the station info file
    apr_file_path = os.path.join(outdir,apr_file_name);
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_APR_BUCKET)     ;
    bucketKey = bucket.get_key(apr_file_name)         ;
    
    # make sure we're on track here
    if bucketKey is None:
            raise ResourceException('could not locate resource: '+apr_file_name);
    
    # create the s3 object
    bucketKey.key = apr_file_name;  
    
    # pull the file
    bucketKey.get_contents_to_filename(apr_file_path);
    
    # thats a wrap
    return apr_file_path;
        
def get_bin(program,outdir=None):
    
    # make sure program specified is not bogus
    if program is None or program == "":
        raise ResourceException('invalid program name');
    
    # figure out what platform we're on
    pid = Utils.get_platform_id();
    
    # compute the resource id
    rid = Utils.get_resource_delimiter().join((program,pid));
    
    # add the file and compression suffix
    rid = '.'.join((rid,'tar','gz'));
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # compute the full file path
    bin_file_path = os.path.join(outdir,rid);
    
    # init s3 connection to the resources bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_RES_BUCKET)     ;
    bucketKey = bucket.get_key(rid)                   ;
    
    if bucketKey is None:
        raise ResourceException('binary resource: '+rid+' could not be located');
    
    # set the key to download
    bucketKey.key = rid;
    
    # pull the resource
    bucketKey.get_contents_to_filename(bin_file_path);
    
    # all done;
    return bin_file_path;
     
def get_tables(program,outdir=None):
    
    # make sure program specified is not bogus
    if program is None or program == "":
        raise ResourceException('invalid program name');
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # compute the resource id
    rid = Utils.get_resource_delimiter().join((program,'tables'));
    
    # add the file suffix and the compression suffix
    rid  = '.'.join((rid,'tar','gz'));
    
    # compute the full file path for tables resource
    tables_file_path = os.path.join(outdir,rid);
    
    # init s3 connection to the resources bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_RES_BUCKET)     ;
    bucketKey = bucket.get_key(rid)                   ;
    
    if bucketKey is None:
        raise ResourceException('tables resource: '+rid+' could not be located');
    
    # set the key to download
    bucketKey.key = rid;
    
    # pull the resource
    bucketKey.get_contents_to_filename(tables_file_path);
    
    # yup yup
    return tables_file_path

def pushSNX(key_path,file_path):
    
    # parse the name of the file
    file_name = os.path.basename(file_path);
    
    # create the file key path into S3
    file_key_path = "/".join((key_path,file_name));
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SOLN_BUCKET)       ;
    bucketKey = Key(bucket)                           ;
    
    print "pushing snx file",file_path,"-->", file_key_path
    
    # create the s3 object
    bucketKey.key = file_key_path;  bucketKey.set_contents_from_filename(file_path);
      
def pushSP3(file_path):
    
    # parse the name of the file
    file_name = os.path.basename(file_path);
    
    # create the file key path into S3
    file_key_path = file_name;
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SP3_BUCKET)        ;
    bucketKey = Key(bucket)                           ;
    
    # create the s3 object
    bucketKey.key = file_key_path;  bucketKey.set_contents_from_filename(file_path);
    
def pushOUT(key_path,file_path):
    
    # parse the name of the file
    file_name = os.path.basename(file_path);
    
    # create the file key path into S3
    file_key_path = "/".join((key_path,file_name));
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SOLN_BUCKET)    ;
    bucketKey = Key(bucket)                           ;
    
    print "pushing out file",file_path,"-->", file_key_path
    
    # create the s3 object
    bucketKey.key = file_key_path;  bucketKey.set_contents_from_filename(file_path);
    
def get_snx(key_path,outdir=None):
    
    # init list of files copied
    snx_file_list = list();
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # make sure to expand any user symbols
    outdir = os.path.expanduser(outdir);
    
    # initialize pattern to match sinex files 
    # Should we match the second '.'?  
    # will this match 'file.snx'?
    pattern = re.compile('.*\.snx\..*');
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SOLN_BUCKET)       ;
    bucketKey = Key(bucket)                           ;
    
    # ok now get list of snx files at the key path
    file_keys = bucket.list(prefix=key_path);
    
    # copy each file to the outpath with same keypath
    for fk in file_keys:
        
        # make sure it's a sinex file
        if not pattern.match(fk.key): continue;
        
        # fix the file name for unpadded gps week
        file_name = Utils.fix_gps_week(fk.key);
        
        # create file path w.r.t. outdir
        file_path = os.path.join(outdir,file_name);
                
        # try in initialize the output path
        file_root = os.path.split(file_path)[0];
        
        # make the root if it does not exist
        try:
            if not os.path.isdir(file_root): os.makedirs(file_root);
        except Exception as e:
            os.sys.stderr.write(str(e)+'\n');
            continue;
        
        # set the bucket key
        bucketKey.key = fk;
        
        # get the snx resource
        bucketKey.get_contents_to_filename(file_path);
        
        # add the file to the file list
        snx_file_list.append(file_path);
        
    return snx_file_list;

def get_resources(key_path,ext=None,outdir=None):
    
    # init list of files copied
    res_file_list = list();
    
    # set the file extension to everything, if not set
    if ext is None: ext = '*';
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # make sure to expand any user symbols
    outdir = os.path.expanduser(outdir);
    
    # help user out before compile regex to translate literal "."
    ext = ext.replace('.', '\.');
    
    # initialize pattern to match files 
    # Should we match the second '.'?  
    # will this match 'file.snx'?
    pattern = re.compile('.*'+ext);
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SOLN_BUCKET)       ;
    bucketKey = Key(bucket)                           ;
    
    # ok now get list of snx files at the key path
    file_keys = bucket.list(prefix=key_path);
    
    # copy each file to the outpath with same keypath
    for fk in file_keys:
        
        # make sure it's a sinex file
        if not pattern.match(fk.key): continue;
        
        # fix the file name for unpadded gps week
        file_name = Utils.fix_gps_week(fk.key);
        
        # create file path w.r.t. outdir
        file_path = os.path.join(outdir,file_name);
                
        # try in initialize the output path
        file_root = os.path.split(file_path)[0];
        
        # make the root if it does not exist
        try:
            if not os.path.isdir(file_root): os.makedirs(file_root);
        except Exception as e:
            os.sys.stderr.write(str(e)+'\n');
            continue;
        
        # set the bucket key
        bucketKey.key = fk;
        
        # get the snx resource
        bucketKey.get_contents_to_filename(file_path);
        
        # add the file to the file list
        res_file_list.append(file_path);
        
    return res_file_list;

def list_resources(key_path,ext=None,outdir=None):
    
    # init list of files copied
    res_file_list = list();
    
    # set the file extension to everything, if not set
    if ext is None: ext = '*';
    
    # set outdir to current directory if not set
    if outdir is None: outdir = '.';
    
    # make sure to expand any user symbols
    outdir = os.path.expanduser(outdir);
    
    # help user out before compile regex to translate literal "."
    ext = ext.replace('.', '\.');
    
    # initialize pattern to match files 
    # Should we match the second '.'?  
    # will this match 'file.snx'?
    pattern = re.compile('.*'+ext);
    
    # init s3 connection to the metadata bucket
    conn      = S3Connection(calling_format=OrdinaryCallingFormat())  ;
    bucket    = conn.get_bucket(WL_SOLN_BUCKET)       ;
    bucketKey = Key(bucket)                           ;
    
    # ok now get list of snx files at the key path
    file_keys = bucket.list(prefix=key_path);
    
    # copy each file to the outpath with same keypath
    for fk in file_keys:
        
        # make sure it's a sinex file
        if not pattern.match(fk.key): continue;
        
        # fix the file name for unpadded gps week
        file_name = Utils.fix_gps_week(fk.key);
        
        # create file path w.r.t. outdir
        file_path = os.path.join(outdir,file_name);
                
        # try in initialize the output path
#        file_root = os.path.split(file_path)[0];
#        
#        # make the root if it does not exist
#         try:
#             if not os.path.isdir(file_root): os.makedirs(file_root);
#         except Exception as e:
#             os.sys.stderr.write(str(e)+'\n');
#             continue;
#         
#         # set the bucket key
#         bucketKey.key = fk;
#         
#         # get the snx resource
#         bucketKey.get_contents_to_filename(file_path);
#         
#         # add the file to the file list
        res_file_list.append(file_path);
        
    return res_file_list;

def soln_exists(date,expt,org,net='n0'):

    # init s3 connection
    conn = S3Connection(calling_format=OrdinaryCallingFormat());

    # create a bucket object into s3
    bucket = conn.get_bucket(WL_SOLN_BUCKET);

    # construct the relative path to where the file should be
    relPath = date.yyyy()+"/"+date.ddd()+"/"+expt+"/"+org+"/"+net

    # construct the name of the sinex file
    fileName = org+date.wwwwd()+".snx.gz"

    # full file path
    fullFilePath = relPath + "/" + fileName

    # create a file in to the bucket
    key = Key(bucket,fullFilePath)

    return key.exists(),fullFilePath


if __name__ == '__main__':
    
    #files = get_snx('2009/123/odot/g06','~/tmp');
    #for f in files: print f;
    
    #files = list_resources('2009/123/odot/g06/n1','.mat.gz');
    #for f in files: print f;

    date = pyDate.Date(year=2016,doy=101)
    expt = 'glbf'
    org  = 'n08'
    net  = 'n0'

    exists = soln_exists(date,expt,org,net)

    print("file: "+exists[1]+", "+str(exists[0]))