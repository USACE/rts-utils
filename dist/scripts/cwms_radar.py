"""CWMS Radar Data to DSS
"""

import os

from rtsutils.cavi.jython import status
from rtsutils.cwmsradar import CwmsRADAR

from hec.heclib.util import HecTime
from hec.script import MessageBox

#
tw = status.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    raise Exception('No Forecast open or in "Setup Tab"')

cwmsdat = CwmsRADAR()
cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
cwmsdat.dssfile = os.path.join(
    status.get_database_directory(),
    "{}.dss".format(status.get_watershed().getName()),
)
cwmsdat.read_config(os.path.join(status.get_shared_directory(), "template_cwms_radar.config"))
# Reading the configutation file defines the lists but they still need to be set
cwmsdat.set_tsids()
cwmsdat.run()
MessageBox.showInformation("Script Done", "Script Done")
