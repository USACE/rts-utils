"""Go package allowing initialization for python to know where
and which Go exe to use.
"""

import json
import subprocess
import os
import platform
import sys

_platform_sys = platform.system().lower()
if not _platform_sys:
    print("Platform not recognized")
    print("Program exiting")
    sys.exit(1)

_binding = "cavi"

# assuming Jython is running on windows
if platform.python_implementation() == "Jython":
    _platform_sys = "windows"
    _binding += ".exe"

CAVI_GO = "{}/{}/{}".format(os.path.dirname(__file__), _platform_sys, _binding)


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
