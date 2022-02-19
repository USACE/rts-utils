"""Utilities supporting CAVI tools

Java classes used to render dialogs to the user within the
CAVI environmnet
"""

from javax.swing import JOptionPane

def token():
    """Provide the user a dialog to add their bearer token

    Return
    ------
    string
        User's input into dialog
    """

    msg = """The Bearer Token in your configuration has expired!

    Please enter a new token here.

    """
    token = JOptionPane.showInputDialog(
            None,                                               # dialog parent component
            msg,                                                # message
            "Bearer Token Input",                               # title
            JOptionPane.WARNING_MESSAGE
            )

    return token
