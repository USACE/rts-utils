"""Example Script: Extract from Water API
"""
import os
from java.util import TimeZone
from hec.heclib.util import HecTime
from hec.script import MessageBox

from rtsutils.cavi.jython.ui import cumulus
from rtsutils.cavi.jython import status

# headless run True takes predefined configurations and
# False gives the user a UI to define the configurations
HEADLESS = False

# set some initial parameters
params_ = {
    "Host": "cumulus-api.corps.cloud",
    "Scheme": "https",
    "Timeout": 600  # default is 300
}


# shred directory is the 'shared' directory in the CAVI's open watershed
SHARED = status.get_shared_directory()
CONFIG = os.path.join(SHARED, "{}-cfg.json".format(arg2))


# Get the time window from the CAVI
tw = status.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    MessageBox.showError("No forecast open on Modeling tab to get a timewindow.", "Error")
    raise Exception("No forecast open on Modeling tab to get a timewindow.")

# set the start time and convert to UTC
ws_tz = status.get_timezone()

st = HecTime(st, HecTime.MINUTE_GRANULARITY)
st.showTimeAsBeginningOfDay(True)
HecTime.convertTimeZone(st, ws_tz, TimeZone.getTimeZone("UTC"))

et = HecTime(et, HecTime.MINUTE_GRANULARITY)
et.showTimeAsBeginningOfDay(True)
HecTime.convertTimeZone(et, ws_tz, TimeZone.getTimeZone("UTC"))

after = "{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z".format(st.year(), st.month(), st.day(), st.hour(), st.minute())
before = "{}-{:02d}-{:02d}T{:02d}:{:02d}:00Z".format(et.year(), et.month(), et.day(), et.hour(), et.minute())

params_["After"] = after
params_["Before"] = before

#
cui = cumulus.Cumulus()
cui.cumulus_configuration(CONFIG)
cui.go_configuration(params_)
if HEADLESS:
    cui.execute()
else:
    cui.invoke()
