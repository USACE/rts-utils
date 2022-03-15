"""Setup initial configurations
"""

import os.path

# handle the jython poop
null = None

APPDATA = os.path.expandvars("$APPDATA")

PACKAGE_PATH = os.path.dirname(__file__)
