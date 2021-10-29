#!/bin/bash
#:
#: Compile packages and dependencies
#:
#: Arguments
#: ---------
#:  $1 -> Output name (e.g., CaviTool or CaviTool.exe for Win)
#:  $2 -> Go file to build
#: 
#: Defaults
#: --------
#:  Output executable always goes to ../appdata/rsgis/rtsutils/
#:
usage(){ echo "Script '$0' Usage:" && grep "#:" $0; exit 0;}

[ $# -lt 2 ] && usage

go build -o ../appdata/rsgis/rtsutils/${1} ${2}
