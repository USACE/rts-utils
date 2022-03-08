"""Utilities supporting CAVI tools

Java classes used to render dialogs to the user within the
CAVI environmnet
"""
import os
from textwrap import dedent
from rtsutils import FALSE

from hec.heclib.dss import HecDss
from java.io import File
from java.time import LocalDateTime, ZonedDateTime, ZoneId
from java.time.format import DateTimeFormatter, DateTimeFormatterBuilder
from javax.swing import JFileChooser, JFrame, JOptionPane, UIManager
from javax.swing.filechooser import FileNameExtensionFilter


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
    token_ = JOptionPane.showInputDialog(
        None,  # dialog parent component
        dedent(msg),  # message
        "Bearer Token Input",  # title
        JOptionPane.WARNING_MESSAGE,
    )

    return token_


class LookAndFeel:
    """Set the look and feel of the UI.  Execute before the objects are created.//n
    Takes one argument for the name of the look and feel class.
    """

    def __init__(self, name="Nimbus"):
        self.name = name
        for info in UIManager.getInstalledLookAndFeels():
            if info.getName() == name:
                UIManager.setLookAndFeel(info.getClassName())

    def __repr__(self):
        return "{self.__class__.__name__}({self.name})".format(self=self)


class TimeFormatter:
    """Java time formatter/builder dealing with different date time formats"""

    def __init__(self, zid=ZoneId.of("UTC")):
        self.zid = zid
        self.form_builder = self.format_builder()

    def __repr__(self):
        return "{self.__class__.__name__}({self.zid})".format(self=self)

    def format_builder(self):
        """
        Return DateTimeFormatter

        Used to define the datetime format allowing for proper parsing.
        """
        form_builder = DateTimeFormatterBuilder()
        form_builder.parseCaseInsensitive()
        form_builder.appendPattern(
            "[[d][dd]MMMyyyy[[,][ ][:][Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]"
            + "[[d][dd]-[M][MM][MMM]-yyyy[[,] [Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]"
            + "[yyyy-[M][MM][MMM]-[d][dd][['T'][ ][Hmm[ss]][H:mm[:ss]][HHmm[ss]][HH:mm[:ss]]]]"
        )
        return form_builder.toFormatter()

    def iso_instant(self):
        """
        Return DateTimeFormatter ISO_INSTANT

        Datetime format will be in the form '2020-12-03T10:15:30Z'
        """
        return DateTimeFormatter.ISO_INSTANT

    def parse_local_date_time(self, date_time):
        """
        Return LocalDateTime

        Input is a java.lang.String parsed to LocalDateTime
        """
        return LocalDateTime.parse(date_time, self.form_builder)

    def parse_zoned_date_time(self, date_time, zone_id):
        """
        Return ZonedDateTime

        Input is a java.lang.String parsed to LocalDateTime and ZoneId applied.
        """
        ldt = self.parse_local_date_time(date_time)
        return ZonedDateTime.of(ldt, zone_id)


class FileChooser(JFileChooser):
    """Java Swing JFileChooser allowing for the user to select the dss file
    for output.  Currently, once seleted the result is written to the user's
    APPDATA to be read later.
    """

    def __init__(self):
        super(FileChooser, self).__init__()
        self.output_path = None
        self.setFileSelectionMode(JFileChooser.FILES_ONLY)
        self.allow = ["dss"]
        self.destpath = None
        self.filetype = None
        self.current_dir = None
        self.title = None
        self.set_dialog_title(self.title)
        self.set_multi_select(FALSE)
        self.set_hidden_files(FALSE)
        self.set_file_type("dss")
        self.set_filter("HEC-DSS File ('*.dss')", "dss")

    def __repr__(self):
        return "{self.__class__.__name__}()".format(self=self)

    def show(self):
        """show the save dialog"""
        return_val = self.showSaveDialog(self)
        if self.destpath is None or self.filetype is None:
            return_val == JFileChooser.CANCEL_OPTION
        if return_val == JFileChooser.APPROVE_OPTION:
            self.approve_option()
        elif return_val == JFileChooser.CANCEL_OPTION:
            self.cancel_option()
        elif return_val == JFileChooser.ERROR_OPTION:
            self.error_option()

    def set_dialog_title(self, title_):
        """Set the dialog title

        Parameters
        ----------
        title_ : string
            title
        """
        self.setDialogTitle(title_)

    def set_current_dir(self, dir_):
        """set directory

        Parameters
        ----------
        dir_ : string
            set dialog current directory
        """
        self.setCurrentDirectory(File(dir_))

    def set_multi_select(self, is_enabled):
        """set multi selection in dialog

        Parameters
        ----------
        is_enabled : bool
            enable dialog multiselection
        """
        self.setMultiSelectionEnabled(is_enabled)

    def set_hidden_files(self, is_enabled):
        """set hidden files

        Parameters
        ----------
        is_enabled : bool
            enable dialog file hiding
        """
        self.setFileHidingEnabled(is_enabled)

    def set_file_type(self, file_type):
        """set dialog file type

        Parameters
        ----------
        file_type : string
            file type
        """
        if file_type.lower() in self.allow:
            self.filetype = file_type.lower()

    def set_filter(self, desc, *ext):
        """set the filter

        Parameters
        ----------
        desc : string
            description
        """
        self.remove_filter(self.getChoosableFileFilters())
        filter_ = FileNameExtensionFilter(desc, ext)
        filter_desc = [d.getDescription() for d in self.getChoosableFileFilters()]
        if not desc in filter_desc:
            self.addChoosableFileFilter(filter_)

    def set_destpath(self, dest_path):
        """set destination path in dialog

        Parameters
        ----------
        dest_path : string
            path to set as destination in dialog
        """
        self.destpath = dest_path

    def remove_filter(self, filter_):
        """remove filter from dialog

        Parameters
        ----------
        filter_ : string
            file extensions to filter in dialog
        """
        _ = [self.removeChoosableFileFilter(f) for f in filter_]

    def get_files(self):
        """get selected files

        Returns
        -------
        List
            selected files from dialog
        """
        files = [f for f in self.getSelectedFiles()]
        return files

    def cancel_option(self):
        """cancel option"""
        for _filter in self.getChoosableFileFilters():
            self.removeChoosableFileFilter(_filter)

    # def error_option(self):
    #     """error option not used"""
    #     ...

    def approve_option(self):
        """set output path to selected file"""
        self.output_path = self.getSelectedFile().getPath()
        if not self.output_path.endswith(".dss"):
            self.output_path += ".dss"


if __name__ == "__main__":
    # testing purposes
    # testing TimeFormatter()
    # tf = TimeFormatter()
    # tz = tf.zid
    # st = tf.parse_zoned_date_time("2022-02-02T12:00:00", tz)
    # et = tf.parse_zoned_date_time("2022-02-12T12:00:00", tz)
    # print(st, et)

    # testing FileChooser()
    fc = FileChooser()
    fc.title = "Select Output DSS File"
    fc.set_current_dir(os.getenv("HOME"))

    fc.show()
    print(type(fc.output_path))
    # dss = HecDss.open(fc.output_path)
    # if dss:
    #     dss.close()
