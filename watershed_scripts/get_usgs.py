import os
import sys
from hec.heclib.util import HecTime
from hec.script import MessageBox
script_name = arg2
try:
# Add rtsutils package to sys.path before importing
    sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
    from rtsutils import cavistatus, usgs
except ImportError, ex:
    raise
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    raise Exception('No Forecast open or in "Setup Tab"')
rts_dss = os.path.join(
    cavistatus.get_database_directory(),
    '{}-usgs-data.dss'.format(cavistatus.get_watershed().getName())
    )
retrieve = usgs.USGSDataRetrieve()
retrieve.set_dssfilename(rts_dss)
retrieve.set_begin_date(st)
retrieve.set_end_date(et)
retrieve.set_timezone('GMT')
retrieve.set_tzdss('GMT')
loc_file = os.path.join(
    cavistatus.get_shared_directory(),
    'usgs_locations.csv'
    )
retrieve.set_locations_file(loc_file)
retrieve.run()
MessageBox.showInformation(
    "Script '{}' done!".format(script_name),
    "End Process")