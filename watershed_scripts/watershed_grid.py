"""Extract gridded data from Cumulus API"""
#
# *************** Script Setup *************** 
#
# Watershed slug name defined in API
ws_name = None
# Watershed list of products as their slug name (use https://cumulus-api.rsgis.dev/products to determine slug name)
ws_products = [
    
]
# Path where to save the DSS file; environment variables accepted (e.g., '$APPDATA', '$TMP')
dsspath = None
# Name of the DSS file, w/ or w/out extenstion (e.g., 'mydss.dss' or 'mydss')
dssfilename = None
# Timezone
tz = 'UTC'
import os
import re
import subprocess
import sys
import json
import tempfile
from datetime import datetime
from java.util import TimeZone
from hec.script import Constants, MessageBox
from hec.heclib.util import Heclib, HecTime
from hec.heclib.dss import HecDSSUtilities
# Check length of product list
if len(ws_products) < 1: raise Exception("No grid products provided")
# Set some globals and add to the PATH
_start = datetime.now()
True = Constants.TRUE
False = Constants.FALSE
APPDATA = os.getenv('APPDATA')
RSGIS = os.path.join(APPDATA, "rsgis")
CAVI_EXE = os.path.join(RSGIS, 'rtsutils', 'cavi.exe')
SUB_COMMAND = 'grid'
_stdin = {
    'Scheme': 'https',
    'Host': 'cumulus-api.rsgis.dev',
    'Products': ws_products,
}
Heclib.zset('MLVL', '', 1)
"""Try importing rtsutils, which imports hec2, package.  An exception is thrown
if not in CWMS CAVI or RTS CAVI.  This will determine if this script runs in the
CAVI or outside that environment.  ClientAppCheck.haveClientApp() was tried but
does not provide expected results.
"""
try:
    # Add rtsutils package to sys.path before importing
    if os.path.isdir(RSGIS) and (RSGIS not in sys.path):
            sys.path.append(RSGIS)
            from rtsutils import cavistatus
    cavi_env = True
except ImportError as ex:
    cavi_env = False
# Scripts in the CAVI send out a couple arguments
script_name = "{}.py".format(arg2)
# Watershed name as a slug from the active watershed or user defined
ws_name = cavistatus.get_watershed().getName() if ws_name is None else ws_name
ws_name_slug = re.sub(r'\s+|_', '-', ws_name).lower()
_stdin['Slug'] = ws_name_slug
# Get the active time window and raise an exception if no forecast open
# Convert to UTC
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    raise Exception('No forecast open on Modeling tab to get a timewindow.')
st = HecTime(st, HecTime.MINUTE_GRANULARITY)
st.showTimeAsBeginningOfDay(True)
print('Converting time window to UTC for API request.')
ws_tz = cavistatus.get_timezone()
HecTime.convertTimeZone(st, ws_tz, TimeZone.getTimeZone('UTC'))    
et = HecTime(et, HecTime.MINUTE_GRANULARITY)
et.showTimeAsBeginningOfDay(True)
HecTime.convertTimeZone(et, ws_tz, TimeZone.getTimeZone('UTC'))    
after = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(st.year(), st.month(), st.day(), st.hour(), st.minute())
before = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(et.year(), et.month(), et.day(), et.hour(), et.minute())    
_stdin['After'] = after
_stdin['Before'] = before
# DSS filename and path
if dssfilename is None: dssfilename = 'grid.dss'
if not dssfilename.endswith('.dss'): dssfilename += '.dss'
if dsspath is None: dsspath = cavistatus.get_database_directory()
dsspath = os.path.expandvars(dsspath)
dbdss = os.path.join(dsspath, dssfilename)
print('DSS: {}'.format(dbdss))
# Subprocess to Go EXE and get the stdout
# NEED '-stdout' to get the output
CMD = ' '.join([
    CAVI_EXE,
    SUB_COMMAND,
    '-stdout',
])
print('Subprocess Command: {}'.format(CMD))
sp = subprocess.Popen(
    CMD,
    shell=True,
    cwd=os.path.join(RSGIS, 'rtsutils'),
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
stdout, stderr = sp.communicate(input=json.dumps(_stdin))
print(stderr)
if "Error" in stderr: raise Exception(stderr)
# Convert Version
_, fp = stdout.split('::')
if os.path.exists(fp):
    dss7 = HecDSSUtilities()
    dss7.setDSSFileName(fp)
    dss6_temp = os.path.join(tempfile.gettempdir(), 'dss6.dss')
    result = dss7.convertVersion(dss6_temp)
    dss6 = HecDSSUtilities()
    dss6.setDSSFileName(dss6_temp)
    dss6.copyFile(dbdss)
    dss7.close()
    dss6.close()
    try:
        os.remove(fp)
        os.remove(dss6_temp)
    except Exception as err:
        print(err)
    msg = 'Converted \'{}\' to \'{}\' (int={})'.format(fp, dbdss, result)
else:
    msg = 'No grid'
print(msg)
_end = datetime.now()
dur = _end - _start
MessageBox.showInformation(msg, script_name)
