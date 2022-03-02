[README](../README.md)
# CAVI Status

## CAVI Status Methods and Type

| Method                   | Modifier and Type            | Description                                                                               |
| ------------------------ | ---------------------------- | ----------------------------------------------------------------------------------------- |
| get_working_dir()        | String                       | Get the working directory, CWMS_HOME                                                      |
| get_watershed()          | hec2.rts.model.Watershed     | Return watershed object; used internally                                                  |
| get_project_directory()  | String                       | Get the open watershed and return its project directory                                   |
| get_database_directory() | String                       | Get the open watershed and return its project database directory                          |
| get_data_timewindow()    | String[]                     | Return a tuple of start time and end time                                                 |
| get_current_module()     | hec2.rts.ui.RtsTab Interface | RtsTab for the selected module                                                            |
| get_timewindow()         | String[]                     | Get the selected module and return its timewindow as a tuple of start time and end time   |
| get_selected_forecast()  | hec2.rts.model.Forecast      | Return the selected forecast object                                                       |
| get_extract_timewindow() | String[]                     | Get the selected forecast and return its timewindow as a tuple of start time and end time |
| get_forecast_dss()       | String                       | Get the selected forecast and return the forecast.dss path                                |

---

## Example Scripts

__Simple Usage__

```jython

```
