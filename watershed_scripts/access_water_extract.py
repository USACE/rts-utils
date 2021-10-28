"""Extract timeseries data from Access2Water"""

import os
import re
import subprocess
import sys
import json
from collections import namedtuple
from functools import partial

from hec.io import TimeSeriesContainer
from hec.lang import TimeStep
from hec.script import Constants, MessageBox
from hec.heclib.dss import HecDss
from hec.heclib.util import Heclib, HecTime
from hec.hecmath.functions import TimeSeriesFunctions
from hec.hecmath import HecMath

True = Constants.TRUE
False = Constants.FALSE
APPDATA = os.getenv('APPDATA')
RSGIS = os.path.join(APPDATA, "rsgis")
CMD = os.path.join(RSGIS, 'rtsutils', 'CaviTools ')

DSSVERSION = 6
Heclib.zset('MLVL', '', 1)

#
dssfilename = 'grid.dss'
scheme = 'http'
host = '192.168.2.104'
endpoint = 'watersheds/:slug/extract'

# Parameter, Unit, Data Type, DSS Fpart (Version)
usgs_code = {
    '00065': ('Stage', 'feet', 'inst-val', 'a2w'),
    '00061': ('Flow', 'cfs', 'per-aver', 'a2w'),
    '00060': ('Flow', 'cfs', 'inst-val', 'a2w'),
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
    pathname = '//{0}/{1}//{2}/{3}/'.format(Site.site_number, parameter, epart, version).upper()
    apart, bpart, cpart, _, _, fpart = pathname.split('/')[1:-1]
    
    tsc = TimeSeriesContainer()
    tsc.fullName     = pathname
    tsc.location     = apart
    tsc.parameter    = parameter
    tsc.type         = data_type
    tsc.version      = version
    tsc.interval     = timestep_min
    tsc.units        = unit
    tsc.times        = times
    tsc.values       = Site.values
    tsc.numberValues = len(Site.times)
    tsc.startTime    = times[0]
    tsc.endTime      = times[-1]
    tsc.makeAscending()

    # Snap to regular is iregular
    if TimeSeriesFunctions.isIregular(tsc):
        # Irregular to Regular TS
        tsm = HecMath.createInstance(tsc)
        tsc = tsm.snapToRegularTimeSeries(epart, '0MIN', '0MIN', '0MIN')

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
    ws_name = cavistatus.getWatershed().getName()
    ws_name_slug = re.sub(r'\s+|_', '-', ws_name).lower()

    tw = cavistatus.get_timewindow()
    if tw == None:
        msg = "No forecast open on Modeling tab to get a timewindow."
        MessageBox.showWarning(msg,
            "No Forecast Open"
        )
        sys.exit()

    # DSS save location
    if not dssfilename.endswith('.dss'): dssfilename += dssfilename + '.dss'
    dbdss = os.path.join(cavistatus.get_database_directory(), dssfilename)
    
    endpoint = re.sub(r':\w+', ws_name_slug, endpoint)
    query = '?after=' + tw[0] + '&before=' + tw[1]
    endpoint += query

else:
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    # TESTING SECTION TO BE REMOVED OR COMMENT-OUT
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    endpoint = re.sub(r':\w+', 'kanawha-river', endpoint)
    dbdss = os.getenv('USERPROFILE') + r'\Desktop\data.dss'
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# Subprocess to Go EXE and get the stdout
CMD += '-host=' + host +' -endpoint=' + endpoint +' -scheme=' + scheme + ' -stdout'
print(CMD)
sp = subprocess.Popen(
    CMD,
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
        put_to_dss(obj, dss)

if dss: dss.close()