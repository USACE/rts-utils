"""
CAVI status functions providing attributes for CAVI, CAVI modules, and Forecasts
"""
import os
from hec2.rts.script import RTS as ScriptRts, Forecast
from hec2.rts.client import RTS as ClientRts
from hec2.rts.ui import DataAcqTab, DataVisTab, ForecastTab, RtsProjectTab
from java.util import TimeZone

__all__ = ['get_working_dir', 'get_watershed',
    'get_project_directory', 'get_database_directory', 'get_shared_directory',
    'get_data_timewindow', 'get_current_module', 'get_timezone', 'get_timewindow',
    'get_selected_forecast', 'get_extract_timewindow', 'get_forecast_dss']

def get_working_dir():
    '''
    Return java.lang.String

    Get the working directory, CWMS_HOME.
    '''
    return ClientRts.getRTS().getWorkingDir()

def get_watershed():
    '''
    Return hec2.rts.model.Watershed
    '''
    return ScriptRts.getWatershed()

def get_project_directory():
    '''
    Return java.lang.String

    Get the open watershed and return its project directory
    '''
    return get_watershed().getProjectDirectory()

def get_database_directory():
    '''
    Return java.lang.String

    Get the open watershed and return its project database directory
    '''
    _dir = get_project_directory()
    _list = _dir.split(os.sep)[:-2]
    _list.append('database')
    return os.sep.join(_list)

def get_shared_directory():
    '''
    Return java.lang.String

    Get the open watershed and return its project's shared directory
    '''
    _dir = get_project_directory()
    return os.sep.join([_dir, "shared"])

def get_data_timewindow():
    '''
    Return (java.lang.String StartTime, java.lang.String EndTime)

    Use this instance's methods to get start and end times
    '''
    _dtw = get_watershed().getDataTimeWindow()
    return (_dtw.getStartDateTime().toString(),
        _dtw.getEndDateTime().toString())

def get_current_module():
    '''
    Return hec2.rts.ui.RtsTab Interface
    '''
    return ScriptRts.getCurrentModule()

def get_timewindow():
    '''
    Return (java.lang.String start_time, java.lang.String end_time)

    Get the selected module and return its timewindow as a tuple of times.
    '''
    result = None
    _rtstab = get_current_module()
    if isinstance(_rtstab, RtsProjectTab):
    	result = None
    elif isinstance(_rtstab, ForecastTab):
    	if _rtstab.getForecast() == None:
            result = None
        else:
        	result = get_extract_timewindow()
    else:
        result = tuple(_rtstab.getTimeWindowString().split(";"))

    return result

def get_selected_forecast():
    '''
    Returns hec2.rts.model.Forecast
    '''
    return Forecast.getSelectedForecast()

def get_timezone():
    '''
    Returns java.util.Timezone

    Get the watershed timezone
    '''
    return ScriptRts.getWatershed().getTimeZone()

def get_extract_timewindow():
    '''
    Return (java.lang.String datetime, java.lang.String datetime)

    Get the selected forecast and return its timewindow as a tuple of datetime
    strings.
    '''
    _forecast = get_selected_forecast()
    if _forecast is not None:
    	_rtw = _forecast.getRunTimeWindow()
    	_start = _rtw.getExtractStartDateString() + ", " + _rtw.getExtractStartHrMinString()
        _end = _rtw.getExtractEndDateString() + ", " + _rtw.getExtractEndHrMinString()
        return (_start, _end)
    else:
        return None

def get_forecast_dss():
    '''
    Return java.lang.String

    Get the selected forecast and return the forecast.dss
    '''
    _forecast = get_selected_forecast()
    if _forecast is not None:
        return _forecast.getForecastDSSFilename()
    else:
        return None
