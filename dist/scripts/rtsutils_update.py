"""Update the user's rtsutils repository

This update script is Jython running in the CAVI env
"""

from collections import namedtuple
import os
from rtsutils import go, APPDATA, TRUE, FALSE

FIELD_NAMES = [
    "user",
    "repo",
    "branch",
    "appdata",
    "rtsutils_dst",
]

def main(cfg):
    """Update repo

    Parameters
    ----------
    cfg : namedtuple
        namedtuple of configurations
    """
    config = {
        "Host": "github.com",
        "Scheme": "https",
        "Subcommand": "git",
        "Endpoint": cfg.user + "/" + cfg.repo,
        "Branch": cfg.branch,
        "Path": cfg.rtsutils_dst,
    }
    std_out, std_err = go.get(config, out_err=TRUE, is_shell=FALSE)
    print(std_out)
    print(std_err)


if __name__ == "__main__":
    Config = namedtuple("Config", FIELD_NAMES)
#
# ~~~~~~ Configure Here ~~~~~~ #
#
    Config.user = "USACE"
    Config.repo = "rts-utils"
    Config.branch = "refactor/rtsutil-package"
    Config.appdata = APPDATA
    Config.rtsutils_dst = os.path.join(Config.appdata, Config.repo)
#
# ~~~~~~ Configure Here ~~~~~~ #
#

    main(Config)
