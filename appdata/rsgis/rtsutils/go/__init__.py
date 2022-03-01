"""Go package allowing initialization for python to know where
and which Go exe to use.
"""

import json
import subprocess
import os
import platform
import sys

from rtsutils import TRUE, FALSE, null


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

GIT_GO = "{}/{}/{}".format(os.path.dirname(__file__), _platform_sys, "git")

def get(d, subprocess_=FALSE, sh=TRUE):
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
    if subprocess_:
        return sp
    else:
        return sp.communicate(input=json.dumps(d))
