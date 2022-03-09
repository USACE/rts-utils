"""Get USGS Data to DSS
"""

import os

from rtsutils.cavi.jython import status
from rtsutils.usgs import USGSDataRetrieve

from hec.script import MessageBox


tw = status.get_timewindow()
if tw != None:
    st, et = tw
    print("Time window: {}".format(tw))
else:
    raise Exception('No Forecast open or in "Setup Tab"')
rts_dss = os.path.join(
    status.get_database_directory(),
    "{}-usgs-data.dss".format(status.get_watershed().getName()),
)
retrieve = USGSDataRetrieve()
retrieve.set_dssfilename(rts_dss)
retrieve.set_begin_date(st)
retrieve.set_end_date(et)
retrieve.set_timezone("GMT")
retrieve.set_tzdss("GMT")
loc_file = os.path.join(status.get_shared_directory(), "template_usgs_locations.csv")
retrieve.set_locations_file(loc_file)
retrieve.run()
MessageBox.showInformation("Script Done", "Script Done")
