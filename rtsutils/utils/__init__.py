"""Initialize the cavi.jython module
"""

from collections import OrderedDict
import os

UTILS_PATH = os.path.join(os.path.dirname(__file__))

CLOUD_ICON = os.path.join(UTILS_PATH, "cloud.png")
USACE_ICON = os.path.join(UTILS_PATH, "usace.png")
WATER_ICON = os.path.join(UTILS_PATH, "water-drop.png")
EXTRACT_ICON = os.path.join(UTILS_PATH, "extract.png")

# utilities

def watershed_refactor(json_):
    """refactor the input list to a dictionary

    Parameters
    ----------
    json_ : dict
        JSON object

    Returns
    -------
    OrderedDict
        ordered dictionary
    """
    return OrderedDict(
        {"{}:{}".format(d["office_symbol"], d["name"]): d for d in json_}
    )

def watershed_index(ws_id, ws_dict):
    """define the JList index from selection

    Parameters
    ----------
    ws_id : string
        watershed selected
    ws_dict : dict
        dictionary of watersheds

    Returns
    -------
    int
        JList index from selected watershed
    """
    try:
        idx = [
            i
            for i, k in enumerate(sorted(ws_dict.keys()))
            if ws_id == ws_dict[k]["id"]
        ][0]
    except IndexError as ex:
        print(ex)
        print("setting index to 0")
        idx = 0

    return idx

def product_refactor(json_):
    """

    Parameters
    ----------
    json_ : dict
        list of Cumulus products

    Returns
    -------
    OrderedDict
        ordered dictionary
    """
    return OrderedDict(
        {"{}".format(d["name"].replace("_", " ").title()): d for d in json_}
    )

def product_index(prod_select, prod_dict):
    """define the JList index from selection

    Parameters
    ----------
    prod_select : string
        product selected
    prod_dict : dict
        dictionary of watersheds

    Returns
    -------
    List[int]
        list of JList indices from selected watershed
    """
    idxs = [
        i
        for i, k in enumerate(sorted(prod_dict.keys()))
        if prod_dict[k]["id"] in prod_select
    ]
    return idxs

