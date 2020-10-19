import os
import sys
from hec.heclib.util import HecTime
# Add rtsutils package to sys.path before importing
sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
from rtsutils import cavistatus, cwmsradar
#
tw = cavistatus.get_timewindow()
if tw != None:
    st, et = tw
else:
    raise Exception('No Forecast open to get a timewindow')
tsid_list = [
    'LRN/NAST1-CumberlandR-NashvilleTN.Stage.Inst.30Minutes.0.dcp-rev',
    'LRN/ANTT1-MillCr-AntiochTN.Precip-Inc.Total.30Minutes.30Minutes.dcp-rev',
    'LRN/Anderson.Precip-Inc.Total.15Minutes.15Minutes.CCP-Computed-Rev'
    ]
dssid_list = [
    '//NAST1-CUMBERLANDR-NASHVILLETN/STAGE//30MIN/DCP-REV/',
    '//ANNT1-MILLCR-ANTIOCHTN/PRECIP-INC//30MIN/DCP-REV/',
    '//ANDERSON/PRECIP-INC//15MIN/CCP-COMPUTED-REV'
]
cwmsdat = cwmsradar.CwmsRADAR()
cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
cwmsdat.dssfile = os.path.join(cavistatus.get_database_directory(), 'test-data.dss')
cwmsdat.set_tsids(tsid_list)                   # Define TSID only tells the script to define DSS paths
cwmsdat.set_tsids(tsid_list, dssid_list)       # Define TSID and DSS lists defines DSS path names
cwmsdat.run()