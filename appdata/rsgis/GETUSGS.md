[README](../../README.md)
# Get USGS

|Method|Modifier and Type|Description|
|------|-----------------|-----------|
|USGSDataRetrieve()|Class|Define parameters for getusgs.py|
|USGSDataRetrieve().run()|void|Initiates getusgs.py|
|USGSDataRetrieve().is_forget()|boolean|Is 'forget' option set|
|USGSDataRetrieve().set_begin_date(String dt)|void|Date or date/time format from HEC library|
|USGSDataRetrieve().set_end_date(String dt)|void|Date or date/time format from HEC library|
|USGSDataRetrieve().set_timezone(String tz)|void|Set the timezone for the start and ending dates; checked against available IDs|
|USGSDataRetrieve().set_dssfilename(String dssfile)|void|Specify the DSS file to use|
|USGSDataRetrieve().set_tzdss(String tz)|void|Specifies time zone to use for data stored to a HEC-DSS file|
|USGSDataRetrieve().set_locations(locations[])|void|Specify the locations (locations[]) in json format|
|USGSDataRetrieve().set_locations_file(locations_file)|void|Specify the locations file (locations_file)|
|USGSDataRetrieve().set_parameters(String paramters)|void|Specifies parameters input file; Default parameters stored in package|
|USGSDataRetrieve().set_aliases(String aliases)|void|Specifies parameter aliases input file; Default aliases stored in package|
|USGSDataRetrieve().set_working_dir(String working_dir)|void|Specifies the working directory for the 'getusgs.py'; default is the package directory|

---

## Example Scripts

___Locations Defined in Script___

```jython
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
locations = [
    {'[USGS_LOC]': '[03566700]',
        'SHEF_LOC': '',
        'DSS_A-PART': '',
        'DSS_B-PART': 'Ringgold',
        'DSS_F-PART': 'USGS',
        'CWMS_LOC': '',
        'CWMS_VER': '',
        'PARAMETERS': 'Stage,Elevation,Flow,Precip'},
    {'[USGS_LOC]': '[03567500]',
        'SHEF_LOC': '',
        'DSS_A-PART': '',
        'DSS_B-PART': 'SouthChickGage',
        'DSS_F-PART': 'USGS',
        'CWMS_LOC': '',
        'CWMS_VER': '',
        'PARAMETERS': 'Stage,Elevation,Flow,Precip'},
    {'[USGS_LOC]': '[03567340]',
        'SHEF_LOC': '',
        'DSS_A-PART': '',
        'DSS_B-PART': 'WestChickGage ',
        'DSS_F-PART': 'USGS',
        'CWMS_LOC': '',
        'CWMS_VER': '',
        'PARAMETERS': 'Stage,Elevation,Flow'},
    {'[USGS_LOC]': '[02331600]',
        'SHEF_LOC': '',
        'DSS_A-PART': '',
        'DSS_B-PART': 'Chata ',
        'DSS_F-PART': 'USGS',
        'CWMS_LOC': '',
        'CWMS_VER': '',
        'PARAMETERS': 'Stage,Elevation,Flow,Precip'}
    ]
retrieve.set_locations(locations)
retrieve.run()
MessageBox.showInformation('Script Done!', 'Script Done')
```

___Locations Defined by File in Database Directory___

```jython
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
```
