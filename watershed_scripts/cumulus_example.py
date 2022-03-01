"""
"""
import json
import os
import tempfile
from time import sleep

from java.util import TimeZone
from hec.heclib.util import HecTime
from hec.heclib.dss import HecDSSUtilities

# from rtsutils.cavi.jython.status import get_timewindow, get_timezone
from rtsutils import go
from rtsutils.cavi.jython.ui import extract

true = 1
false = 0

# define the configuration file for this script using 'arg2' from CAVI
# comment out 'arg2' when running in  CAVI
arg2 = "cumulus_example"
SCRIPT_NAME = "{}.py".format(arg2)
# SHARED_DIRECTORY = get_shared_directory()
# CONFIG_FILE = os.path.join(SHARED_DIRECTORY, SCRIPT_NAME)

CONFIG_FILE = r"C:\Users\u4rs9jsg\projects\rts-utils\test_cumulus.json"

CONFIGURE = true         # 1 = True, 0 = False, and configure = 1 is to view the GUI

# tw = get_timewindow()
# if tw != None:
#     st, et = tw
# else:
#     raise Exception("No forecast open on Modeling tab to get a timewindow")
# st = HecTime(st, HecTime.MINUTE_GRANULARITY)
# st.showTimeAsBeginningOfDay(True)
# print('Converting time window to UTC for API request.')
# ws_tz = get_timezone()
# HecTime.convertTimeZone(st, ws_tz, TimeZone.getTimeZone('UTC'))
# et = HecTime(et, HecTime.MINUTE_GRANULARITY)
# et.showTimeAsBeginningOfDay(True)
# HecTime.convertTimeZone(et, ws_tz, TimeZone.getTimeZone('UTC'))
# after = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(st.year(), st.month(), st.day(), st.hour(), st.minute())
# before = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(et.year(), et.month(), et.day(), et.hour(), et.minute())




params = {
    "Host": "develop-cumulus-api.corps.cloud",
    "After": "2020-02-02T12:00:00Z",
    "Before": "2020-02-05T12:00:00Z",
    "StdOut": "true",
}


cui = extract.CumulusUI()
cui.set_config_file(r"C:\Users\u4rs9jsg\projects\rts-utils\test_cumulus.json")
cui.parameters(params)


# check if user needs to config
cui.show(CONFIGURE)






# params = {
#     "host": DEVELOP_API,
#     "slug": config_name["slug"],
#     "after": after,
#     "before": before,
#     "products": config_name["product_ids"]
# }
# stdout, stderr = go.get(args)
# _, fp = stdout.split('::')
# if os.path.exists(fp):
#     dss7 = HecDSSUtilities()
#     dss7.setDSSFileName(fp)
#     dss6_temp = os.path.join(tempfile.gettempdir(), 'dss6.dss')
#     result = dss7.convertVersion(dss6_temp)
#     dss6 = HecDSSUtilities()
#     dss6.setDSSFileName(dss6_temp)
#     dss6.copyFile(dss)
#     dss7.close()
#     dss6.close()
#     try:
#         os.remove(fp)
#         os.remove(dss6_temp)
#     except Exception as err:
#         print(err)
# else:
#     msg = 'No grid'
# print(msg)
