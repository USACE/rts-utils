"""Setup initial configurations
"""

import os.path

# handle the jython poop
null = None

USGS_SQL_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "usgs/get_usgs.db"))

APPDATA = os.path.expandvars("$APPDATA")

PACKAGE_PATH = os.path.dirname(__file__)
