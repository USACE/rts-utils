# Java
from java.lang import String, Short, Thread, System
from java.net import URL, MalformedURLException
from java.time import ZoneId, LocalDateTime, ZonedDateTime
from java.time.format import DateTimeFormatterBuilder, DateTimeFormatter, DateTimeParseException
from java.io import BufferedReader, BufferedWriter
from java.io import InputStreamReader, OutputStreamWriter
from java.io import File, IOException
from java.nio.file import Files, StandardCopyOption, FileSystemException
from java.awt import Font, Point

from javax.swing import UIManager
from javax.swing import JFrame, JButton, JLabel, JTextField, JList, JCheckBox
from javax.swing import JScrollPane, JFileChooser
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing.border import TitledBorder
from javax.swing.filechooser import FileNameExtensionFilter
# HEC
from hec.script import Constants, MessageBox
from hec.heclib.util import Heclib, HecTime
from hec.heclib.dss import HecDss, DSSPathname
from hec.heclib.grid import GridUtilities, GriddedData, GridInfo, SpecifiedGridInfo
from hec.hecmath import DSSFileException
# Python
import os
import sys
import json
import math
import tempfile
import subprocess
import logging
import logging.handlers
#
True = Constants.TRUE
False = Constants.FALSE
APPDATA = os.getenv("APPDATA")
# Max timeout for downloading dss files in seconds.
max_timeout = 600
# List of URLs used in the script
url_basins = "https://api.rsgis.dev/development/cumulus/basins"
url_products = "https://api.rsgis.dev/development/cumulus/products"
url_downloads = "https://api.rsgis.dev/development/cumulus/downloads"
#

# Add some logging but check to see if it already exists because we are running in the CAVI
# if not "cumulus_logger" in dir():
log_filename = os.path.join(APPDATA, "cumulus_rts_ui.log")
cumulus_logger = logging.Logger("Cumulus UI Log")
cumulus_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s.%(msecs)03d - ' +
    '%(name)s:%(funcName)15s - %(levelname)-5s - %(message)s',
    '%Y-%m-%dT%H:%M:%S')
# Console Handler
ch = logging.StreamHandler()
ch.setFormatter(formatter)
cumulus_logger.addHandler(ch)

# File logger
try:
    fh = logging.handlers.RotatingFileHandler(log_filename, maxBytes=5000000,
        backupCount=1)
    fh.setFormatter(formatter)
    cumulus_logger.addHandler(fh)
    cumulus_logger.info('Logging file set to: {}'.format(log_filename))
except IOError as ex:
    cumulus_logger.warning(ex)
    cumulus_logger.warning('Rotating File Handler not created.')

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
    cumulus_logger.warning(str(ex) + ", which means running outside of CAVI")
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
        with open(os.path.join(APPDATA, self.config_filename), 'w') as f:
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

# Define something to download the DSS and process
def download_dss(dss_url):
    '''
    Return java.nio.file.Path temp_dssfile

    Inputs: java.lang.String DSS URI
    DSS file downloaded to user's temporary directory as to not clober any existing
    DSS file and all records written to DSS OUT Path.
    '''
    start_timer = System.currentTimeMillis()
    # Heclib.zset('DSSV', '', 7)
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
    except IOException as ex:
        # MessageBox.showError(str(ex), "Exception")
        raise

    end_timer = System.currentTimeMillis()
    cumulus_logger.debug(
        "DSS Download (milliseconds): {}".format(
            (end_timer - start_timer)
        )
    )

    return result

