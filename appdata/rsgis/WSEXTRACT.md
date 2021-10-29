[README](../../README.md)
# Watershed Extract

Watershed Extract is a `Jython` script written for use in HEC's CWMS/RTS CAVI.  The script uses a `Go` program as a subproccess to fetch the result of an `Access 2 Water` endpoint (`watersheds/:watershed_slug/extract`).  The standard output from the `Go` program is parsed and records written to a DSS file.  The timewindow is determined by the CAVI and active tab.  If the active tab is `Modeling` and no forecast open, an exception is raised and the program stops.

## Script Setup

At the top of the `Jython` script (`watershed_extract.py`) there is a section to modify the watershed's slug ID, default DSS filename, and default path.  The watershed's slug ID is the watershed name with all lower case with spaces and underscore(s) ("_") replaced with a dash ("-"); see A2W endpoint `watersheds` for defined watershed slug IDs.  The default DSS filename is `data.dss`.  The default path is defined by the active watershed's `database` directory.  Paths can be defined using environment variables.

```python
# Script Setup
# Watershed slug name defined in A2W
ws_name = None
# Path where to save the DSS file
dsspath = None
# Name of the DSS file, w/ or w/out extenstion
dssfilename = None
```

### Example setup

Below are a few examples defining the watershed name, DSS path, and DSS filename.

__Example 1__

```python
# Script Setup
# Watershed slug name defined in A2W
# 'C:\\Users\\<username>\\' or r'C:\Users\<username>\'
ws_name = 'kanawha-river'
# Path where to save the DSS file
dsspath = r'C:\Users\<username>\'
# Name of the DSS file, w/ or w/out extenstion
# 'mydss' or 'mydss.dss'
dssfilename = 'mydss'
```

Console returns `DSS: C:\Users\<username>\mydss.dss`

__Example 2__

```python
# Script Setup
# Watershed slug name defined in A2W
ws_name = 'kanawha-river'
# Path where to save the DSS file
# USERPROFILE = 'C:\\Users\\<username>\\'
dsspath = '$USERPROFILE'
# Name of the DSS file, w/ or w/out extenstion
dssfilename = None
```

Console returns `DSS: C:\Users\<username>\data.dss`

__Example 3__

```python
# Script Setup
# Watershed slug name defined in A2W
# Assuming watershed name is 'MSC_Blue_Dam_River_Basin'
ws_name = None
# Path where to save the DSS file
# USERPROFILE = 'C:\\Users\\<username>\\'
dsspath = None
# Name of the DSS file, w/ or w/out extenstion
dssfilename = None
```

Console returns `msc-blue-dam-river-basin` for the watershed slug id

Console returns `DSS: <watershed location>\database\data.dss`
