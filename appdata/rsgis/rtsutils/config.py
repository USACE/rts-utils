

import json
import os


"""
Go flag options struct used in stdin json string
Scheme     string
Host       string
Subcommand string
Slug       string
Products
After    string
Before   string
StdOut   string
OutFile  string
Endpoint string
Timeout  float64
"""

class DictConfig():
    base_cfg = {}
    
    def __init__(self, cfg):
        self.cfg = cfg

    def read(self):
        try:
            with open(self.cfg, "r") as f:
                json_ = json.load(f)
                return json_
        except :
            self.write(self.base_cfg)
            print("creating new file: {}".format(self.cfg))
            return self.read(self.base_cfg)
        finally:
            if not os.path.isfile(self.cfg):
                raise FileNotFoundError("{} not found".format(self.cfg))


    def write(self, json_):
        with open(self.cfg, "w") as f:
            json.dump(json_, f, indent=4)