def merge_dss(src_dss, dest_dss, cwms_name=False, *coords):
    '''
    Return list containing FQPN of DSS files

    Input: java.nio.file.Path src_path java.lang.String dest_path
    Merge all grid paths in the source dss file into the destination dss file
    '''
    start_timer = System.currentTimeMillis()
    def cwms_dssname(pn):
        '''Return FQPN to CWMS naming dss file
        Input: java.lang.String source_directory java.lang.String DSSPathname
        '''
        dsspn = DSSPathname(pn)
        dpart = dsspn.dPart()
        dpart_date, dpart_time = dpart.split(":")
        cpart = String(dsspn.cPart().split("-")[0]).toLowerCase()
        # dt = TimeFormatter().parse_local_date_time(dpart)
        dt = HecTime(dpart_date, dpart_time, HecTime.MINUTE_GRANULARITY)
        new_filename = "{p}.{y}.{m:02}.dss".format(
            p=cpart,
            y=dt.year(),
            m=dt.month())
        
        return new_filename

    dssin = dssout = None
    oi, oj, ei, ej = coords
    origin_factor = lambda x, y: int(math.floor(x / y))
    merged_paths = list()
    # Process the DSS file
    if Files.exists(src_dss):
        try:
            dssin = HecDss.open(src_dss.toString(), False, False, 7)
            dssout = HecDss.open(dest_dss, False, False, 6)
            for pathname in dssin.getCatalogedPathnames(True):
                if cwms_name:
                    dest_dss = os.path.join(os.path.dirname(dest_dss), cwms_dssname(pathname))
                grid_container = dssin.get(pathname)
                grid_info = grid_container.getGridInfo()
                grid_info.setCellInfo(
                    origin_factor(oi, grid_info.getCellSize()),
                    origin_factor(oj, grid_info.getCellSize()),
                    grid_info.getNumberOfCellsX(),
                    grid_info.getNumberOfCellsY(),
                    grid_info.getCellSize()
                )
                dssout.put(grid_container)
                # GridUtilities.storeGridToDss(dest_dss, pathname, grid_data)
                if dest_dss not in merged_paths: merged_paths.append(dest_dss)

            # else:
                # dssin.copyRecordsFrom(dest_dss, dssin.getCatalogedPathnames(True))
                # merged_paths.append(dest_dss)

        except DSSFileException as ex:
            # MessageBox.showError(str(ex), "Exception")
            cumulus_logger.error(str(ex))
            raise
        except Exception as ex:
            cumulus_logger.error(str(ex))
            # MessageBox.showError(str(ex), "Exception")
            raise
        finally:
            if dssin:
                dssin.done()
                dssin.close()
            if dssout:
                dssout.done()
                dssout.close()
            try:
                Files.deleteIfExists(src_dss)
                cumulus_logger.debug(
                    "Deleteing the source DSS file: {}".format(src_dss))
            except FileSystemException as ex:
                # MessageBox.showError(str(ex), "Exception")
                cumulus_logger.error(str(ex))
                raise
    
    end_timer = System.currentTimeMillis()
    cumulus_logger.debug(
        "Merging DSS records (milliseconds): {}".format(
            (end_timer - start_timer)
        )
    )

    return merged_paths

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
            with open(os.path.join(APPDATA, "cumulus.config")) as f:
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
        lbl_select_file = JLabel()

        self.txt_start_time = JTextField()
        self.txt_end_time = JTextField()

        jScrollPane1 = JScrollPane()
        self.lst_product = JList()
        self.lst_product = JList(self.jlist_products, valueChanged = self.choose_product)
        
        jScrollPane2 = JScrollPane()
        self.lst_watershed = JList()
        self.lst_watershed = JList(self.jlist_basins, valueChanged = self.choose_watershed)

        self.cwms_dssname = JCheckBox()

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

        lbl_select_file.setText("Output File Location")

        self.txt_start_time.setToolTipText("Start Time")
        self.txt_end_time.setToolTipText("End Time")

        self.lst_product.setBorder(BorderFactory.createTitledBorder(None, "Available Products", TitledBorder.CENTER, TitledBorder.TOP, Font("Tahoma", 0, 14)))
        self.lst_product.setFont(Font("Tahoma", 0, 14))
        jScrollPane1.setViewportView(self.lst_product)
        self.lst_product.getAccessibleContext().setAccessibleName("Available Products")
        self.lst_product.getAccessibleContext().setAccessibleParent(jScrollPane2)

        self.lst_watershed.setBorder(BorderFactory.createTitledBorder(None, "Available Watersheds", TitledBorder.CENTER, TitledBorder.TOP, Font("Tahoma", 0, 14)))
        self.lst_watershed.setFont(Font("Tahoma", 0, 14))
        self.lst_watershed.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        jScrollPane2.setViewportView(self.lst_watershed)

        self.cwms_dssname.setText("CWMS DSS filename")
        self.cwms_dssname.setToolTipText("Parameter.yyyy.mm.dss")
        self.cwms_dssname.setVisible(False)

        layout = GroupLayout(self.getContentPane());
        self.getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING, False)
                    .addComponent(lbl_select_file)
                    .addComponent(jScrollPane1)
                    .addComponent(jScrollPane2)
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.TRAILING)
                            .addComponent(btn_submit)
                            .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, 377, GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(btn_select_file))
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                            .addComponent(lbl_start_date)
                            .addComponent(self.txt_start_time, GroupLayout.PREFERRED_SIZE, 170, GroupLayout.PREFERRED_SIZE))
                        .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                        .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                            .addComponent(self.txt_end_time, GroupLayout.PREFERRED_SIZE, 170, GroupLayout.PREFERRED_SIZE)
                            .addComponent(lbl_end_date))))
                .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
        )
        layout.setVerticalGroup(
            layout.createParallelGroup(GroupLayout.Alignment.LEADING)
            .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                .addGap(25, 25, 25)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                    .addComponent(lbl_start_date)
                    .addComponent(lbl_end_date))
                .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                    .addComponent(self.txt_start_time, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addComponent(self.txt_end_time, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                .addGap(18, 18, 18)
                .addComponent(jScrollPane2, GroupLayout.PREFERRED_SIZE, 201, GroupLayout.PREFERRED_SIZE)
                .addGap(18, 18, 18)
                .addComponent(jScrollPane1, GroupLayout.PREFERRED_SIZE, 201, GroupLayout.PREFERRED_SIZE)
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
        start_timer = System.currentTimeMillis()
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
            cumulus_logger.error(str(ex))
            MessageBox.showError(str(ex), "Exception")
            raise
        except IOException as ex:
            cumulus_logger.error(str(ex))
            MessageBox.showError(str(ex), "Exception")
            raise
        end_timer = System.currentTimeMillis()
        cumulus_logger.debug(
            "HTTP GET (milliseconds): {}".format(
                (end_timer - start_timer)
                )
        )

        return s

    def http_post(self, json_string, url):
        '''Return java.lang.String JSON

        Input: java.lang.String JSON, java.lang.String URL
        '''
        start_timer = System.currentTimeMillis()

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
            cumulus_logger.error(str(ex))
            MessageBox.showError(str(ex), "Exception")
            raise Exception(ex)
        except IOException as ex:
            cumulus_logger.error(str(ex))
            MessageBox.showError(str(ex), "Exception")
            raise Exception(ex)

        end_timer = System.currentTimeMillis()
        cumulus_logger.debug(
            "HTTP GET (milliseconds): {}".format(
                (end_timer - start_timer)
                )
        )

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
        output_str = '''{name}
After: {after}
Before: {before}
Parameter: {para}
Unit: {u}
'''
        index = self.lst_product.selectedIndex
        if not event.getValueIsAdjusting():
            pnames = self.lst_product.getSelectedValues()
            for pname in pnames:
                cumulus_logger.info("~" * 50)
                cumulus_logger.info("Product: {}".format(pname))
                cumulus_logger.info(
                    "After time: {}".format(self.product_meta[pname]['after']))
                cumulus_logger.info(
                    "Before time: {}".format(self.product_meta[pname]['before']))
                cumulus_logger.info(
                    "Parameter: {}".format(self.product_meta[pname]['parameter']))
                cumulus_logger.info(
                    "unit: {}".format(self.product_meta[pname]['unit']))

    def choose_watershed(self, event):
        '''The event here is a javax.swing.event.ListSelectionEvent because
        it comes from a Jlist.  Use getValueIsAdjusting() to only get the
        mouse up value.
        '''
        index = self.lst_watershed.selectedIndex
        if not event.getValueIsAdjusting():
            _dict = self.basin_meta[self.lst_watershed.getSelectedValue()]

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

        start_timer = end_timer = System.currentTimeMillis()
        # Build the JSON from the UI inputs and POST if we have JSON
        json_string = self.json_build()
        cumulus_logger.debug("JSON String Builder: {}".format(json_string))

        # Get the watershed's coordinates
        selected_watershed = self.lst_watershed.getSelectedValue()
        coords = list()
        if selected_watershed is not None:
            coords.append(self.basin_meta[selected_watershed]['x_min'])
            coords.append(self.basin_meta[selected_watershed]['y_min'])
            coords.append(self.basin_meta[selected_watershed]['x_max'])
            coords.append(self.basin_meta[selected_watershed]['y_max'])

        if json_string is not None:
            cumulus_logger.info("*" * 50)
            cumulus_logger.info("Initiated Cumulus Product Request")
            cumulus_logger.info("*" * 50)
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

                    cumulus_logger.info("Status: {:>10} Filename: {} Progress: {:>3}% Timeout: {:>4}".format(stat, fname, progress, timeout))

                    if stat == 'FAILED':
                        cumulus_logger.error("Failed to load grid products.")
                        MessageBox.showError(
                            "Failed to load grid products.",
                            "Failed Download"
                            )
                        break

                    if int(progress) == 100 and stat == 'SUCCESS' and fname is not None:
                        dest_dssfile = self.txt_select_file.getText()
                        cwmsdss_naming = self.cwms_dssname.isSelected()
                        downloaded_dssfile = download_dss(fname)
                        if downloaded_dssfile is not None:
                            cumulus_logger.info("DSS file downloaded.")
                            merged_dssfiles = merge_dss(downloaded_dssfile, dest_dssfile, cwmsdss_naming, *coords)
                            if len(merged_dssfiles) > 0:
                                end_timer = System.currentTimeMillis()

                                msg = "DSS file downloaded and merged to: {}".format(
                                        '\n'.join([f for f in merged_dssfiles])
                                        )
                                cumulus_logger.info(msg)
                                MessageBox.showInformation(msg,
                                    "Successful Processing"
                                )
                            else:
                                msg = "DSS file merge unsuccessful"
                                cumulus_logger.warning(msg)
                                MessageBox.showWarning(msg,
                                    "Unsuccessful Merge"
                                )
                        else:
                            msg = "Downloading and processing the DSS file failed!"
                            cumulus_logger.error(msg)
                            MessageBox.showError(msg,
                                "Failed Processing"
                                )
                        break
                    else:
                        Thread.sleep(1000)
                    timeout += 1

            cumulus_logger. info(
                "Submit time duration (milliseconds): {}".format(
                    (end_timer - start_timer)
                )
            )
                                

def main():
    ''' The main section to determine is the script is executed within or
    outside of the CAVI environment
    '''
    if cavi_env:                                                                # This is all the stuff to do if in the CAVI
        script_name = "{}.py".format(arg2)
        tw = cavistatus.get_timewindow()
        if tw == None:
            msg = "No forecast open on Modeling tab to get a timewindow."
            cumulus_logger.warning(msg)
            raise Exception(msg)
        db = os.path.join(cavistatus.get_database_directory(), "grid.dss")
        cwms_home = cavistatus.get_working_dir()
        common_exe = os.path.join(os.path.split(cwms_home)[0], "common", "exe")

        cumulus_logger.debug("DSS file default: {}".format(db))
        cumulus_logger.debug("CWMS working directory: {}".format(cwms_home))
        cumulus_logger.debug("Jython execution directory: {}".format(common_exe))
        
        cumulus_config = os.path.join(APPDATA, "cumulus.config")
        this_script = os.path.join(cavistatus.get_project_directory(), "scripts", script_name)
        cmd = "@PUSHD {pushd}\n"
        cmd += "Jython.bat {script} "
        cmd += '"{start}" "{end}" "{dss}" "{home}" "{config}"'
        cmd = cmd.format(pushd=common_exe, script=this_script, start=tw[0],
            end=tw[1], dss=db, home=cwms_home, config=cumulus_config
            )
        # Create a temporary file that will be executed outside the CAVI env
        batfile = tempfile.NamedTemporaryFile(mode='w', suffix='.cmd', delete=False)
        batfile.write(cmd)
        batfile.close()
        cumulus_logger.info("Initiated Subprocess")
        p = subprocess.Popen("start cmd /C " + batfile.name, shell=True)
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
    sys.argv[1:] = ["26NOV2020, 00:00", "26NOV2020, 23:00", "D:/WS_CWMS/lrn-m3000-v32-dev/database/grid.dss", "C:/app/CWMS/CWMS-v3.2.1.132/CAVI", "C:/Users/h3ecxjsg/AppData/Roaming/cumulus.config"]
    # DELETE THIS LIST.  ONLY FOR TESTING

    main()