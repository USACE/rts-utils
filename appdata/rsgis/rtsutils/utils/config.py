"""Handle configurations for watershed scripts
"""

import os
import platform
import sys
import json

# base configuration for Windows
cfg_base = {
    "default": {
        "rsgis_package": "APPDATA",
        "rsgis": "rsgis/rtsutils",
        "cavi_go": "rsgis/rtsutils/CaviTools",
        "dsspath": "",
    },
    "script_name1": {
        "host": "",
        "endpoint": "",
        "after": "",
        "before": "",
        "watershed_id": "00000000-0000-0000-0000-000000000000",
    },
    "script_name2": {
        "host": "",
        "endpoint": "",
        "after": "",
        "before": "",
        "watershed_id": "00000000-0000-0000-0000-000000000000",
        "product_ids": [
            "00000000-0000-0000-0000-000000000000",
            "00000000-0000-0000-0000-000000000000",
        ],
    },
    "usgs_codes": {
        "00065": ("Stage", "feet", "inst-val", "water-usgs"),
        "00061": ("Flow", "cfs", "per-aver", "water-usgs"),
        "00060": ("Flow", "cfs", "inst-val", "water-usgs"),
        "62614": ("Elev", "feet", "inst-val", "water-usgs"),
    },
}

class JsonConfigParser():


    def __init__(self, config_file):
        # only using Windows
        self.platform_system = platform.system()

        self.is_windows = True if self.platform_system == "Windows" else False
        self.config_file = config_file
        self.check_config(self.config_file)

        # if all checks then read it
        self.cfg_dict = self.read(self.config_file)


    def check_config(self, cfg_file):
        if os.path.isfile(cfg_file) and self.is_windows:
            return self.parse(cfg_file)
        elif self.is_windows:
                appdata = os.path.expandvars("$APPDATA")
                self.config_file = os.path.join(appdata, ".rtsutils")
                self.write(self.config_file)
                print("Writing basic configuration to '{}'".format(self.config_file))
        else:
            print("Configuration check not satisfied")
            print("Configuration path and file defined as '{}'".format(cfg_file))
            print("Platform system Windows only.  This system is '{}'".format(self.platform_system))
            print("Program Exiting")
            sys.exit(1)


    def read(self, cfg_file):
        return json.load(cfg_file, encoding="utf-8")


    def write(self, cfg_file, cfg_json=cfg_base):
        return json.dump(cfg_json, cfg_file)


    @property
    def attribute(self, attr, key):
        try:
            return self.cfg_dict[attr][key]
        except KeyError as ex:
            print(ex)
            raise

    @attribute.setter
    def attribute(self, attr, key, value):
        if isinstance(self.cfg_dict[attr][key], list):
            self.cfg_dict[attr][key].append(value)
        else:
            self.cfg_dict[attr][key] = value

    @property
    def attributes(self, attr):
        try:
            return self.cfg_dict[attr]
        except KeyError as ex:
            print(ex)
            raise

    @attributes.setter
    def attributes(self, attr, d):
        self.cfg_dict[attr] = d

