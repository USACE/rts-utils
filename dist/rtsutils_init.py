"""Initialize the user with rtsutils

This setup script is specific to CWMS on Windows
"""
#
import os
import sys
import urllib2
import distutils.dir_util
from io import BytesIO
from zipfile import ZipFile
from collections import namedtuple

from javax.swing import JOptionPane

FIELD_NAMES = [
    "user",
    "repo",
    "branch",
    "file_path",
    "personal_config",
    "cavi_config_name",
    "include",
    "appdata",
    "rtsutils_dst",
    "update_script",
    "personal_config_path",
    "rtsutils_src",
]

def extract_zip(src, dst):
    """read the zip file as bytes and extract"""
    open_url = urllib2.urlopen(src)
    bytes_io = BytesIO(open_url.read())
    open_url.close()
    with ZipFile(bytes_io, "r") as zip_ref:
        zip_ref.extractall(dst)


def main(cfg):
    """Initial setup rtsutils

    Parameters
    ----------
    cfg : namedtuple
        namedtuple of configurations
    """

    # Extract the zip file from the repo 'dist' directory
    extract_zip(cfg.rtsutils_src, cfg.rtsutils_dst)
    # add an include to the CAVI.config if it is NOT there
    with open(cfg.personal_config_path, "w") as fp:
        fp.write(cfg.include)
    #
    try:
        # add to sys.path to use downloaded package
        sys_path = os.path.join(cfg.appdata, cfg.repo)
        if os.path.isdir(sys_path) and (sys_path not in sys.path):
            sys.path.append(sys_path)
        # import methods
        from rtsutils import go, TRUE, FALSE
        from rtsutils.cavi.jython import status

        # check the user's CAVI personal configurations
        cavi_config_path = os.path.join(status.get_working_dir(), cfg.cavi_config_name)
        with open(cavi_config_path, "r") as fc:
            if cfg.personal_config not in fc.read():
                with open(cavi_config_path, "a") as append_cfg:
                    append_cfg.write(
                        r"include $APPDATA\{}\{}".format(cfg.repo, cfg.personal_config)
                    )
                    append_cfg.write("\n\n# Here is the space after the last line\n\n")
            else:
                print("{} already in CAVI.config".format(cfg.personal_config))

            # use go.get() to clone/update the repo on the user's pc
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
            if "error" in std_err:
                JOptionPane.showMessageDialog(
                    None,
                    std_err,
                    "Program Error",
                    JOptionPane.ERROR_MESSAGE,
                )
                raise Exception(std_err)
        #
        # copy all scripts from dist/scripts
        update_src = os.path.join(cfg.rtsutils_dst, "dist", "scripts")
        update_dst = os.path.join(status.get_watershed(), "scripts")
        distutils.dir_util.copy_tree(update_src, update_dst)
        # copy all files from dist/shared
        update_src = os.path.join(cfg.rtsutils_dst, "dist", "shared")
        update_dst = os.path.join(status.get_watershed(), "shared")
        distutils.dir_util.copy_tree(update_src, update_dst)

    except ImportError as ex:
        print(ex)


if __name__ == "__main__":
    Config = namedtuple("Config", FIELD_NAMES)
    Config.user = "USACE"
    Config.repo = "rts-utils"
    Config.branch = "refactor/rtsutil-package"
    Config.file_path = "dist/rts-utils.zip"
    Config.personal_config = "RTSUTILS-Personal.config"
    Config.cavi_config_name = "CAVI.config"
    Config.include = "vmparam -Dpython.path=$APPDATA\\{}\\".format(Config.repo)
    Config.appdata = os.getenv("APPDATA")
    Config.rtsutils_dst = os.path.join(Config.appdata, Config.repo)
    Config.personal_config_path = os.path.join(Config.rtsutils_dst, Config.personal_config)
    Config.rtsutils_src = (
        "https://raw.githubusercontent.com/{USER}/{REPO}/{BRANCH}/{FILE_PATH}".format(
            USER=Config.user, REPO=Config.repo, BRANCH=Config.branch, FILE_PATH=Config.file_path
        )
    )

    main(Config)
