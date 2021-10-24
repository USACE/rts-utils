import os
import re
import subprocess
import sys
import tempfile
import jarray
import json
from collections import namedtuple

from java.lang import System
from java.net import URL, MalformedURLException
from java.io import BufferedReader, BufferedWriter,ByteArrayOutputStream
from java.io import InputStreamReader, OutputStreamWriter, IOException
from java.security import Security

from hec.io import TimeSeriesContainer
from hec.lang import TimeStep
from hec.script import Constants, MessageBox
from hec.heclib.dss import HecDss, HecDSSUtilities, HecTimeSeriesBase
from hec.heclib.util import Heclib, HecTime, HecTimeArray
from hec.hecmath.functions import TimeSeriesFunctions
from hec.hecmath import HecMath

True = Constants.TRUE
False = Constants.FALSE
DSSVERSION = 6
Heclib.zset('MLVL', '', 1)

APPDATA = os.getenv('APPDATA')

# List of URLs used in the script
url_root = 'https://develop-water-api.rsgis.dev'
endpoint = '/watershed/:slug/extract'
url_extract = url_root + endpoint
#


# Parameter, Unit, Data Type, DSS Fpart (Version)
usgs_code = {
    '00065': ('Stage', 'feet', 'inst-val', 'a2w'),
    '00061': ('Flow', 'cfs', 'per-aver', 'a2w'),
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
    rsgis_syspath = os.path.join(os.environ['APPDATA'], "rsgis")
    if os.path.isdir(rsgis_syspath) and (rsgis_syspath not in sys.path):
            sys.path.append(rsgis_syspath)
            from rtsutils import cavistatus
    cavi_env = True
except ImportError as ex:
    cavi_env = False

def stream_data(stream):
    byte_array_output = ByteArrayOutputStream()
    while True:
        buffer = jarray.zeros(1, 'b')
        if stream.read(buffer) > 0:
            byte_array_output.write(buffer)
        else:
            break

    byte_array_output.close()
    return byte_array_output.toString()

def service(http_method, url):
    """Initiate the service"""
    
    # url = URL(url)
    # con = url.openConnection()
    # con.setRequestProperty('Accept', 'application/json')
    # con.setRequestProperty('Content-Type', 'application/json')
    # con.setRequestMethod(http_method)
    
    # responseCode = con.getResponseCode()
    # responseMessage = con.getResponseMessage()
    # contentLength = con.getHeaderField('Content-Length')

    # stream = con.getInputStream()
    # data = stream_data(stream)
    # stream.close()
    
    # THIS IS JUST FOR TESTING
    with open(r'C:\Users\u4rs9jsg\Projects\code_repos\rts-utils\ztest_extract.json', 'r') as f:
        data = f.read()

    return data

def main():
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
        db = os.path.join(cavistatus.get_database_directory(), "grid.dss")
        cwms_home = cavistatus.get_working_dir()
        common_exe = os.path.join(os.path.split(cwms_home)[0], "common", "exe")
        
        this_script = os.path.join(cavistatus.get_project_directory(), "scripts", script_name)
        cmd = "@PUSHD {pushd}\n"
        cmd += '@Jython.bat "{script}" '
        cmd += '"{start}" "{end}" "{dss}" "{home}" "{slug}"'
        cmd = cmd.format(pushd=common_exe, script=this_script, start=tw[0],
            end=tw[1], dss=db, home=cwms_home, slug=ws_name_slug
            )
        # Create a temporary file that will be executed outside the CAVI env
        batfile = tempfile.NamedTemporaryFile(mode='w', suffix='.cmd', delete=False)
        batfile.write(cmd)
        batfile.close()
        p = subprocess.Popen("start cmd /C " + batfile.name, shell=True)
    else:
        args = sys.argv[1:]
        if len(args) < 5:
            MessageBox.showPlain(
                "Expecting five arguments.  {} arguments given".format(len(args)),
                "Exception"
                )
            raise Exception("Need more arguments")
        keys = ['start_time', 'end_time', 'dss_path', 'cwms_home', 'slug']
        args_dict = dict(zip(keys, args))
        
        
        # Get the DSS location from the CAVI
        # dss = HecDss.open(r'C:\Users\u4rs9jsg\Projects\code_repos\rts-utils\zTest.dss', DSSVERSION)
        dss = HecDss.open(args_dict['dss_path'], DSSVERSION)
        
        url_extract = url_extract.replace(':slug', args_dict['slug'])
        url_extract += '?after=' + args_dict['start_time'] + '&before=' + args_dict['end_time']
        data = service('GET', url_extract)

        json_data = json.loads(data)
        for site in json_data:
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
                    
            print(timestep_min)
            # timestep_min = abs(times[1] - times[0])
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
            
            
            # TODO Determine TimeSeriesFunctions.isIrregular(TSC) or TimeSeriesFunction.isRegular(TSC)
            if TimeSeriesFunctions.isIregular(tsc):
                # Irregular to Regular TS
                tsm = HecMath.createInstance(tsc)
                tsc = tsm.snapToRegularTimeSeries(epart, '0MIN', '0MIN', '0MIN')

            # TODO Remove later; Break to work only on the first one
            # break

            # Put the data to DSS
            try:
                dss.put(tsc)
            except:
                continue

        if dss: dss.close()
    
if __name__ == '__main__':
    main()