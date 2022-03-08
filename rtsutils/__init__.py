"""Setup initial configurations
"""

import os.path

# handle the jython poop
TRUE = 1
FALSE = 0
null = None

APPDATA = os.path.expandvars("$APPDATA")

PACKAGE_PATH = os.path.dirname(__file__)
