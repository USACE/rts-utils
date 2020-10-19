import os
import sys
from hec.heclib.util import HecTime
from hec.script import MessageBox
# Add rtsutils package to sys.path before importing
sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
from rtsutils import cavistatus, cwmsradar
#
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
else:
    MessageBox.showError('No Forecast open to get a timewindow', 'Error')
    raise Exception('No Forecast open to get a timewindow')
cwmsdat = cwmsradar.CwmsRADAR()
cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
cwmsdat.dssfile = os.path.join(cavistatus.get_database_directory(), 'test-data.dss')
cwmsdat.read_config(os.path.join(cavistatus.get_database_directory(), 'cwms_radar.config'))
cwmsdat.set_tsids() # Reading the configutation file defines the lists but they still need to be set
cwmsdat.run()