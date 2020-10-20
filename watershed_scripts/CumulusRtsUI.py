# Java
from java.lang import Short, Thread
from java.net import URL, MalformedURLException
from java.time import ZoneId, LocalDateTime, ZonedDateTime
from java.time.format import DateTimeFormatterBuilder, DateTimeFormatter, DateTimeParseException
from java.io import BufferedReader, BufferedWriter
from java.io import InputStreamReader, OutputStreamWriter
from java.io import File, IOException
from java.nio.file import Files, StandardCopyOption, FileSystemException
from java.awt import Font, Point

from javax.swing import UIManager
from javax.swing import JFrame, JButton, JLabel, JTextField, JList
from javax.swing import JScrollPane, JFileChooser
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing.border import TitledBorder
from javax.swing.filechooser import FileNameExtensionFilter
# HEC
from hec.script import Constants, MessageBox
from hec.heclib.util import Heclib
from hec.heclib.dss import HecDss
from hec.heclib.grid import GridUtilities
from hec.hecmath import DSSFileException
# Python
import os
import sys
import json
import tempfile
import subprocess
#
True = Constants.TRUE
False = Constants.FALSE
# Max timeout for downloading dss files in seconds.
max_timeout = 60
# List of URLs used in the script
url_basins = "https://api.rsgis.dev/development/cumulus/basins"
url_products = "https://api.rsgis.dev/development/cumulus/products"
url_downloads = "https://api.rsgis.dev/development/cumulus/downloads"
#
'''Try importing rtsutils, which imports hec2, package.  An exception is thrown
if not in CWMS CAVI or RTS CAVI.  This will determine if this script runs in the
CAVI or outside that environment.  ClientAppCheck.haveClientApp() was tried but
does not provide expected results.

If we are not in the CAVI environment, then we need to get the provided arguments
from this script because we will call it again outsid the CAVI environment.
'''
try:
    # Add rtsutils package to sys.path before importing
    sys.path.append(os.path.join(os.environ['APPDATA'], "rsgis"))
    from rtsutils import cavistatus
    cavi_env = True
except ImportError as ex:
    print(ex)
    cavi_env = False

# Look and feel class
class LookAndFeel():
    '''Set the look and feel of the UI.  Execute before the objects are created.//n
    Takes one argument for the name of the look and feel class.
    '''
    def __init__(self, name):
        for info in UIManager.getInstalledLookAndFeels():
            if info.getName() == name:
                UIManager.setLookAndFeel(info.getClassName())

# File chooser class
class FileChooser(JFileChooser):
    '''Java Swing JFileChooser allowing for the user to select the dss file
    for output.  Currently, once seleted the result is written to the user's
    APPDATA to be read later.
    '''
    def __init__(self, output_path):
        super(FileChooser, self).__init__()
        self.config_filename = "cumulus.config"
        self.output_path = output_path
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
        self.setCurrentDirectory(d)

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
        with open(os.path.join(os.getenv('APPDATA'), self.config_filename), 'w+b') as f:
            f.write(selected_file)
        self.output_path.setText(selected_file)

