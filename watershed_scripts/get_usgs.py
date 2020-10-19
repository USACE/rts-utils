import os
import sys
from hec.heclib.util import HecTime
from hec.script import MessageBox
# Add rtsutils package to sys.path before importing
sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
from rtsutils import cavistatus, usgs
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
else:
    raise Exception('No Forecast open to get a timewindow')
rts_dss = os.path.join(cavistatus.get_database_directory(), 'test-data.dss')
retrieve = usgs.USGSDataRetrieve()
retrieve.set_dssfilename(rts_dss)
retrieve.set_begin_date(st)
retrieve.set_end_date(et)
retrieve.set_timezone('GMT')
retrieve.set_tzdss('GMT')
loc_file = os.path.join(cavistatus.get_database_directory(), 'locations.csv')
retrieve.set_locations_file(loc_file)
retrieve.run()
MessageBox.showInformation('Script Done!', 'Script Done')