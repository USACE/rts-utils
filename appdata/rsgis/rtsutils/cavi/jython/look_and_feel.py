from javax.swing import UIManager


class LookAndFeel():
    '''Set the look and feel of the UI.  Execute before the objects are created.//n
    Takes one argument for the name of the look and feel class.
    '''
    def __init__(self, name="Nimbus"):
        for info in UIManager.getInstalledLookAndFeels():
            if info.getName() == name:
                UIManager.setLookAndFeel(info.getClassName())

if __name__ == "__main__":
    LookAndFeel()
