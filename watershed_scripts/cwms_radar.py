import os
import sys
from hec.heclib.util import HecTime
from hec.script import MessageBox
script_name = arg2
# Add rtsutils package to sys.path before importing
try:
    sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
    from rtsutils import cavistatus, cwmsradar
except ImportError, ex:
    raise
#
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    raise Exception('No Forecast open or in "Setup Tab"')
cwmsdat = cwmsradar.CwmsRADAR()
cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
cwmsdat.dssfile = os.path.join(
    cavistatus.get_database_directory(),
    '{}-grids.dss'.format(cavistatus.get_watershed().getName())
    )
cwmsdat.read_config(os.path.join(
        cavistatus.get_shared_directory(),
        'cwms_radar.config'
        )
    )
cwmsdat.set_tsids() # Reading the configutation file defines the lists but they still need to be set
cwmsdat.run()
MessageBox.showInformation(
    "Script '{}' done!".format(script_name),
    "End Process")