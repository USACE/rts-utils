[README](../README.md)
# CWMS RADAR

| Method                                   | Modifier and Type | Description                                                         |
| ---------------------------------------- | ----------------- | ------------------------------------------------------------------- |
| CwmsRADAR()                              | Class             | Set inputs that are used to build the sys.argv for cwms_data2dss.py |
| CwmsRADAR().begintime                    | String            | Assign time format 'yyyy-MM-ddTHH:mm:00'                            |
| CwmsRADAR().endtime                      | String            | Assign time format 'yyyy-MM-ddTHH:mm:00'                            |
| CwmsRADAR().format_datetime(HecTime dt)  | String            | Input HecTime object returning time format 'yyyy-MM-ddTHH:mm:00'    |
| CwmsRADAR().dssfile                      | String            | Assign path and dss pathname                                        |
| CwmsRADAR().set_tsids(tsid[], [dssid[]]) | String[]          | Assign list of TSIDs and/or list of DSS IDs                         |
| CwmsRADAR().set_timezone(String tz)      | String            | Assign timezone; checked against available IDs                      |
| CwmsRADAR().run()                        | void              | Build arguments for cwms_data2dss.py and call its main() method     |

---

## Example Scripts

___TSID and DSS ID Lists___

```jython
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
```

___TSIDs and DSS IDs Defined by Configuration File___

```jython
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
cwmsdat = cwmsradar.CwmsRADAR()
cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
cwmsdat.dssfile = os.path.join(cavistatus.get_database_directory(), 'test-data.dss')
cwmsdat.read_config(os.path.join(cavistatus.get_database_directory(), 'cwms_radar.config'))
cwmsdat.set_tsids()  # Reading the configutation file defines the lists but they still need to be set
cwmsdat.run()
```

___Example: Configuration file for TSIDs and DSS IDs___

`*Do NOT leave any trailing commas (,) after the last entry!`

```json
{
    "DistrictID/Location.Parameter.ParameterType.Interval.Duration.Version": "/Apart/Bpart/Cpart/Dpart/Epart/Fpart/",
    "DistrictID/Location.Parameter.ParameterType.Interval.Duration.Version": "/Apart/Bpart/Cpart/Dpart/Epart/Fpart/"
}
```

```json

{
  "LRN/NAST1-CumberlandR-NashvilleTN.Stage.Inst.30Minutes.0.dcp-rev": "//NAST1-CUMBERLANDR-NASHVILLETN/STAGE//30MIN/DCP-REV/",
  "LRN/ANTT1-MillCr-AntiochTN.Precip-Inc.Total.30Minutes.30Minutes.dcp-rev": "//ANNT1-MILLCR-ANTIOCHTN/PRECIP-INC//30MIN/DCP-REV/"
}
```