# Java time formatter
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
        fb.appendPattern("[[d][dd]MMMyyyy[[,] [Hmm[ss]][H:mm[:ss]][HHmm][HH:mm[:ss]]]]" + \
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

# Define something to download the DSS and process
def download_dss(dss_url):
    '''
    Return java.nio.file.Path temp_dssfile

    Inputs: java.lang.String DSS URI
    DSS file downloaded to user's temporary directory as to not clober any existing
    DSS file and all records written to DSS OUT Path.
    '''
    # Heclib.zset('DSSV', '', 6)
    result = None
    try:
        # Create input stream reader to read the file
        url = URL(dss_url)
        urlconnect = url.openConnection()
        response_code = urlconnect.getResponseCode()
        if response_code == 200:
            input_stream = urlconnect.getInputStream()
            tempfile = Files.createTempFile("", ".dss")
            Files.copy(input_stream,
                tempfile,
                StandardCopyOption.REPLACE_EXISTING
                )
            input_stream.close()
            result = tempfile
    except IOException, ex:
        MessageBox.showError(ex, "Exception")
        raise Exception(ex)

    return result

def merge_dss(src_dss, dest_dss):
    '''
    Return Boolean

    Input: java.nio.file.Path src_path java.lang.String dest_path
    Merge all grid paths in the source dss file into the destination dss file
    '''
    result = False
    dssin = None
    # Process the DSS file
    if Files.exists(src_dss):
        try:
            dssin = HecDss.open(src_dss.toString())
            for pathname in dssin.getCatalogedPathnames():
                grid_container = dssin.get(pathname)
                grid_data = grid_container.getGridData()
                GridUtilities.storeGridToDss(dest_dss, pathname, grid_data)
            result = True
        except DSSFileException, ex:
            # MessageBox.showError(ex, "Exception")
            raise
        except Exception, ex:
            # MessageBox.showError(ex, "Exception")
            raise
        finally:
            if dssin:
                dssin.done()
                dssin.close()
            try:
                Files.deleteIfExists(src_dss)
            except FileSystemException, ex:
                # MessageBox.showError(ex, "Exception")
                raise
    else:
        result = False
    
    return result

# Cumulus UI class
class CumulusUI(JFrame):
    '''Java Swing used to create a JFrame UI.  On init the objects will be
    populated with information derived from URL requests to CUMULUS and
    the open CWMS watershed.
    '''
    def __init__(self, arg_dict):
        super(CumulusUI, self).__init__()

        # Load argument from the command line
        self.start_time = arg_dict['start_time']
        self.end_time = arg_dict['end_time']
        self.dss_path = arg_dict['dss_path']
        self.cwms_home = arg_dict['cwms_home']
        self.config = arg_dict['config']

        # Get the DSS Path if one was saved in the "cumulus.config" file
        if os.path.isfile(self.config):
            with open(os.path.join(os.getenv('APPDATA'), "cumulus.config")) as f:
                self.dss_path = f.read()

        # Get the basins and products, load JSON, create lists for JList, and create dictionaries
        self.basin_download = json.loads(self.http_get(url_basins))        
        self.jlist_basins = ["{}:{}".format(b['office_symbol'], b['name']) for b in self.basin_download]
        self.basin_meta = dict(zip(self.jlist_basins, self.basin_download))
        self.jlist_basins.sort()

        self.product_download = json.loads(self.http_get(url_products))
        self.jlist_products = ["{}".format(p['name'].replace("_", " ").title()) for p in self.product_download]
        self.product_meta = dict(zip(self.jlist_products, self.product_download))
        self.jlist_products.sort()

        btn_submit = JButton()
        lbl_start_date = JLabel()
        lbl_end_date = JLabel()
        self.txt_select_file = JTextField()
        btn_select_file = JButton()
        lbl_origin = JLabel()
        lbl_extent = JLabel()
        self.txt_originx = JTextField()
        self.txt_originy = JTextField()
        self.txt_extentx = JTextField()
        self.txt_extenty = JTextField()
        lbl_select_file = JLabel()
        comma1 = JLabel()
        comma2 = JLabel()
        paren_l1 = JLabel()
        paren_l2 = JLabel()
        paren_r1 = JLabel()
        paren_r2 = JLabel()
        self.txt_start_time = JTextField()
        self.txt_end_time = JTextField()

        JScrollPane1 = JScrollPane()
        self.lst_product = JList()
        self.lst_product = JList(self.jlist_products, valueChanged = self.choose_product)
        
        JScrollPane2 = JScrollPane()
        self.lst_watershed = JList()
        self.lst_watershed = JList(self.jlist_basins, valueChanged = self.choose_watershed)

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)
        self.setTitle("Cumulus CAVI UI")
        self.setLocation(Point(10, 10))
        self.setLocationByPlatform(True)
        self.setName("CumulusCaviUi")
        self.setResizable(False)

        btn_submit.setFont(Font("Tahoma", 0, 18))
        btn_submit.setText("Submit")
        btn_submit.actionPerformed = self.submit

        lbl_start_date.setText("Start Date/Time")

        lbl_end_date.setText("End Date/Time")

        self.txt_select_file.setToolTipText("FQPN to output file (.dss)")

        btn_select_file.setText("...")
        btn_select_file.setToolTipText("Select File...")
        btn_select_file.actionPerformed = self.select_file

        lbl_origin.setText("Minimum (x,y):")

        lbl_extent.setText("Maximum (x,y):")

        self.txt_originx.setToolTipText("Minimum X")

        self.txt_originy.setToolTipText("Minimum Y")

        self.txt_extentx.setToolTipText("Maximum X")

        self.txt_extenty.setToolTipText("Maximum Y")

        lbl_select_file.setText("Output File Location")

        comma1.setFont(Font("Tahoma", 0, 12))
        comma1.setText(",")

        comma2.setFont(Font("Tahoma", 0, 12))
        comma2.setText(",")

        paren_l1.setText("(")

        paren_l2.setText("(")

        paren_r1.setText(")")

        paren_r2.setText(")")

        self.txt_start_time.setToolTipText("Start Time")
        self.txt_end_time.setToolTipText("End Time")

        self.lst_product.setBorder(BorderFactory.createTitledBorder(None, "Available Products", TitledBorder.CENTER, TitledBorder.TOP, Font("Tahoma", 0, 14)))
        self.lst_product.setFont(Font("Tahoma", 0, 14))
        JScrollPane1.setViewportView(self.lst_product)
        self.lst_product.getAccessibleContext().setAccessibleName("Available Products")
        self.lst_product.getAccessibleContext().setAccessibleParent(JScrollPane2)

        self.lst_watershed.setBorder(BorderFactory.createTitledBorder(None, "Available Watersheds", TitledBorder.CENTER, TitledBorder.TOP, Font("Tahoma", 0, 14)))
        self.lst_watershed.setFont(Font("Tahoma", 0, 14))
        self.lst_watershed.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        JScrollPane2.setViewportView(self.lst_watershed)

        layout = GroupLayout(self.getContentPane())
        self.getContentPane().setLayout(layout)
        layout.setHorizontalGroup(
            layout.createParallelGroup(GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING, False)
                    .addComponent(lbl_select_file)
                    .addComponent(JScrollPane1)
                    .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                        .addComponent(paren_l1)
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                            .addComponent(lbl_origin)
                            .addGroup(layout.createSequentialGroup()
                                .addComponent(self.txt_originx, GroupLayout.PREFERRED_SIZE, 65, GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(comma1, GroupLayout.PREFERRED_SIZE, 5, GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.txt_originy, GroupLayout.PREFERRED_SIZE, 65, GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(paren_r1)))
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .addComponent(paren_l2)
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                            .addComponent(lbl_extent)
                            .addGroup(layout.createSequentialGroup()
                                .addComponent(self.txt_extentx, GroupLayout.PREFERRED_SIZE, 65, GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(comma2)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.txt_extenty, GroupLayout.PREFERRED_SIZE, 65, GroupLayout.PREFERRED_SIZE)
                                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(paren_r2))))
                    .addComponent(JScrollPane2)
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                            .addComponent(btn_submit)
                            .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, 377, GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(btn_select_file))
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                            .addComponent(lbl_start_date)
                            .addComponent(self.txt_start_time, GroupLayout.PREFERRED_SIZE, 140, GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                            .addGroup(layout.createSequentialGroup()
                                .addComponent(lbl_end_date)
                                .addGap(70, 70, 70))
                            .addComponent(self.txt_end_time, GroupLayout.Alignment.LEADING, GroupLayout.PREFERRED_SIZE, 140, GroupLayout.PREFERRED_SIZE))))
                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        )
        layout.setVerticalGroup(
            layout.createParallelGroup(GroupLayout.Alignment.LEADING)
            .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                .addGap(25, 25, 25)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                    .addComponent(lbl_start_date)
                    .addComponent(lbl_end_date))
                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                    .addComponent(self.txt_start_time, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addComponent(self.txt_end_time, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                .addGap(18, 18, 18)
                .addComponent(JScrollPane2, GroupLayout.PREFERRED_SIZE, 201, GroupLayout.PREFERRED_SIZE)
                .addGap(18, 18, 18)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING, False)
                    .addGroup(layout.createSequentialGroup()
                        .addComponent(lbl_extent)
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                            .addComponent(self.txt_extentx, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                            .addComponent(self.txt_extenty, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                            .addComponent(comma2)
                            .addComponent(paren_l2)
                            .addComponent(paren_r2)))
                    .addGroup(layout.createSequentialGroup()
                        .addComponent(lbl_origin)
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                            .addComponent(self.txt_originx, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                            .addComponent(self.txt_originy, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                            .addComponent(comma1)
                            .addComponent(paren_l1)
                            .addComponent(paren_r1))))
                .addGap(39, 39, 39)
                .addComponent(JScrollPane1, GroupLayout.PREFERRED_SIZE, 201, GroupLayout.PREFERRED_SIZE)
                .addGap(18, 18, Short.MAX_VALUE)
                .addComponent(lbl_select_file)
                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                    .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addComponent(btn_select_file))
                .addGap(18, 18, 18)
                .addComponent(btn_submit)
                .addContainerGap())
        )
        self.txt_select_file.setText(self.dss_path)
        self.txt_start_time.setText(self.start_time)
        self.txt_end_time.setText(self.end_time)

        self.pack()
        self.setLocationRelativeTo(None)

    def http_get(self, url):
        '''Return java.lang.String JSON
        
        Input: java.lang.String URL
        '''
        try:
            url = URL(url)
            urlconnect = url.openConnection()
            br = BufferedReader(
                InputStreamReader(
                    urlconnect.getInputStream(), "UTF-8"
                )
            )
            s = br.readLine()
            br.close()
        except MalformedURLException() as ex:
            MessageBox.showError(ex, "Exception")
            raise Exception(ex)
        except IOException as ex:
            MessageBox.showError(ex, "Exception")
            raise Exception(ex)
        return s

    def http_post(self, json_string, url):
        '''Return java.lang.String JSON

        Input: java.lang.String JSON, java.lang.String URL
        '''
        try:
            # Get a connection and set the request properties
            url = URL(url)
            urlconnect = url.openConnection()
            urlconnect.setDoOutput(True)
            urlconnect.setRequestMethod("POST")
            urlconnect.setRequestProperty("Content-Type", "application/json; UTF-8")
            urlconnect.setRequestProperty("Accept", "application/json")
            # Write to the body
            bw = BufferedWriter(
                OutputStreamWriter(
                    urlconnect.getOutputStream()
                )
            )
            bw.write(json_string)
            bw.flush()
            bw.close()
            # Read the result from the POST
            br = BufferedReader(
                InputStreamReader(
                    urlconnect.getInputStream(), "UTF-8"
                )
            )
            s = br.readLine()
            br.close()
        except MalformedURLException() as ex:
            MessageBox.showError(ex, "Exception")
            raise Exception(ex)
        except IOException as ex:
            MessageBox.showError(ex, "Exception")
            raise Exception(ex)
        return s

    def json_build(self):
        '''Return JSON string or 'None' if failed

        The returning JSON string is from the UI and used when POSTing to the
        Cumulus API.
        '''
        conf = {
            'datetime_start': None,
            'datetime_end': None,
            'basin_id': None,
            'product_id': None,
            }

        try:
            tf = TimeFormatter()
            tz = tf.zid
            st = tf.parse_zoned_date_time(self.txt_start_time.getText(), tz)
            et = tf.parse_zoned_date_time(self.txt_end_time.getText(), tz)

            conf['datetime_start'] = st.format(tf.iso_instant())
            conf['datetime_end'] = et.format(tf.iso_instant())
        except DateTimeParseException as ex:
            MessageBox.showWarning(ex, "Exception")


        selected_watershed = self.lst_watershed.getSelectedValue()
        selected_products = self.lst_product.getSelectedValues()

        if selected_watershed is not None:
            watershed_id = self.basin_meta[selected_watershed]['id']
            conf['basin_id'] = watershed_id
        else:
            MessageBox.showWarning(
                "No Watershed Selected",
                "Exception"
                )
            return None
        
        product_ids = list()
        if len(selected_products) > 0:
            for p in selected_products:
                product_ids.append(self.product_meta[p]['id'])
                conf['product_id'] = product_ids
        else:
            MessageBox.showWarning(
                "No Products Selected",
                "Exception"
                )
            return None

        return json.dumps(conf)

    def choose_product(self, event):
        '''The event here is a javax.swing.event.ListSelectionEvent because
        it comes from a Jlist.  Use getValueIsAdjusting() to only get the
        mouse up value.
        '''
        index = self.lst_product.selectedIndex
        if not event.getValueIsAdjusting():
            pass
            # print(self.product_meta[self.lst_product.getSelectedValues()])

    def choose_watershed(self, event):
        '''The event here is a javax.swing.event.ListSelectionEvent because
        it comes from a Jlist.  Use getValueIsAdjusting() to only get the
        mouse up value.
        '''
        index = self.lst_watershed.selectedIndex
        if not event.getValueIsAdjusting():
            _dict = self.basin_meta[self.lst_watershed.getSelectedValue()]
            self.txt_originx.setText(str(_dict['x_min']))
            self.txt_originy.setText(str(_dict['y_min']))
            self.txt_extentx.setText(str(_dict['x_max']))
            self.txt_extenty.setText(str(_dict['y_max']))

    def select_file(self, event):
        '''Provide the user a JFileChooser to select the DSS file data is to download to.

        Event is a java.awt.event.ActionEvent
        '''
        fc = FileChooser(self.txt_select_file)
        fc.title = "Select Output DSS File"
        _dir = os.path.dirname(self.dss_path)
        fc.set_current_dir(File(_dir))
        fc.show()

    def submit(self, event):
        '''Collect user inputs and initiate download of DSS files to process.

        Event is a java.awt.event.ActionEvent
        '''
        # Build the JSON from the UI inputs and POST if we have JSON
        json_string = self.json_build()

        if json_string is not None:
            post_result = self.http_post(json_string, url_downloads)
            json_post_result = json.loads(post_result)
            id = json_post_result['id']
            timeout = 0
            while timeout < max_timeout:
                get_result = self.http_get("/".join([url_downloads, id]))
                if get_result is not None:
                    json_get_result = json.loads(get_result)
                    progress = json_get_result['progress']                          #100%
                    stat = json_get_result['status']                                #SUCCESS
                    fname = json_get_result['file']                                 # not null

                    print("Status: {}".format(stat))

                    if stat == 'FAILED':
                        MessageBox.showError(
                            "Failed to load grid products.",
                            "Failed Download"
                            )
                        break

                    if int(progress) == 100 and stat == 'SUCCESS':                  # May add file check to make sure not None
                        source_dssfile = self.txt_select_file.getText()
                        downloaded_dssfile = download_dss(fname)
                        if downloaded_dssfile is not None:
                            print("DSS file downloaded.")
                            merged_dssfile = merge_dss(downloaded_dssfile, source_dssfile)
                            if merged_dssfile:
                                MessageBox.showInformation(
                                    "DSS file downloaded and merged to:\n{}".format(source_dssfile),
                                    "Successful Processing"
                                )
                            else:
                                MessageBox.showWarning(
                                    "DSS file merge unsuccessful",
                                    "Unsuccessful Merge"
                                )
                        else:
                            MessageBox.showError(
                                "Downloading and processing the DSS file failed!",
                                "Failed Processing"
                                )
                        break
                    else:
                        Thread.sleep(1000)
                    timeout += 1

