"""Go package allowing initialization for python to know where
and which Go exe to use.
"""

import json
import subprocess
import os
import platform
import sys
try:
    from java.lang import Exception as JavaException
except ImportError:
    JavaException = Exception

from rtsutils import null


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


def _invoke(go_flags=None, out_err=True, is_shell=False):
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
    if out_err:
        std_in_out = subprocess_popen.communicate(input=json.dumps(go_flags).encode("utf-8"))
        return std_in_out

    return subprocess_popen


def get(go_flags=None, out_err=True, is_shell=False):
    """Run the helper; obtain a short-lived CAC token for CWBI downloads."""
    flags = dict(go_flags or {})
    if not out_err or flags.get("Host", "").strip() != "cumulus.cwbi.mil":
        return _invoke(go_flags, out_err, is_shell)
    if flags.get("Scheme", "https") != "https":
        return "", "error::CWBI requires Scheme=https"
    try:
        if flags.get("Subcommand") == "grid" and not flags.get("Auth"):
            from rtsutils.go import cwbi_auth
            flags["Auth"] = cwbi_auth.get_access_token()
        stdout, stderr = _invoke(flags, out_err, is_shell)
        # Metadata is public in the API source. Retry once with a CAC token
        # only if this deployment explicitly denies the unauthenticated call.
        if flags.get("Subcommand") == "get" and not flags.get("Auth") and (
                "HTTP 401" in stderr or "HTTP 403" in stderr):
            from rtsutils.go import cwbi_auth
            try:
                flags["Auth"] = cwbi_auth.get_access_token()
            except (Exception, JavaException) as exc:
                return "", stderr + "\nerror::CAC retry failed: " + str(exc)
            return _invoke(flags, out_err, is_shell)
        return stdout, stderr
    except (Exception, JavaException) as exc:
        return "", "error::Cumulus helper {}: {}".format(CAVI_GO, str(exc))
