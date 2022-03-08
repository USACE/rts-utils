"""Dictionary utility to read/write configuration file
"""

import json


class DictConfig:
    """Read/Write configuration file

    Returns
    -------
    None
    """

    base_cfg = {}

    def __init__(self, cfg):
        self.cfg = cfg

    def __repr__(self):
        return "{self.__class__.__name__}({self.cfg})".format(self=self)

    def read(self):
        """Read configuration file

        Returns
        -------
        None
        """
        try:
            with open(self.cfg, "r") as cfg_file:
                json_ = json.load(cfg_file)
                return json_
        except IOError:
            self.write(self.base_cfg)
            print("creating new file: {}".format(self.cfg))
            return self.read()

    def write(self, json_):
        """Write configuration file

        Parameters
        ----------
        json_ : Dict
            JSON configuration
        """
        with open(self.cfg, "w") as cfg_file:
            json.dump(json_, cfg_file, indent=4)
