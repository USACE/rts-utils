"""Update the user's rtsutils repository

This update script is Jython running in the CAVI env
"""

import os
from rtsutils import go, APPDATA

#
# ~~~~~~~~~~ Only need to mod these, maybe ~~~~~~~~~~ #
#
USER = "USACE"
REPO = "rts-utils"
BRANCH = "refactor/rtsutil-package"
#
# ~~~~~~~~~~ Only need to mod these, maybe ~~~~~~~~~~ #
#
RTSUTILS_DST = os.path.join(APPDATA, REPO)

#
gogit_cfg = {"Endpoint": USER + "/" + REPO, "Branch": BRANCH, "Path": RTSUTILS_DST}
