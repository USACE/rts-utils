"""Java Swing UI for Water API extracting time series
"""

import os
import json
from functools import partial
from java.lang import Runnable, Short
from java.awt import EventQueue, Font, Point, Cursor
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
from rtsutils import go
from rtsutils.cavi.jython import jutil
from rtsutils.utils.config import DictConfig
from rtsutils.utils import EXTRACT_ICON, watershed_index, watershed_refactor


class Extract():
    config_path = {}
    go_config = {}

    @classmethod
    def invoke(cls):
        """The invoke classmethod 'runs' the runnable cumulus class
        """
        EventQueue.invokeLater(cls.Extract_Runnable())

    @classmethod
    def execute(cls):
        """executing the Go binding as a subprocess"""
        configurations = DictConfig(cls.config_path).read()

        cls.go_config.update({
            "StdOut": "true",
            "Subcommand": "extract",
            "Endpoint": "watersheds/{}/extract".format(
                configurations["watershed_slug"]
            ),
        })

        sub = go.get(out_err=False, is_shell=False)
        sub.stdin.write(json.dumps(cls.go_config))
        sub.stdin.close()
        dsspath = configurations["dss"]

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
                msg = jutil.put_timeseries(obj, dsspath, configurations["apart"])
                if msg:
                    print(msg)

        std_err = sub.stderr.read()
        sub.stderr.close()
        sub.stdout.close()
        print(std_err)
        if "error" in std_err:
            JOptionPane.showMessageDialog(
                None,
                std_err.split("::")[-1],
                "Error",
                JOptionPane.ERROR_MESSAGE,
            )
            quit()

        JOptionPane.showMessageDialog(
            None,
            "Program Done",
            "Program Done",
            JOptionPane.INFORMATION_MESSAGE,
        )

    @classmethod
    def extract_configuration(cls, cfg):
        """Set the extract configuration file"""
        cls.config_path = cfg

    @classmethod
    def go_configuration(cls, dict_):
        """update Go parameters

        Parameters
        ----------
        dict_ : dict
            Go parameters to update class defined configurations
        """
        cls.go_config = dict_

    class Extract_Runnable(Runnable):
        """java.lang.Runnable class executes run when called"""

        def watersheds(self, event):
            """event handler selecting a watershed from the list

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            # index = self.watershed_list.selectedIndex
            if not self.check_box.selected:
                selected_watershed = self.watershed_list.getSelectedValue()
                self.apart.setText(self.api_watersheds[selected_watershed]["slug"])

            if not event.getValueIsAdjusting():
                pass
                # print(self.api_watersheds[self.watershed_list.getSelectedValue()])

        def check_apart(self, event):
            """check box activating DSS Apart editing

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.apart.editable = self.check_box.selected

        def select(self, event):
            """initiate Java Swing JFileChooser

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            file_chooser = jutil.FileChooser()
            file_chooser.title = "Select Output DSS File"
            try:
                _dir = os.path.dirname(self.dsspath.getText())
                file_chooser.set_current_dir(_dir)
            except TypeError as ex:
                print(ex)

            file_chooser.show()
            self.dsspath.setText(file_chooser.output_path)

        def execute(self, event):
            """set configurations to execute Go binding

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """

            if self.save_config():
                source = event.getSource()
                prev = source.getCursor()
                source.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR))
                self.outer_class.execute()
                source.setCursor(prev)

        def save(self, event):
            """save the selected configurations to file

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            if self.save_config():
                source = event.getSource()
                source.setText("Configuration Saved")

        def save_config(self):
            """save the selected configurations to file
            """
            selected_watershed = self.watershed_list.getSelectedValue()
            apart = self.apart.getText()
            dssfile = self.dsspath.getText()

            if selected_watershed and apart and dssfile:
                watershed_id = self.api_watersheds[selected_watershed]["id"]
                watershed_slug = self.api_watersheds[selected_watershed]["slug"]

                # Get, set and save jutil.configurations
                self.configurations["watershed_id"] = watershed_id
                self.configurations["watershed_slug"] = watershed_slug
                self.configurations["apart"] = apart
                self.configurations["dss"] = dssfile
                DictConfig(self.outer_class.config_path).write(self.configurations)
            else:
                JOptionPane.showMessageDialog(
                    None,
                    "Missing configuration inputs",
                    "Configuration Inputs",
                    JOptionPane.INFORMATION_MESSAGE,
                )
                return False
            return True

        def close(self, event):
            """Close the dialog

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.dispose()
        
        def create_jbutton(self, label, action):
            """Dynamic JButton creation

            Parameters
            ----------
            label : str
                set text and tooltip
            action : actionPerformed
                the action in the class to be performed

            Returns
            -------
            JButton
                java swing JButton
            """
            jbutton = self.jbutton = JButton()
            jbutton.setFont(Font("Tahoma", 0, 14))
            jbutton.setText(label)
            jbutton.setToolTipText(label)
            jbutton.actionPerformed = action
            jbutton.setHorizontalTextPosition(SwingConstants.CENTER)

            return jbutton

        def create_jlist(self, label, values=None, mode=ListSelectionModel.MULTIPLE_INTERVAL_SELECTION):
            """Dynamic JList creation

            Parameters
            ----------
            label : str
                set text and tooltip
            values : OrderedDict, optional
                ordered dictionary, by default None
            mode : ListSelectionModel, optional
                define JList selection method, by default ListSelectionModel.MULTIPLE_INTERVAL_SELECTION

            Returns
            -------
            JList
                java swing JList
            """
            jlist = self.jlist = JList(sorted(values))
            jlist.setFont(Font("Tahoma", 0, 14))
            jlist.setSelectionMode(mode)
            jlist.setToolTipText(label)
            jlist.setBorder(
                BorderFactory.createTitledBorder(
                    None, label, 2, 2, Font("Tahoma", 0, 14)
                )
            )
            return jlist

        def run(self):
            """Invloke
            """
            self.outer_class = Extract()

            if self.outer_class.config_path is None:
                JOptionPane.showMessageDialog(
                    None,
                    "No configuration file path provided\n\nExiting program",
                    "Missing Configuration File",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.configurations = DictConfig(self.outer_class.config_path).read()

            self.outer_class.go_config["StdOut"] = "true"
            self.outer_class.go_config["Subcommand"] = "get"
            self.outer_class.go_config["Endpoint"] = "watersheds"

            ws_out, stderr = go.get(self.outer_class.go_config, out_err=True, is_shell=False)

            if "error" in stderr:
                print(stderr)
                JOptionPane.showMessageDialog(
                    None,
                    stderr.split("::")[-1],
                    "Program Error",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.api_watersheds = watershed_refactor(json.loads(ws_out))

            frame = JFrame("Extract Time Series Configuration")
            frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
            frame.setAlwaysOnTop(False)
            frame.setIconImage(ImageIcon(EXTRACT_ICON).getImage())
            frame.setLocation(Point(10, 10))
            frame.setLocationByPlatform(True)
            frame.setName("WaterExtractUI")
            frame.setResizable(True)
            content_pane = frame.getContentPane()

            # create lists
            self.watershed_list = self.create_jlist("Watersheds", self.api_watersheds, ListSelectionModel.SINGLE_SELECTION)
            self.watershed_list.valueChanged = self.watersheds
            
            # create buttons
            select_button = self.create_jbutton("...", self.select)
            execute_button = self.create_jbutton("Save and Execute Configuration", self.execute)
            save_button = self.create_jbutton("Save Configuration", self.save)
            close_button = self.create_jbutton("close", self.close)
            # create label
            label = self.label = JLabel()
            label.setFont(Font("Tahoma", 0, 14))
            label.setText("DSS File Downloads")
            # create text field for dsspath
            dsspath = self.dsspath = JTextField()
            dsspath.setFont(Font("Tahoma", 0, 14))
            dsspath.setToolTipText("FQPN to output file (.dss)")
            # create text field for apart
            apart = self.apart = JTextField()
            apart.setEditable(False)
            apart.setFont(Font("Tahoma", 0, 14))
            apart.setToolTipText("DSS A part override")
            # create check box
            check_box = self.check_box = JCheckBox()
            check_box.setFont(Font("Tahoma", 0, 14))
            check_box.setText("DSS A part")
            check_box.setToolTipText("DSS A part override")
            check_box.actionPerformed = self.check_apart
            # create scroll pane
            jScrollPane1 = JScrollPane()
            jScrollPane1.setViewportView(self.watershed_list)

            # set the checkbox and checkbox input text field
            try:
                apart.setText(self.configurations["apart"])
                if (
                    self.configurations["apart"] != ""
                    and self.configurations["watershed_slug"]
                    != self.configurations["apart"]
                ):
                    check_box.selected = True
                    apart.editable = True

                self.dsspath.setText(self.configurations["dss"])
                idx = watershed_index(
                    self.configurations["watershed_id"], self.api_watersheds
                )
                self.watershed_list.setSelectedIndex(idx)
            except KeyError as ex:
                print("KeyError: missing {}".format(ex))

            layout = GroupLayout(content_pane)
            content_pane.setLayout(layout)
            layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addComponent(jScrollPane1)
                        .addGroup(layout.createSequentialGroup()
                            .addComponent(check_box)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                            .addComponent(apart))
                        .addGroup(layout.createSequentialGroup()
                            .addComponent(label)
                            .addGap(0, 0, Short.MAX_VALUE))
                        .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                            .addComponent(dsspath, GroupLayout.DEFAULT_SIZE, 429, Short.MAX_VALUE)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                            .addComponent(select_button))
                        .addGroup(layout.createSequentialGroup()
                            .addGap(0, 0, Short.MAX_VALUE)
                            .addComponent(execute_button)
                            .addGap(18, 18, 18)
                            .addComponent(save_button)))
                    .addContainerGap())
            )
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(jScrollPane1, GroupLayout.DEFAULT_SIZE, 166, Short.MAX_VALUE)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(check_box)
                        .addComponent(apart, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addComponent(label)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(dsspath, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                        .addComponent(select_button))
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(execute_button)
                        .addComponent(save_button))
                    .addContainerGap())
            )

            frame.pack()
            frame.setLocationRelativeTo(None)


            frame.setVisible(True)
