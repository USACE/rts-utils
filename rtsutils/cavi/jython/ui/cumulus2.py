"""_summary_
"""

import os
import json
import java
from java.awt import EventQueue, Font, Point, Cursor
from javax.swing import (
    BorderFactory,
    GroupLayout,
    ImageIcon,
    JButton,
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
from rtsutils.utils import CLOUD_ICON, product_index, product_refactor, watershed_index, watershed_refactor


class Cumulus():
    cumulus_configs = None
    go_config = None

    @classmethod
    def invoke(cls):
        """The invoke classmethod 'runs' the runnable cumulus class
        """
        EventQueue.invokeLater(cls.Cumulus_Runnable())

    @classmethod
    def execute(cls):
        """executing the Go binding as a subprocess"""
        configurations = DictConfig(cls.cumulus_configs).read()

        cls.go_config.update({
            "StdOut": "true",
            "Subcommand": "grid",
            "Endpoint": "downloads",
            "ID": configurations["watershed_id"],
            "Products": configurations["product_ids"],
        })

        stdout, stderr = go.get(cls.go_config, out_err=True, is_shell=False)
        print(stderr)
        if "error" in stderr:
            JOptionPane.showMessageDialog(
                None,
                stderr.split("::")[-1],
                "Program Error",
                JOptionPane.ERROR_MESSAGE,
            )
            quit()

        try:
            _, file_path = stdout.split("::")
            jutil.convert_dss(file_path, configurations["dss"])

            JOptionPane.showMessageDialog(
                None,
                "Program Done",
                "Program Done",
                JOptionPane.INFORMATION_MESSAGE,
            )
        except ValueError as ex:
            print(ex)

    @classmethod
    def cumulus_configuration(cls, cfg):
        """Set the cumulus configuration file"""
        cls.cumulus_configs = cfg

    @classmethod
    def go_configuration(cls, dict_):
        """update Go parameters

        Parameters
        ----------
        dict_ : dict
            Go parameters to update class defined configurations
        """
        cls.go_config = dict_

    class Cumulus_Runnable(java.lang.Runnable):
        """_summary_"""

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
                self.close(event)

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
            selected_products = self.product_list.getSelectedValues()
            dssfile = self.dsspath.getText()

            if selected_products and selected_watershed and dssfile:
                watershed_id = self.api_watersheds[selected_watershed]["id"]
                watershed_slug = self.api_watersheds[selected_watershed]["slug"]
                product_ids = [self.api_products[p]["id"] for p in selected_products]

                # Get, set and save jutil.configurations
                self.configurations["watershed_id"] = watershed_id
                self.configurations["watershed_slug"] = watershed_slug
                self.configurations["product_ids"] = product_ids
                self.configurations["dss"] = dssfile
                DictConfig(self.outer_class.cumulus_configs).write(self.configurations)
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
            quit()
        
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
            self.outer_class = Cumulus()

            if self.outer_class.cumulus_configs is None:
                JOptionPane.showMessageDialog(
                    None,
                    "No configuration file path provided\n\nExiting program",
                    "Missing Configuration File",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.configurations = DictConfig(self.outer_class.cumulus_configs).read()

            self.outer_class.go_config["StdOut"] = "true"
            self.outer_class.go_config["Subcommand"] = "get"
            self.outer_class.go_config["Endpoint"] = "watersheds"

            ws_out, stderr = go.get(self.outer_class.go_config, out_err=True, is_shell=False)
            self.outer_class.go_config["Endpoint"] = "products"
            ps_out, stderr = go.get(self.outer_class.go_config, out_err=True, is_shell=False)

            if "error" in stderr:
                print(stderr)
                JOptionPane.showMessageDialog(
                    None,
                    stderr.split("::")[-1],
                    "Program Error",
                    JOptionPane.ERROR_MESSAGE,
                )

            self.api_watersheds = watershed_refactor(json.loads(ws_out))
            self.api_products = product_refactor(json.loads(ps_out))

            frame = JFrame("Cumulus Configuration")
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE)
            frame.setTitle("Cumulus Configuration")
            frame.setAlwaysOnTop(False)
            frame.setIconImage(ImageIcon(CLOUD_ICON).getImage())
            frame.setLocation(Point(10, 10))
            frame.setLocationByPlatform(True)
            frame.setName("CumulusCaviUI")
            frame.setResizable(True)
            content_pane = frame.getContentPane()

            # create lists
            self.watershed_list = self.create_jlist("Watersheds", self.api_watersheds, ListSelectionModel.SINGLE_SELECTION)
            self.product_list = self.create_jlist("Products", self.api_products)
            # create buttons
            select_button = self.create_jbutton("...", self.select)
            execute_button = self.create_jbutton("Save and Execute Configuration", self.execute)
            save_button = self.create_jbutton("Save Configuration", self.save)
            close_button = self.create_jbutton("close", self.close)
            # create label
            label = self.label = JLabel()
            label.setFont(Font("Tahoma", 0, 14))
            label.setText("DSS File Downloads")
            # create text field
            dsspath = self.dsspath = JTextField()
            dsspath.setFont(Font("Tahoma", 0, 14))
            dsspath.setToolTipText("FQPN to output file (.dss)")
            # create scroll pane
            jScrollPane1 = JScrollPane()
            jScrollPane2 = JScrollPane()
            jScrollPane1.setViewportView(self.product_list)
            jScrollPane2.setViewportView(self.watershed_list)

            try:
                dsspath.setText(self.configurations["dss"])
                idxs = product_index(
                    self.configurations["product_ids"], self.api_products
                )
                self.product_list.setSelectedIndices(idxs)
                idx = watershed_index(
                    self.configurations["watershed_id"], self.api_watersheds
                )
                self.watershed_list.setSelectedIndex(idx)
            except KeyError as ex:
                print("KeyError: missing {}".format(ex))

            layout = GroupLayout(content_pane)
            content_pane.setLayout(layout)
            layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING).addGroup(
                    layout.createSequentialGroup()
                    .addContainerGap()
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addComponent(jScrollPane1)
                        .addGroup(
                            layout.createSequentialGroup()
                            .addGroup(
                                layout.createParallelGroup(
                                    GroupLayout.Alignment.LEADING
                                )
                                .addComponent(label)
                                .addGroup(
                                    layout.createSequentialGroup()
                                    .addComponent(
                                        dsspath,
                                        GroupLayout.PREFERRED_SIZE,
                                        429,
                                        GroupLayout.PREFERRED_SIZE,
                                    )
                                    .addPreferredGap(
                                        LayoutStyle.ComponentPlacement.RELATED
                                    )
                                    .addComponent(select_button)
                                )
                            )
                            .addGap(0, 0, java.lang.Short.MAX_VALUE)
                        )
                        .addGroup(
                            GroupLayout.Alignment.TRAILING,
                            layout.createSequentialGroup()
                            .addComponent(execute_button)
                            .addGap(18, 18, 18)
                            .addComponent(save_button)
                            .addPreferredGap(
                                LayoutStyle.ComponentPlacement.RELATED,
                                GroupLayout.DEFAULT_SIZE,
                                java.lang.Short.MAX_VALUE,
                            )
                            .addComponent(close_button),
                        )
                        .addComponent(jScrollPane2)
                    )
                    .addContainerGap()
                )
            )
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING).addGroup(
                    layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(
                        jScrollPane2,
                        GroupLayout.PREFERRED_SIZE,
                        GroupLayout.DEFAULT_SIZE,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addGap(18, 18, 18)
                    .addComponent(
                        jScrollPane1,
                        GroupLayout.PREFERRED_SIZE,
                        280,
                        GroupLayout.PREFERRED_SIZE,
                    )
                    .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                    .addComponent(label)
                    .addPreferredGap(
                        LayoutStyle.ComponentPlacement.RELATED,
                        GroupLayout.DEFAULT_SIZE,
                        java.lang.Short.MAX_VALUE,
                    )
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(
                            dsspath,
                            GroupLayout.PREFERRED_SIZE,
                            GroupLayout.DEFAULT_SIZE,
                            GroupLayout.PREFERRED_SIZE,
                        )
                        .addComponent(select_button)
                    )
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(
                        layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(execute_button)
                        .addComponent(save_button)
                        .addComponent(close_button)
                    )
                    .addContainerGap()
                )
            )

            frame.pack()
            frame.setLocationRelativeTo(None)


            frame.setVisible(True)
