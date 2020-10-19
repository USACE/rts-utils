"""
Initial setup for the cwms_data2dss.py module
"""

__all__ = [
    'CwmsRADAR'
    ]

from java.util import TimeZone
from hec.script import Constants
import os
import sys
import tempfile
import string
import json
import logging
import cwms_data2dss

# A few constants
True = Constants.TRUE
False = Constants.FALSE
time_zones = TimeZone.getAvailableIDs()

# modify the program name to reflect the imported module
cwmsdata_file = cwms_data2dss.__file__.replace("$py.class", ".py")
cwms_data2dss.progName = os.path.split(cwmsdata_file)[1]

class CwmsRADAR():
    '''
    CWMS Data class used to set inputs that will ultimately build the sys.argv
    that the cwms_data2dss.py module will use.
    '''

    def __init__(self):
        '''
        Initialize the class
        '''
        print('Initialize class CwmsRADAR')
        tmpdir = tempfile.gettempdir()
        self.input = None
        self.dssfile = os.path.join(tmpdir, 'cwms-data.dss')
        self.version = None
        self.begintime = None
        self.endtime = None
        self.timezone = None
        self.tsids = None
        self.dssids = None
    
    def run(self):
        '''
        Build the sys.argv and then run the module
        '''
        self.arg_dict = {
        'i': self.input,
        'd': self.dssfile,
        'v': self.version,
        'b': self.begintime,
        'e': self.endtime,
        'z': self.timezone
        }

        print('DSS file set to: {}'.format(self.dssfile))
        
        sys_argv = [cwmsdata_file]
        for key, val in self.arg_dict.iteritems():
            if val is not None:
                sys_argv.append('-' + key)
                sys_argv.append(val)
        
        sys.argv = sys_argv

        try:
            if os.path.exists(self.input):
                print('Starting cwms-data2dss module')
                cwms_data2dss.main()
            else:
                print('No input file!')
        except TypeError, err:
            print(err)
            sys.exit(1)

    def read_config(self, config=None):
        '''
        '''
        
        def read_config(jsonconfig):
            # jdata = None
            try:
                with open(jsonconfig, 'r') as jsonfile:
                    jdata = json.loads(jsonfile.read())
            except ValueError, ex:
                raise Exception("Check config file JSON formatting!")

            return jdata
        
        if config is not None:
            self.tsids = list()
            self.dssids = list()
            json_dict = read_config(config)
            for k, val in json_dict.iteritems():
                self.tsids.append(k)
                self.dssids.append(val)

    def set_tsids(self, tsids=None, dssids=None):
        '''
        Input is a list of TSIDs and DSS IDs.  If no DSS IDs, TSID names will
        be used.  This def will create a temporary file, write the names in the
        cwms_data2dss format, and set the -i as the temporary file
        '''
        if tsids is None: tsids = self.tsids
        if dssids is None: dssids = self.dssids

        tmpfile = tempfile.NamedTemporaryFile(mode='w+b', prefix='cwmsdata',
            suffix='.in', delete=False)
        self.input = tmpfile.name
        tmpfile.close()
        
        if (dssids is None or len(dssids) == 0 or len(tsids) != len(dssids)):
            print('No DSS pathnames provided.')
            print('DSS pathnames will be built from TSIDs')
            dssids = []
            for tsid in tsids:
                if '/' not in tsid:
                    print('Office ID not defined for pathname.')
                    #raise Exception('Office ID not defined for pathname.')
                    tmpfile.close()
                    sys.exit(1)
                tspath = tsid.split('/')[-1]
                loc, par, ptype, inter, dur, ver = map(string.upper, tspath.split('.'))
                inter = inter.replace('~', '')
                inter = inter.replace('MINUTES', 'MIN')
                inter = inter.replace('HOURS', 'HOUR')
                dssids.append('//{}/{}//{}/{}/'.format(loc, par, inter, ver))
        
        if len(tsids) == len(dssids):
            with open(self.input, 'wb') as f:
                for i in range(len(tsids)):
                    f.write(tsids[i] + " = " + dssids[i] + '\n')

    def format_datetime(self, dt):
        '''
        Datetime (dt) input is a HecTime.  Output is a string formated for
        cwms_data2dss.py
        '''
        dt.showTimeAsBeginningOfDay(True)
        _dt = '{:04}-{:02}-{:02}T{:02}:{:02}:00'.format(dt.year(), dt.month(),
            dt.day(), dt.hour(), dt.minute())
        return _dt

    def set_timezone(self, tz):
        '''
        Timezone input is a string.
        '''
        if tz in time_zones:
            self.timezone = tz
            print('Timezone set to: {}'.format(self.timezone))
        else:
            print('Timezone not in list of available options.')
            print('Timezone set to UTC.')
            self.timezone = 'UTC'