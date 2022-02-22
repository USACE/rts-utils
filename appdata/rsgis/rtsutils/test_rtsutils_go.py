"""Testing rtstuils and Go without any reference to HEC java classes
"""
from collections import namedtuple
from datetime import datetime
import json
import os
import sys
# sys.path.append("/Users/rdcrljsg/projects/rts-utils/appdata/rsgis")
from rtsutils import PACKAGE_PATH
from rtsutils.cavi import cumulus
from rtsutils import go

CONFIG_NAME = "cumulus.json"
CONFIGURE = 1         # 1 = True, 0 = False, and configure = 1 is to view the GUI
DEVELOP_API = 1         # 1 = True, 0 = False, and develop = 1 is to use the develop API

SHARED = PACKAGE_PATH   # cavi.status.get_shared_directory()


cfg_file = os.path.join(SHARED, CONFIG_NAME)


# check if user needs to config
if CONFIGURE:
    # start the GUI to config before reading the config
    print("Open the GUI with config file path and name")
    # cumulus_config(cfg_file)

# open the config file and get the contents as json object
with open(cfg_file, "r") as f:
    config = json.load(f)
    Config = namedtuple("Config", config.keys())(**config)

# Check the token timestamp when using corps.cloud
# ts = datetime.fromtimestamp(Config.auth["expire"])
# if (ts - datetime.now()) < 0:
#     print("Open the GUI to update token and write to the config file")


after = "2022-02-10T12:00:00Z"
before = "2022-02-14T12:00:00Z"


args = {
    "Host": DEVELOP_API,
    "Auth": Config.auth["token"],
    "Slug": Config.watershed_slug,
    "After": after,
    "Before": before,
    "Products": Config.product_ids
}


stdout, stderr = cumulus.grids(**args)
