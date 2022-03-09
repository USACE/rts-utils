"""Java Swing UI for Water API extracting time series
"""

import copy
import json
import os
from collections import OrderedDict, namedtuple
from functools import partial

from hec.heclib.dss import HecDss
from hec.heclib.util import HecTime
from hec.hecmath import TimeSeriesMath
from hec.hecmath.functions import TimeSeriesFunctions
from hec.io import TimeSeriesContainer
from hec.lang import TimeStep
from java.awt import Font, Point
from java.lang import Short
from javax.swing import (
    BorderFactory,
    GroupLayout,
    ImageIcon,
    JButton,
    JCheckBox,
    JFrame,
    JLabel,
    JList,
    JOptionPane,
    JScrollPane,
    JTextField,
    LayoutStyle,
    ListSelectionModel,
    SwingConstants,
)
from rtsutils import FALSE, TRUE, go, null
from rtsutils.cavi.jython import jutil
from rtsutils.usgs import USGS_EXTRACT_CODES
from rtsutils.utils import EXTRACT_ICON
from rtsutils.utils.config import DictConfig


DSSVERSION = 6


def put_ts(site, dss, apart):
    """Save timeseries to DSS File

    exception handled with a message output saying site not saved, but
    continues on trying additional site/parameter combinations

    Parameters
    ----------
    site: json
        JSON object containing meta data about the site/parameter combination,
        time array and value array
    dss: HecDss DSS file object
        The open DSS file records are written to
    Returns
    -------
    None

    Raises
    ------
    HEC DSS exception
    """

    site_parameters = namedtuple("site_parameters", site.keys())(**site)
    parameter, unit, data_type, version = USGS_EXTRACT_CODES[site_parameters.code]
    times = [
        HecTime(t, HecTime.MINUTE_GRANULARITY).value() for t in site_parameters.times
    ]

    timestep_min = None
    for t_time in range(len(times) - 1):
        time_step = abs(times[t_time + 1] - times[t_time])
        if time_step < timestep_min or timestep_min is None:
            timestep_min = time_step
    epart = TimeStep().getEPartFromIntervalMinutes(timestep_min)
    # Set the pathname
    pathname = "/{0}/{1}/{2}//{3}/{4}/".format(
        apart, site_parameters.site_number, parameter, epart, version
    ).upper()
    # apart, bpart, cpart, _, _, fpart = pathname.split('/')[1:-1]

    container = TimeSeriesContainer()
    container.fullName = pathname
    container.location = apart
    container.parameter = parameter
    container.type = data_type
    container.version = version
    container.interval = timestep_min
    container.units = unit
    container.times = times
    container.values = site_parameters.values
    container.numberValues = len(site_parameters.times)
    container.startTime = times[0]
    container.endTime = times[-1]
    container.timeZoneID = "UTC"
    # container.makeAscending()
    if not TimeSeriesMath.checkTimeSeries(container):
        return 'site_parameters: "{}" not saved to DSS'.format(
            site_parameters.site_number
        )
    tsc = TimeSeriesFunctions.snapToRegularInterval(
        container, epart, "0MIN", "0MIN", "0MIN"
    )
    # Put the data to DSS
    try:
        dss.put(tsc)
    except Exception as ex:
        print(ex)
        return "site_parameters: '{}' not saved to DSS".format(
            site_parameters.site_number
        )


