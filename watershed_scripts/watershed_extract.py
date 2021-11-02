"""Extract timeseries data from Access2Water"""

# Script Setup
# Watershed slug name defined in A2W
ws_name = None
# Path where to save the DSS file; environment variables accepted
dsspath = None
# Name of the DSS file, w/ or w/out extenstion
dssfilename = None
# Timezone
tz = 'UTC'

import os
import re
import subprocess
import sys
import json
from collections import namedtuple
from functools import partial
from java.util import TimeZone

from hec.io import TimeSeriesContainer
from hec.lang import TimeStep
from hec.script import Constants, MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import Heclib, HecTime
from hec.hecmath.functions import TimeSeriesFunctions
from hec.hecmath import HecMath, TimeSeriesMath

True = Constants.TRUE
False = Constants.FALSE
APPDATA = os.getenv('APPDATA')
RSGIS = os.path.join(APPDATA, "rsgis")
CaviTools = os.path.join(RSGIS, 'rtsutils', 'CaviTools ')


scheme = 'https'
host = 'develop-water-api.corps.cloud'
endpoint = 'watersheds/:slug/extract'

Heclib.zset('MLVL', '', 1)
DSSVERSION = 6

# Parameter, Unit, Data Type, DSS Fpart (Version)
usgs_code = {
    '00065': ('Stage', 'feet', 'inst-val', 'water-usgs'),
    '00061': ('Flow', 'cfs', 'per-aver', 'water-usgs'),
    '00060': ('Flow', 'cfs', 'inst-val', 'water-usgs'),
}

'''Try importing rtsutils, which imports hec2, package.  An exception is thrown
if not in CWMS CAVI or RTS CAVI.  This will determine if this script runs in the
CAVI or outside that environment.  ClientAppCheck.haveClientApp() was tried but
does not provide expected results.

If we are not in the CAVI environment, then we need to get the provided arguments
from this script because we will call it again outsid the CAVI environment.
'''
try:
    # Add rtsutils package to sys.path before importing
    if os.path.isdir(RSGIS) and (RSGIS not in sys.path):
            sys.path.append(RSGIS)
            from rtsutils import cavistatus
    cavi_env = True
except ImportError as ex:
    cavi_env = False

# put_to_dss(site, dss)
def put_to_dss(site, dss):
    """Save timeseries to DSS File
    
    Parameters
    ----------
    site: json
        JSON object containing meta data about the site/parameter combination,
        time array and value array
    dss: HecDss DSS file object
        The open DSS file records are written to
    Returns
    -------
    None
    
    Raises
    ------
    Put to DSS exception handled with a message output saying site not saved, but
    continues on trying additional site/parameter combinations
    """
    
    Site = namedtuple(
        'Site',
        site.keys()
    )(**site)
    parameter, unit, data_type, version = usgs_code[Site.code]
    times = [
        HecTime(t, HecTime.MINUTE_GRANULARITY).value()
        for t in Site.times
    ]
    
    timestep_min = None
    for i, t in enumerate(range(len(times) - 1)):
        ts = abs(times[t + 1] - times[t])
        if ts < timestep_min or timestep_min is None:
            timestep_min = ts

    epart = TimeStep().getEPartFromIntervalMinutes(timestep_min)

    # Set the pathname
    pathname = '/{0}/{1}/{2}//{3}/{4}/'.format(ws_name, Site.site_number, parameter, epart, version).upper()
    apart, bpart, cpart, _, _, fpart = pathname.split('/')[1:-1]
    
    container = TimeSeriesContainer()
    container.fullName     = pathname
    container.location     = apart
    container.parameter    = parameter
    container.type         = data_type
    container.version      = version
    container.interval     = timestep_min
    container.units        = unit
    container.times        = times
    container.values       = Site.values
    container.numberValues = len(Site.times)
    container.startTime    = times[0]
    container.endTime      = times[-1]
    container.timeZoneID   = tz
    # container.makeAscending()

    if not TimeSeriesMath.checkTimeSeries(container):
        return 'Site: "{}" not saved to DSS'.format(Site.site_number)

    tsc = TimeSeriesFunctions.snapToRegularInterval(container, epart, "0MIN", "0MIN", "0MIN")

    # Put the data to DSS
    try:
        dss.put(tsc)
    except Exception as ex:
        print(ex)
        return 'Site: "{}" not saved to DSS'.format(Site.site_number)



''' The main section to determine is the script is executed within or
outside of the CAVI environment
'''
# Decide to execute within the CAVI environment
if cavi_env:
    script_name = "{}.py".format(arg2)

    # Get the watershed name for the slug
    ws_name = cavistatus.get_watershed().getName() if ws_name is None else ws_name
    ws_name_slug = re.sub(r'\s+|_', '-', ws_name).lower()

    tw = cavistatus.get_timewindow()
    if tw != None:
        st, et = tw
        print("Time window: {}".format(tw))
    else:
        err = 'No forecast open on Modeling tab to get a timewindow.'
        MessageBox.showInformation(err)
        raise Exception(err)
    st = HecTime(st, HecTime.MINUTE_GRANULARITY)
    st.showTimeAsBeginningOfDay(True)
    # Convert start to UTC
    print('Converting time window to UTC for API request.')
    ws_tz = cavistatus.get_timezone()
    HecTime.convertTimeZone(st, ws_tz, TimeZone.getTimeZone('UTC'))    
    et = HecTime(et, HecTime.MINUTE_GRANULARITY)
    et.showTimeAsBeginningOfDay(True)
    # Convert end to UTC
    HecTime.convertTimeZone(et, ws_tz, TimeZone.getTimeZone('UTC'))    
    after = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(st.year(), st.month(), st.day(), st.hour(), st.minute())
    before = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(et.year(), et.month(), et.day(), et.hour(), et.minute())    
    
    # DSS filename and path
    if dssfilename is None: dssfilename = 'data.dss'
    if not dssfilename.endswith('.dss'): dssfilename += '.dss'
    if dsspath is None: dsspath = cavistatus.get_database_directory()
    dsspath = os.path.expandvars(dsspath)
    # Join the path and
    dbdss = os.path.join(dsspath, dssfilename)
    print('DSS: {}'.format(dbdss))
    
    endpoint = re.sub(r':\w+', ws_name_slug, endpoint)

else:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # TESTING SECTION WHEN NOT RUNNING IN CAVI
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    endpoint = re.sub(r':\w+', 'savannah-river-basin', endpoint)
    dbdss = os.getenv('USERPROFILE') + r'\Desktop\data.dss'
    after = '2021-10-30T12:00:00Z'
    before = '2021-10-31T23:00:00Z'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Subprocess to Go EXE and get the stdout
CMD = ' '.join([
    CaviTools,
    '-host=' + host,
    '-endpoint=' + endpoint,
    '-after=' + after,
    '-before=' + before,
    '-scheme=' + scheme,
    '-stdout'
])
print('Subprocess Command: {}'.format(CMD))
sp = subprocess.Popen(
    CMD,
    shell=True,
    cwd=os.path.join(RSGIS, 'rtsutils'),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
dss = HecDss.open(dbdss, DSSVERSION)
byte_array = bytearray()
for b in iter(partial(sp.stdout.read, 1), b''):
    byte_array.append(b)
    if b == '}':
        obj = json.loads(str(byte_array))
        byte_array = bytearray()
        if 'message' in obj.keys(): raise Exception(obj['message'])
        msg = put_to_dss(obj, dss)
        if msg: print(msg)

if dss: dss.close()
print('Script Done!')
MessageBox.showInformation('Download to: {}'.format(dbdss), 'Script Done!')