"""Setup initial configurations
"""

# handle the jython poop
TRUE = 1
FALSE = 0
null = None

import os.path

APPDATA = os.path.expandvars("$APPDATA")

PACKAGE_PATH = os.path.dirname(__file__)
