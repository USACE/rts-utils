"""
"""
import json
import os
import tempfile
from java.util import TimeZone
from hec.heclib.util import HecTime
from hec.heclib.dss import HecDSSUtilities
from rtsutils.cavi import cumulus, status, CUMULUS_CONFIG

NAME = "cumulus_qpe",  # name corresponding to what configuration is named in the GUI
CONFIGURE = 0,         # 1 = True, 0 = False, and configure = 1 is to view the GUI
DEVELOP_API = 0,         # 1 = True, 0 = False, and develop = 1 is to use the develop API

SHARED = status.get_shared_directory()


# check if user needs to config
if CONFIGURE:
    # start the GUI to config before reading the config
    print("Open the GUI")
config = json.load(os.path.join(SHARED, CUMULUS_CONFIG))
config_name = config[NAME]
dss = config_name["dss"]
tw = status.get_timewindow()
if tw != None:
    st, et = tw
else:
    raise Exception("No forecast open on Modeling tab to get a timewindow")
st = HecTime(st, HecTime.MINUTE_GRANULARITY)
st.showTimeAsBeginningOfDay(True)
print('Converting time window to UTC for API request.')
ws_tz = status.get_timezone()
HecTime.convertTimeZone(st, ws_tz, TimeZone.getTimeZone('UTC'))
et = HecTime(et, HecTime.MINUTE_GRANULARITY)
et.showTimeAsBeginningOfDay(True)
HecTime.convertTimeZone(et, ws_tz, TimeZone.getTimeZone('UTC'))
after = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(st.year(), st.month(), st.day(), st.hour(), st.minute())
before = '{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z'.format(et.year(), et.month(), et.day(), et.hour(), et.minute())
args = {
    "host": DEVELOP_API,
    "slug": config_name["slug"],
    "after": after,
    "before": before,
    "products": config_name["product_ids"]
}
stdout, stderr = cumulus.request(**args)
_, fp = stdout.split('::')
if os.path.exists(fp):
    dss7 = HecDSSUtilities()
    dss7.setDSSFileName(fp)
    dss6_temp = os.path.join(tempfile.gettempdir(), 'dss6.dss')
    result = dss7.convertVersion(dss6_temp)
    dss6 = HecDSSUtilities()
    dss6.setDSSFileName(dss6_temp)
    dss6.copyFile(dss)
    dss7.close()
    dss6.close()
    try:
        os.remove(fp)
        os.remove(dss6_temp)
    except Exception as err:
        print(err)
else:
    msg = 'No grid'
print(msg)

