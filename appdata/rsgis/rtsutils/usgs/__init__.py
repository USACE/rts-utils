'''
Get USGS data Python package
'''

__all__ = ['USGSDataRetrieve']

# Java Imports
import java.util.TimeZone
# HEC Imports
import hec
# Python Imports
import os
import sys
import csv
import logging
import tempfile
import threading

# Set some constants
True = hec.script.Constants.TRUE
False = hec.script.Constants.FALSE

#getusgs_path = getusgs.__file__.replace("$py.class", ".py")
getusgs_path = os.path.join(os.path.dirname(__file__), 'getusgs.py')
#getusgs. = os.path.split(getusgs_path)[1]

class USGSDataRetrieve():
    '''
    class to define parameters for HEC's 'getUsgs.py' module
    '''
    def __init__(self):
        '''
        Initialize
        '''
        self.mod_dir = os.path.dirname(__file__)
        self.locations_file = None
        self.parameters_file = os.path.join(self.mod_dir, 'parameters.csv')
        self.aliases_file = os.path.join(self.mod_dir, 'parameter_aliases.csv')
        self.dss_filename = os.path.join(tempfile.gettempdir(), 'usgs-data.dss')
        self.tzdss = None
        self.begin_date = None
        self.end_date = None
        self.timezone = None
        self.forget = None
        self.loglevel = None
        self.working_directory = os.path.dirname(__file__)

    def run(self):
        '''
        Set the sys.argv and then execute the HEC provided 'getUsgs.py' module
        '''
        self.arg_dict = {
            'workdir': self.working_directory,
            'locations': self.locations_file,
            'parameters': self.parameters_file,
            'aliases': self.aliases_file,
            'dss': self.dss_filename,
            'tzdss': self.tzdss,
            'begindate': self.begin_date,
            'enddate': self.end_date,
            'timezone': self.timezone,
            'forget': self.forget,
            'output': self.loglevel
        }
        
        sys.argv = [getusgs_path]
        for key, val in self.arg_dict.iteritems():
            if val is not None:
                sys.argv.append('--' + key)
                sys.argv.append(val)
        
        # Threading with getusgs ending with sys.exit() is needed to run the
        # script multiple times in the CAVI environment
        thread = threading.Thread(target=self.run_seperate)
        thread.start()
        thread.join()
        
    def run_seperate(self):
        '''
        Run (import) getusgs as a seperate thread so it terminates itself and not
        all other scripts
        '''
        import getusgs

    def is_forget(self):
        '''
        Return a boolean to see if the forget option is set
        '''
        return self.forget
    
    def set_begin_date(self, d):
        '''
        Specifies the beginning of the time window for which to retrieve data
        from the USGS, in the specified or default time zone.  The format is any
        date or date/time format recognized by the HEC library. If a date only
        is specified, the time is interpreted as 00:00 of the specified day.
        '''
        self.begin_date = d

    def set_end_date(self, d):
        '''
        Specifies the end of the time window for which to retrieve data from the
        USGS, in the specified or default time zone.  The format is any date or
        date/time format recognized by the HEC library. If a date only is
        specified, the time is interpreted as 24:00 of the specified day.
        '''
        self.end_date = d 
    
    def set_timezone(self, tz):
        '''
        Set the timezone for the start and ending dates
        '''
        if tz not in java.util.TimeZone.getAvailableIDs():
            raise Exception('Incompatible timezone.\n Application quitting.')
        self.timezone = tz

    def set_dssfilename(self, dssfile):
        '''
        Specifies storing data to a HEC-DSS file. dss_filename specifies the
        HEC-DSS file to use. Relative filenames are relative to the working
        directory.
        '''
        self.dss_filename = dssfile
        
    def set_tzdss(self, tz):
        '''
        Specifies time zone to use for data stored to a HEC-DSS file. If not
        specified, the data will be stored to the HEC-DSS file in the time zone
        specified in the USGS text. Valid values for dss_time_zone are valid
        shef_time_zone values plus any valid Java time zone ID
        (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
        '''
        if tz not in java.util.TimeZone.getAvailableIDs():
            sys.exit(1)
            #raise Exception('Incompatible timezone.\n Application quitting.')
        self.tzdss = tz

    def set_locations(self, loc_parameters=None, file_path=None):
        '''
        Specifies locations input file.
        '''
        headers = ['[USGS_LOC]','SHEF_LOC','DSS_A-PART','DSS_B-PART',
            'DSS_F-PART', 'CWMS_LOC', 'CWMS_VER', 'PARAMETERS']
            
        if file_path == None:
            file_path = os.path.join(tempfile.gettempdir(), 'usgs-locations.csv')
        
            with open(file_path, 'wb') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=headers)
                csvwriter.writeheader()
                for loc_parameter in loc_parameters:
                    csvwriter.writerow(loc_parameter)
            self.locations_file = file_path
        else:
            self.locations_file = file_path
                
    def set_parameters(self, p):
        '''
        Specifies parameters input file. Defaults to Parameters.csv.
        The working directory is defaulted to the level of this module
        '''
        self.parameters_file = p
    
    def set_aliases(self, a):
        '''
        Specifies parameter aliases input file. Defaults to
        Parameter_Aliases.csv in the working directory.
        '''
        self.aliases_file = a
        
    def set_working_dir(self, wkdir):
        '''
        Specifies the working directory for the program. Any relative filenames
        specified are relative to this directory. If not specified, the
        directory this module resides is the working directory by default.
        '''
        self.working_directory = wkdir