def main():
    ''' The main section to determine is the script is executed within or
    outside of the CAVI environment
    '''
    if cavi_env:                                                                # This is all the stuff to do if in the CAVI
        script_name = "{}.py".format(arg2)
        tw = cavistatus.get_timewindow()
        if tw == None:
        	raise Exception("No forecast open on Modeling tab to get a timewindow.")
        db = os.path.join(cavistatus.get_database_directory(), "grid.dss")
        cwms_home = cavistatus.get_working_dir()
        common_exe = os.path.join(os.path.split(cwms_home)[0], "common", "exe")
        cumulus_config = os.path.join(os.getenv("APPDATA"), "cumulus.config")
        this_script = os.path.join(cavistatus.get_project_directory(), "scripts", script_name)
        cmd = "@PUSHD {pushd}\n"
        cmd += "Jython.bat {script} "
        cmd += '"{start}" "{end}" "{dss}" "{home}" "{config}"'
        cmd = cmd.format(pushd=common_exe, script=this_script, start=tw[0],
            end=tw[1], dss=db, home=cwms_home, config=cumulus_config
            )
        print(cmd)
        # Create a temporary file that will be executed outside the CAVI env
        batfile = tempfile.NamedTemporaryFile(mode='w+b', suffix='.cmd', delete=False)
        batfile.write(cmd)
        batfile.close()
        p = subprocess.Popen(batfile.name, shell=True)
        # os.remove(batfile.name)
    else:                                                                       # This is all the stuff to do if initiated outside the CAVI environment
        args = sys.argv[1:]
        if len(args) < 5:
            MessageBox.showPlain(
                "Expecting five arguments.  {} arguments given".format(len(args)),
                "Exception"
                )
            raise Exception("Need more arguments")
        keys = ['start_time', 'end_time', 'dss_path', 'cwms_home', 'config']
        ordered_dict = dict(zip(keys, args))

        # Set the look and feel
        # Metal, Nimbus, CDE/Motif, Windows, or Windows Classic
        LookAndFeel("Nimbus")

        cui = CumulusUI(ordered_dict)
        cui.setVisible(True)

if __name__ == "__main__":
    # DELETE THIS LIST.  ONLY FOR TESTING
    sys.argv[1:] = ["22SEP2020, 12:00", "22SEP2020, 13:00", "D:/WS_CWMS/lrn-m3000-v31-pro/database/grid.dss", "C:/app/CWMS/CWMS-Production/CAVI", "C:/Users/h3ecxjsg/AppData/Roaming/cumulus.config"]
    # DELETE THIS LIST.  ONLY FOR TESTING
    main()