class WaterExtractUI:
    """Java Swing for Water Extract configurations"""

    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    @classmethod
    def show(cls):
        """set UI visible true"""
        cls.user_interface = cls.UI()
        cls.user_interface.setVisible(TRUE)

    @classmethod
    def execute(cls):
        """executing the Go binding as a subprocess"""

        configurations = DictConfig(cls.config_path).read()
        go_config = copy.deepcopy(cls.go_config)

        go_config["Subcommand"] = "extract"
        go_config["Slug"] = configurations["watershed_slug"]
        go_config["Endpoint"] = "watersheds/{}/extract".format(
            configurations["watershed_slug"]
        )

        sub = go.get(out_err=FALSE, is_shell=FALSE)
        sub.stdin.write(json.dumps(go_config))
        sub.stdin.close()
        dsspath = configurations["dss"]
        dss = HecDss.open(dsspath)

        byte_array = bytearray()
        for iter_byte in iter(partial(sub.stdout.read, 1), b""):
            byte_array.append(iter_byte)
            if iter_byte == "}":
                obj = json.loads(str(byte_array))
                byte_array = bytearray()
                if "message" in obj.keys():
                    JOptionPane.showMessageDialog(
                        None,
                        obj["message"],
                        "Missing Configuration File",
                        JOptionPane.ERROR_MESSAGE,
                    )

                msg = put_ts(obj, dss, configurations["apart"])
                if msg:
                    print(msg)

        if dss:
            dss.done()

        std_err = sub.stderr.read()
        sub.stderr.close()
        sub.stdout.close()
        if "error" in std_err:
            print(std_err)
            JOptionPane.showMessageDialog(
                None,
                std_err.split("::")[-1],
                "Program Error",
                JOptionPane.INFORMATION_MESSAGE,
            )

        print(std_err)
        JOptionPane.showMessageDialog(
            None,
            "Program Done",
            "Program Done",
            JOptionPane.INFORMATION_MESSAGE,
        )

    @classmethod
    def set_config_file(cls, cfg):
        """Set the cumulus configuration file"""
        cls.config_path = cfg

    @classmethod
    def parameters(cls, dict_):
        """update Go parameters

        Parameters
        ----------
        dict_ : dict
            Go parameters to update class defined configurations
        """
        cls.go_config.update(dict_)

    class UI(JFrame):
        """Java Swing JFrame

        Parameters
        ----------
        JFrame : Java Swing JFrame
            JFrame used to define the GUI
        """

        def __init__(self):
            super(WaterExtractUI.UI, self).__init__()
            self.outer_class = WaterExtractUI()

            if self.outer_class.config_path is None:
                JOptionPane.showMessageDialog(
                    None,
                    "No configuration file path provided\n\nExiting program",
                    "Missing Configuration File",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.config_path = self.outer_class.config_path
            go_config = copy.deepcopy(self.outer_class.go_config)

            self.configurations = DictConfig(self.config_path).read()

            go_config["Endpoint"] = "watersheds"
            ws_out, stderr = go.get(go_config, out_err=TRUE, is_shell=FALSE)
            if "error" in stderr:
                print(stderr)
                JOptionPane.showMessageDialog(
                    None,
                    stderr.split("::")[-1],
                    "Missing Configuration File",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.api_watersheds = self.watershed_refactor(json.loads(ws_out))

            #
            # ~~~~~~~~~~~~ START OF THE JAVA PANE ~~~~~~~~~~~~
            #
            jScrollPane1 = JScrollPane()
            self.lst_watersheds = JList()
            lbl_select_file = JLabel()
            self.txt_select_file = JTextField()
            btn_select = JButton()
            btn_execute = JButton()
            self.cbx_apart = JCheckBox()
            self.txt_apart = JTextField()
            btn_save = JButton()
            btn_close = JButton()

            # self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE)
            self.setTitle("Extract Time Series Configuration")
            self.setAlwaysOnTop(FALSE)
            self.setIconImage(ImageIcon(EXTRACT_ICON).getImage())
            self.setLocation(Point(10, 10))
            self.setLocationByPlatform(TRUE)
            self.setName("WaterExtractUI")
            self.setResizable(FALSE)

            self.lst_watersheds = JList(
                sorted(self.api_watersheds.keys()), valueChanged=self.watersheds
            )
            self.lst_watersheds.setBorder(
                BorderFactory.createTitledBorder(
                    null, "Watersheds", 2, 2, Font("Tahoma", 0, 14)
                )
            )
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14))
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
            jScrollPane1.setViewportView(self.lst_watersheds)

            lbl_select_file.setFont(Font("Tahoma", 0, 14))
            lbl_select_file.setText("DSS File Downloads")

            self.txt_select_file.setFont(Font("Tahoma", 0, 18))
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)")

            btn_select.setFont(Font("Tahoma", 0, 18))
            btn_select.setText("...")
            btn_select.setToolTipText("Select File...")
            btn_select.actionPerformed = self.select_file

            btn_execute.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_execute.setText("Save and Execute Configuration")
            btn_execute.setToolTipText("Save and Execute Configuration")
            btn_execute.setHorizontalTextPosition(SwingConstants.CENTER)
            btn_execute.actionPerformed = self.execute

            btn_save.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_save.setText("Save Configuration")
            btn_save.setToolTipText("Save Configuration")
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER)
            btn_save.actionPerformed = self.save

            btn_close.setFont(Font("Tahoma", 0, 14))
            btn_close.setText("Close")
            btn_close.setToolTipText("Close GUI")
            btn_close.setHorizontalTextPosition(SwingConstants.CENTER)
            btn_close.actionPerformed = self.close

            self.cbx_apart.setFont(Font("Tahoma", 0, 14))
            self.cbx_apart.setText("DSS A part")
            self.cbx_apart.setToolTipText("DSS A part override")
            self.cbx_apart.actionPerformed = self.check_apart

            self.txt_apart.setEditable(FALSE)
            self.txt_apart.setFont(Font("Tahoma", 0, 14))
            self.txt_apart.setToolTipText("DSS A part override")

            # set the checkbox and checkbox input text field
            try:
                self.txt_apart.setText(self.configurations["apart"])
                if (
                    self.configurations["apart"] != ""
                    and self.configurations["watershed_slug"]
                    != self.configurations["apart"]
                ):
                    self.cbx_apart.selected = TRUE
                    self.txt_apart.editable = TRUE

                self.txt_select_file.setText(self.configurations["dss"])
                idx = self.watershed_index(
                    self.configurations["watershed_id"], self.api_watersheds
                )
                self.lst_watersheds.setSelectedIndex(idx)
            except KeyError as ex:
                print("KeyError: missing {}".format(ex))

            layout = GroupLayout(self.getContentPane())
            self.getContentPane().setLayout(layout)
            layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING).addGroup(
                    layout.createSequentialGroup()
                    .addContainerGap()
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(
                            layout.createSequentialGroup()
                            .addGroup(
                                layout.createParallelGroup(
                                    GroupLayout.Alignment.LEADING
                                )
                                .addGroup(
                                    layout.createSequentialGroup()
                                    .addComponent(lbl_select_file)
                                    .addGap(0, 0, Short.MAX_VALUE)
                                )
                                .addComponent(
                                    self.txt_select_file,
                                    GroupLayout.PREFERRED_SIZE,
                                    429,
                                    GroupLayout.PREFERRED_SIZE,
                                )
                            )
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                            .addComponent(btn_select)
                        )
                        .addComponent(jScrollPane1)
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(self.cbx_apart)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                            .addComponent(self.txt_apart)
                        )
                        .addGroup(
                            layout.createSequentialGroup()
                            .addComponent(btn_execute)
                            .addGap(18, 18, 18)
                            .addComponent(btn_save)
                            .addPreferredGap(
                                LayoutStyle.ComponentPlacement.RELATED,
                                GroupLayout.DEFAULT_SIZE,
                                Short.MAX_VALUE,
                            )
                            .addComponent(btn_close)
                        )
                    )
                    .addContainerGap()
                )
            )
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING).addGroup(
                    layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(
                        jScrollPane1,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.DEFAULT_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addGap(18, 18, 18)
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(self.cbx_apart)
                        .addComponent(
                            self.txt_apart,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.DEFAULT_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                    )
                    .addGap(18, 18, 18)
                    .addComponent(lbl_select_file)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(
                            self.txt_select_file,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.DEFAULT_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                        .addComponent(btn_select)
                    )
                    .addPreferredGap(
                        LayoutStyle.ComponentPlacement.RELATED, 17, Short.MAX_VALUE
                    )
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(btn_execute)
                        .addComponent(btn_save)
                        .addComponent(btn_close)
                    )
                    .addContainerGap()
                )
            )

            self.pack()
            self.setLocationRelativeTo(None)

        #
        # ~~~~~~~~~~~~ END OF THE JAVA PANE ~~~~~~~~~~~~
        #

        def watersheds(self, event):
            """event handler selecting a watershed from the list

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            # index = self.lst_watersheds.selectedIndex
            if not self.cbx_apart.selected:
                selected_watershed = self.lst_watersheds.getSelectedValue()
                self.txt_apart.setText(self.api_watersheds[selected_watershed]["slug"])

            if not event.getValueIsAdjusting():
                pass
                # print(self.api_watersheds[self.lst_watersheds.getSelectedValue()])

        def watershed_refactor(self, json_):
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

        def watershed_index(self, ws_id, ws_dict):
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

        def check_apart(self, event):
            """check box activating DSS Apart editing

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.txt_apart.editable = self.cbx_apart.selected

        def select_file(self, event):
            """initiate Java Swing JFileChooser

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            file_chooser = jutil.FileChooser()
            file_chooser.title = "Select Output DSS File"
            try:
                _dir = os.path.dirname(self.txt_select_file.getText())
                file_chooser.set_current_dir(_dir)
            except TypeError as ex:
                print(ex)

            file_chooser.show()
            self.txt_select_file.setText(file_chooser.output_path)

        def save(self, event):
            """save the selected configurations to file

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            selected_watershed = self.lst_watersheds.getSelectedValue()

            watershed_id = self.api_watersheds[selected_watershed]["id"]
            watershed_slug = self.api_watersheds[selected_watershed]["slug"]

            # Get, set and save jutil.configurations
            self.configurations["watershed_id"] = watershed_id
            self.configurations["watershed_slug"] = watershed_slug
            self.configurations["apart"] = self.txt_apart.getText()
            self.configurations["dss"] = self.txt_select_file.getText()
            DictConfig(self.config_path).write(self.configurations)

            msg = []
            for k, v in sorted(self.configurations.items()):
                v = "\n".join(v) if isinstance(v, list) else v
                msg.append("{}: {}".format(k, v))

            JOptionPane.showMessageDialog(
                None,
                "\n\n".join(msg),
                "Updated Config",
                JOptionPane.INFORMATION_MESSAGE,
            )

        def execute(self, event):
            """set configurations to execute Go binding

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.save(event)
            self.outer_class.execute()
            self.close(event)

        def close(self, event):
            """close the UI

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.setVisible(FALSE)
            self.dispose()


if __name__ == "__main__":
    # tesing #
    print("Testing")
    # cui = WaterExtractUI()
    # cui.set_config_file(r"C:\Users\u4rs9jsg\projects\rts-utils\test_extract.json")
    # cui.parameters(
    #     {"Host": "develop-water-api.corps.cloud", "Scheme": "https", "Timeout": 120}
    # )
    # # cui.execute()
    # cui.show()
