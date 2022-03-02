"""Go package allowing initialization for python to know where
and which Go exe to use.
"""

import json
import subprocess
import os
import platform
import sys

from rtsutils import TRUE, FALSE, null


_PLATFORM_SYS = platform.system().lower()
if not _PLATFORM_SYS:
    print("Platform not recognized")
    print("Program exiting")
    sys.exit(1)

_BINDING = "cavi"



# assuming Jython is running on windows
if platform.python_implementation() == "Jython":
    _PLATFORM_SYS = "windows"
    _BINDING += ".exe"

CAVI_GO = "{}/{}/{}".format(os.path.dirname(__file__), _PLATFORM_SYS, _BINDING)

GIT_GO = "{}/{}/{}".format(os.path.dirname(__file__), _PLATFORM_SYS, "git")

def get(go_flags, subprocess_=FALSE, is_shell=TRUE):
    """Method to initiate the Go binding as a subprocess

    Parameters
    ----------
    go_flags : dict
        dictionary defining Go binding flag requirements
    sh : bool, optional
        execute through a shell, by default True

    Returns
    -------
    tuple[bytes, bytes]
        returns a tuple (stdout, stderr)
    """
    subprocess_popen = subprocess.Popen(
        CAVI_GO,
        shell=is_shell,
        cwd=os.path.dirname(__file__),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if subprocess_:
        return subprocess_popen

    return subprocess_popen.communicate(input=json.dumps(go_flags))
