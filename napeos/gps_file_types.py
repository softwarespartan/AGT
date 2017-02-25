
import os
from glob import glob

def get_zip_file_list(dir=os.getcwd()):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*.zip')    
    zip_file_list = glob(path);
    
    return zip_file_list

def get_obs_file_list(dir=os.getcwd()):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*.[0-9][0-9]o')    
    obs_file_list = glob(path);
    
    return obs_file_list

def get_odotzip_file_list(dir=os.getcwd()):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*o.zip')    
    odotzip_file_list = glob(path);
    
    return odotzip_file_list
    

def get_odotZ_file_list(dir=os.getcwd()):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*o.Z')    
    odotZ_file_list = glob(path);
    
    return odotZ_file_list

def get_nav_file_list(dir=os.getcwd(),type='*'):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,type+'[0-9][0-9][0-9][0-9].[0-9][0-9]n.Z')
    
    nav_file_list = glob(path);
        
    return nav_file_list

def get_sp3_file_list(dir=os.getcwd(),type='*'):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,type+'[0-9][0-9][0-9][0-9][0-9].sp3.Z')
    
    sp3_file_list = glob(path);
    
    if len(sp3_file_list) == 0:
        
        path = os.path.join(dir,type+'[0-9][0-9][0-9][0-9][0-9].sp3.gz')
        
        sp3_file_list = glob(path)
        
    if len(sp3_file_list) == 0:
        
        path = os.path.join(dir,type+'[0-9][0-9][0-9][0-9][0-9].sp3')
        
        sp3_file_list = glob(path)
    
    return sp3_file_list

def get_d_file_list(dir=os.getcwd()):
        
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*.[0-9][0-9]d')
    
    d_file_list = glob(path);
    
    return d_file_list

def get_ddotZ_file_list(dir):

    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'*.[0-9][0-9]d.Z')
    ddotZ_file_list = glob(path);
    
    return ddotZ_file_list

def get_R_file_list(dir):
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    path = os.path.join(dir,'R*.[0-9][0-9][0-9]')
    R_file_list = glob(path)
    
    return R_file_list

def get_T00_file_list(dir):
    
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    path = os.path.join(dir,'*.T00')
    T00_file_list = glob(path)
    
    return T00_file_list

def get_T02_file_list(dir):

    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)

    path = os.path.join(dir,'*.T02')
    T02_file_list = glob(path)

    return T02_file_list

def get_TPS_file_list(dir):
    
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    path = os.path.join(dir,'*.TPS')
    TPS_file_list = glob(path)
    
    return TPS_file_list

def get_raw_file_list(dir):
    
    raw_file_list = []   
    raw_file_list += get_R_file_list(dir)
    raw_file_list += get_T00_file_list(dir)
    raw_file_list += get_TPS_file_list(dir)
    
    return raw_file_list

def get_rinex_file_list(dir):
    
    rnx_file_list = []
    rnx_file_list += get_ddotZ_file_list(dir)
    rnx_file_list += get_odotZ_file_list(dir)
    rnx_file_list += get_obs_file_list(dir)
    rnx_file_list += get_odotzip_file_list(dir)
    
    return rnx_file_list

def get_h_file_list(dir=os.getcwd(),type="*"):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    path= os.path.join(dir,'h'+type+'a.[0-9][0-9][0-9][0-9][0-9]*')    
    h_file_list = glob(path);
    
    #HYYDDD_MIT.GLX
    path= os.path.join(dir,'H[0-9][0-9][0-9][0-9][0-9]_'+type+'.*')    
    h_file_list += glob(path);
    
    return h_file_list


def get_g_file_list(dir=os.getcwd(),type="*"):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    final_path= os.path.join(dir,"g"+type+"[0-9].[0-9][0-9][0-9].Z")    
    g_file_list = glob(final_path);
    
    if len(g_file_list) == 0:
        gzip_path = os.path.join(dir,"g"+type+"[0-9].[0-9][0-9][0-9].gz")
        g_file_list = glob(gzip_path)
    
    if len(g_file_list) == 0:
        rapid_path= os.path.join(dir,"g"+type+"[0-9].[0-9][0-9][0-9].rap.Z")    
        g_file_list = glob(rapid_path);
        
    return g_file_list

def get_q_file_list(dir=os.getcwd(),expt = "*"):
    
    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    final_path= os.path.join(dir,"q"+expt+"a"+".[0-9][0-9][0-9]")    
    q_file_list = glob(final_path);
    
    if len(q_file_list) == 0:
        final_path= os.path.join(dir,"q"+expt+"a"+".[0-9][0-9][0-9].gz")    
        q_file_list = glob(final_path);
        
    if len(q_file_list) == 0:
        final_path= os.path.join(dir,"q"+expt+"a"+".[0-9][0-9][0-9].Z")    
        q_file_list = glob(final_path);
        
    return q_file_list
   
def get_prt_file_list(dir=os.getcwd(),expt = "*"):    

    dir = os.path.normcase(dir);
    dir = os.path.normpath(dir);
    
    # look for text files
    final_path= os.path.join(dir,"gk"+expt+"[0-9][0-9][0-9][0-9][0-9].prt")  
    prt_file_list = glob(final_path);
    
    # if no text files look for gzip'ed files
    if len(prt_file_list) == 0:
        final_path= os.path.join(dir,"gk"+expt+"[0-9][0-9][0-9][0-9][0-9].prt.gz")  
        prt_file_list = glob(final_path);
        
    # finally look for compressed files    
    if len(prt_file_list) == 0:
        final_path= os.path.join(dir,"gk"+expt+"[0-9][0-9][0-9][0-9][0-9].prt.Z")  
        prt_file_list = glob(final_path);
    
    return prt_file_list  

def get_autcln_file_list(dir=os.getcwd()):
    
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    final_path = os.path.join(dir,"autcln.post.sum")
    autcln_file_list = glob(final_path)
    
    if len(autcln_file_list) == 0:
        final_path = os.path.join(dir,'autcln.post.sum.gz')
        autcln_file_list = glob(final_path)
        
    if len(autcln_file_list) == 0:
        final_path = os.path.join(dir,'autcln.post.sum.Z')
        autcln_file_list = glob(final_path)
        
    return autcln_file_list

def get_gamit_config_file_list(dir = os.getcwd()):
    
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    final_path = os.path.join(dir,"*.gamit_config")
    gamit_config_file_list = glob(final_path)
    
    if len(gamit_config_file_list) == 0:
        final_path = os.path.join(dir,'gamit_config.gz')
        gamit_config_file_list = glob(final_path)
        
    if len(gamit_config_file_list) == 0:
        final_path = os.path.join(dir,'gamit_config.Z')
        gamit_config_file_list = glob(final_path)
        
    return gamit_config_file_list

def get_clk_file_list(dir=os.getcwd(),type='*'):
    
    # good cross platform shit
    dir = os.path.normcase(dir)
    dir = os.path.normpath(dir)
    
    # make the path
    path = os.path.join(dir,type+'[0-9][0-9][0-9][0-9][0-9].clk');
    clk_file_list = glob(path);
    
    # if the list is empty look for compressed files
    if len(clk_file_list) == 0:
        clk_file_list = glob(path + '.Z');
        
    if len(clk_file_list) == 0:
        clk_file_list = glob(path + '.gz');
        
    # that's a wrap ...
    return clk_file_list;
     
