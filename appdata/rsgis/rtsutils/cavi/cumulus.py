"""Main script called by CAVI scripts
"""

import json
import subprocess
from rtsutils import CAVI_GO_EXE

hosts = {0: "https://cumulus-api.rsgis.dev",
    1: "https://develop-cumulus-api.rsgis.dev"
}
# hosts = {0: "https://cumulus-api.corps.cloud",
#     1: "https://develop-cumulus-api.corps.cloud"
# }

# 
def grids(**kwargs):
    """Run the Go routines

    stdin is a JSON formatted string with keys:

    host, after, before, watershed slug, []Products

    Returns
    -------
    tuple(str, str)
        stdout and stderr from subprocess
    """
    kwargs["host"] = hosts[kwargs["host"]]

    # Subprocess to Go EXE and get the stdout
    # NEED '-stdout' to get the output
    CMD = " ".join([
        CAVI_GO_EXE,
        "grid",
        "-stdout",
    ])
    print("Subprocess Command: {}".format(CMD))
    sp = subprocess.Popen(
        CMD,
        shell=1,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return sp.communicate(input=json.dumps(kwargs))
