"""Setup initial configurations
"""

import os
import os.path
import platform
import sys

CUMULUS_CONFIG = "cumulus.json"


APPDATA = os.path.expandvars("$APPDATA")


PACKAGE_PATH = os.path.dirname(__file__)

platform_sys = platform.system()
if not platform_sys and not platform_sys == "Java":
    print("Platform not recognized")
    print("Program exiting")
    sys.exit(1)


CAVI_GO_EXE = "{}/go/{}/cavi.exe".format(PACKAGE_PATH, platform_sys.lower())
