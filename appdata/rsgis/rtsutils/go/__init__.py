"""Go package allowing initialization for python to know where
and which Go exe to use.
"""

import json
import subprocess
import os
import platform
import sys

platform_sys = platform.system()
if not platform_sys and not platform_sys == "Java":
    print("Platform not recognized")
    print("Program exiting")
    sys.exit(1)


CAVI_GO = "{}/{}/cavi".format(os.path.dirname(__file__), platform_sys.lower())


def get(d, sh=True):
    """Method to initiate the Go binding as a subprocess

    Parameters
    ----------
    d : dict
        dictionary defining Go binding flag requirements
    sh : bool, optional
        execute through a shell, by default True

    Returns
    -------
    tuple[bytes, bytes]
        returns a tuple (stdout, stderr)
    """
    sp = subprocess.Popen(
        CAVI_GO,
        shell=sh,
        cwd=os.path.dirname(__file__),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return sp.communicate(input=json.dumps(d))

if __name__ == "__main__":
    pass
    # testing
    # get()