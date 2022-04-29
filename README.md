# RTS Data Acquisition Utilities


> **NOTICE:** *script_downloader has been replaced by a new process.  See the **[Wiki](https://github.com/USACE/rts-utils/wiki)** for details.*

> `rtsutils` has been refactored to act more like an installed Python package within the CAVI virtual environment.  Code that once added `rtsutils` to the `PYTHONPATH`, within each script, has been removed and CAVI configurations modified by the installer placing the package in the `PYTHONPATH`.  This allows for traditional `import` statements accessing `rtsutils` modules.  A single `include` statement will be added to the CWMS installation CAVI configuration file (HEC-RTS.config for RTS) during the installation process.

## RTSUTILS Package Installation, *First Iteration*

___Read instructions before executing.___

1. Click [here](https://raw.githubusercontent.com/USACE/rts-utils/master/watershed_scripts/script_downloader.py) for the raw `script_downloader` code

1. Select all code in the browser (Ctrl + A)

1. Copy code to your clipboard (Ctrl + C)

1. Create a new script from the CAVI Script Editor and name it `script_downloader`

1. Paste code (Ctrl + V) into the new CAVI script

1. In the Script Editor: Save script

1. Run `script_downloader`

The `script_downloader` will download and install necessary package(s) and template watershed scripts to the currently opened watershed.  Installing/Updating with the `script_downloader` will ask you if you want to view instructions for that script, which comes back to this repository specific to the utility.
