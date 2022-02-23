"""Utilities supporting CAVI tools

Java classes used to render dialogs to the user within the
CAVI environmnet
"""

import json
import os
from datetime import date, datetime
from textwrap import dedent

from java.io import File
from java.time import ZoneId, LocalDateTime, ZonedDateTime
from java.time.format import DateTimeFormatterBuilder, DateTimeFormatter
from javax.swing import JOptionPane, UIManager, JFileChooser, JTextField
from javax.swing.filechooser import FileNameExtensionFilter


def read_config(cfg):
    with open(cfg, "r") as f:
        cfg_in = json.load(f)
    return cfg_in

def write_config(cfg, json_):
    with open(cfg, "w") as f:
        json.dump(json_, f, indent=4)


def watershed_refactor(json_):
    return {
        "{}:{}".format(d['office_symbol'], d['name']): d 
        for d in json_
        }


def product_refactor(json_):
    return {
        "{}".format(d['name'].replace("_", " ").title()): d 
        for d in json_
        }

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
            dedent(msg),                                                # message
            "Bearer Token Input",                               # title
            JOptionPane.WARNING_MESSAGE
            )

    return token


class LookAndFeel():
    '''Set the look and feel of the UI.  Execute before the objects are created.//n
    Takes one argument for the name of the look and feel class.
    '''
    def __init__(self, name="Nimbus"):
        for info in UIManager.getInstalledLookAndFeels():
            if info.getName() == name:
                UIManager.setLookAndFeel(info.getClassName())


class TimeFormatter():
    ''' Java time formatter/builder dealing with different date time formats '''
    def __init__(self, zid=ZoneId.of("UTC")):
        self.zid = zid
        self.fb = self.format_builder()

    def format_builder(self):
        '''
        Return DateTimeFormatter

        Used to define the datetime format allowing for proper parsing.
        '''
        fb = DateTimeFormatterBuilder()
        fb.parseCaseInsensitive()
        fb.appendPattern("[[d][dd]MMMyyyy[[,][ ][:][Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]" + \
            "[[d][dd]-[M][MM][MMM]-yyyy[[,] [Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]" + \
            "[yyyy-[M][MM][MMM]-[d][dd][['T'][ ][Hmm[ss]][H:mm[:ss]][HHmm[ss]][HH:mm[:ss]]]]")
        return fb.toFormatter()

    def iso_instant(self):
        '''
        Return DateTimeFormatter ISO_INSTANT

        Datetime format will be in the form '2020-12-03T10:15:30Z'
        '''
        return DateTimeFormatter.ISO_INSTANT
        
    def parse_local_date_time(self,t):
        '''
        Return LocalDateTime

        Input is a java.lang.String parsed to LocalDateTime
        '''
        return LocalDateTime.parse(t,self.fb)

    def parse_zoned_date_time(self,t, z):
        '''
        Return ZonedDateTime

        Input is a java.lang.String parsed to LocalDateTime and ZoneId applied.
        '''
        ldt = self.parse_local_date_time(t)
        return ZonedDateTime.of(ldt, z)



class FileChooser(JFileChooser):
    '''Java Swing JFileChooser allowing for the user to select the dss file
    for output.  Currently, once seleted the result is written to the user's
    APPDATA to be read later.
    '''
    def __init__(self):
        super(FileChooser, self).__init__()
        self.config_filename = "cumulus.config"
        self.output_path = None
        self.setFileSelectionMode(JFileChooser.FILES_ONLY)
        self.allow = ['dss']
        self.destpath = None
        self.filetype = None
        self.current_dir = None
        self.title = None
        self.set_dialog_title(self.title)
        self.set_multi_select(False)
        self.set_hidden_files(False)
        self.set_file_type("dss")
        self.set_filter("HEC-DSS File ('*.dss')", "dss")
        
    def show(self):
        return_val = self.showSaveDialog(self)
        if self.destpath == None or self.filetype == None:
            return_val == JFileChooser.CANCEL_OPTION
        if return_val == JFileChooser.APPROVE_OPTION:
            self.approve_option()
        elif return_val == JFileChooser.CANCEL_OPTION:
            self.cancel_option()
        elif return_val == JFileChooser.ERROR_OPTION:
            self.error_option()
    
    def set_dialog_title(self, t):
        self.setDialogTitle(t)

    def set_current_dir(self, d):
        self.setCurrentDirectory(File(d))

    def set_multi_select(self, b):
        self.setMultiSelectionEnabled(b)
        
    def set_hidden_files(self, b):
        self.setFileHidingEnabled(b)

    def set_file_type(self, type):
        if type.lower() in self.allow:
            self.filetype = type.lower()
        
    def set_filter(self, desc, *ext):
        self.remove_filter(self.getChoosableFileFilters())
        filter = FileNameExtensionFilter(desc, ext)
        filter_desc = [d.getDescription() for d in self.getChoosableFileFilters()]
        if not desc in filter_desc:
            self.addChoosableFileFilter(filter)
    
    def set_destpath(self, r):
        self.destpath = r

    def remove_filter(self, filter):
        [self.removeChoosableFileFilter(f) for f in filter]
        
    def get_files(self):
        files = [f for f in self.getSelectedFiles()]
        return files
    
    def cancel_option(self):
        for _filter in self.getChoosableFileFilters():
            self.removeChoosableFileFilter(_filter)

    def error_option(self):
        pass
    
    def approve_option(self):
        selected_file = self.getSelectedFile().getPath()
        if not selected_file.endswith(".dss"): selected_file += ".dss"
        return selected_file
        # with open(os.path.join(APPDATA, self.config_filename), 'w') as f:
        #     f.write(selected_file)
        # self.output_path.setText(selected_file)


if __name__ == "__main__":
    # testing purposes
    pass

    # testing token()
    # token()
    
    # testing TimeFormatter()
    # tf = TimeFormatter()
    # tz = tf.zid
    # st = tf.parse_zoned_date_time("2022-02-02T12:00:00", tz)
    # et = tf.parse_zoned_date_time("2022-02-12T12:00:00", tz)
    # print(st, et)
    
    # testing FileChooser()
    fc = FileChooser()
    fc.title = "Select Output DSS File"
    fc.set_current_dir(os.getcwd())
    fc.show()
