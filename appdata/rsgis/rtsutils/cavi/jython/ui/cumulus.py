"""Cumulus UI
"""

import json
import os
import sys
from collections import OrderedDict
import tempfile

import javax.swing.border as border
from hec.heclib.dss import HecDSSUtilities
from java.awt import Font, Point
from java.io import File
from java.lang import Short
from javax.swing import (
    BorderFactory,
    GroupLayout,
    ImageIcon,
    JButton,
    JFrame,
    JLabel,
    JList,
    JOptionPane,
    JRootPane,
    JScrollPane,
    JTextField,
    LayoutStyle,
    ListSelectionModel,
    SwingConstants,
)
from rtsutils import FALSE, TRUE, go, null
from rtsutils.cavi.jython import jutil
from rtsutils.utils import CLOUD_ICON
from rtsutils.utils.config import DictConfig


def convert_dss(dss_src, dss_dst):
    """convert DSS7 from Cumulus to DSS6 on local machine defined by DSS
    destination

    Parameters
    ----------
    dss_src : string
        DSS downloaded file location
    dss_dst : string
        DSS location, user defined
    """
    msg = "Downloaded grid not found"
    if os.path.exists(dss_src):
        dss7 = HecDSSUtilities()
        dss7.setDSSFileName(dss_src)
        dss6_temp = os.path.join(tempfile.gettempdir(), "dss6.dss")
        result = dss7.convertVersion(dss6_temp)
        dss6 = HecDSSUtilities()
        dss6.setDSSFileName(dss6_temp)
        dss6.copyFile(dss_dst)
        dss7.close()
        dss6.close()
        try:
            os.remove(dss_src)
            os.remove(dss6_temp)
        except Exception as ex:
            print(ex)
        msg = "Converted '{}' to '{}' (int={})".format(dss_src, dss_dst, result)

    print(msg)


class CumulusUI:
    """Java Swing for Cumulus configurations"""

    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    @classmethod
    def show(cls):
        """set UI visible true"""
        cls.ui = cls.UI()
        cls.ui.setVisible(TRUE)

    @classmethod
    def execute(cls, cfg, dss_file):
        """executing the Go binding as a subprocess

        Parameters
        ----------
        cfg : dict
            configurations for the Go binding
        """
        stdout, stderr = go.get(cfg, subprocess_=FALSE)
        if "error" in stderr:
            print(stderr)
            sys.exit(1)
        else:
            _, file_path = stdout.split("::")
            convert_dss(file_path, dss_file)

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
            super(CumulusUI.UI, self).__init__()
            self.outer_class = CumulusUI()

            if self.outer_class.config_path is None:
                JOptionPane.showMessageDialog(
                    None,
                    "No configuration file path provided\n\nExiting program",
                    "Missing Configuration File",
                    JOptionPane.ERROR_MESSAGE,
                )
                sys.exit(1)

            self.config_path = self.outer_class.config_path
            self.go_config = self.outer_class.go_config

            self.configurations = DictConfig(self.config_path).read()

            self.go_config["Endpoint"] = "watersheds"
            ws_out, stderr = go.get(self.go_config)
            self.go_config["Endpoint"] = "products"
            ps_out, stderr = go.get(self.go_config)
            if "error" in stderr:
                print(stderr)
                sys.exit(1)

            self.api_watersheds = self.watershed_refactor(json.loads(ws_out))
            self.api_products = self.product_refactor(json.loads(ps_out))

            #
            # ~~~~~~~~~~~~ START OF THE JAVA PANE ~~~~~~~~~~~~
            #
            jScrollPane1 = JScrollPane()
            self.lst_products = JList()
            jScrollPane2 = JScrollPane()
            self.lst_watersheds = JList()
            lbl_select_file = JLabel()
            self.txt_select_file = JTextField()
            btn_select = JButton()
            btn_execute = JButton()
            btn_save = JButton()
            btn_close = JButton()

            # self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE)
            self.setTitle("Cumulus Configuration")
            self.setAlwaysOnTop(TRUE)
            self.setIconImage(ImageIcon(CLOUD_ICON).getImage())
            self.setLocation(Point(10, 10))
            self.setLocationByPlatform(TRUE)
            self.setName("CumulusCaviUI")
            # NOI18N
            self.setResizable(FALSE)

            self.lst_products = JList(
                sorted(self.api_products.keys()), valueChanged=self.products
            )
            self.lst_products.setBorder(
                BorderFactory.createTitledBorder(
                    null,
                    "Products",
                    border.TitledBorder.CENTER,
                    border.TitledBorder.TOP,
                    Font("Tahoma", 0, 14),
                )
            )
            # NOI18N
            self.lst_products.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            self.lst_products.setToolTipText("List of products")
            jScrollPane1.setViewportView(self.lst_products)

            self.lst_watersheds = JList(
                sorted(self.api_watersheds.keys()), valueChanged=self.watersheds
            )
            self.lst_watersheds.setBorder(
                BorderFactory.createTitledBorder(
                    null,
                    "Watersheds",
                    border.TitledBorder.CENTER,
                    border.TitledBorder.TOP,
                    Font("Tahoma", 0, 14),
                )
            )
            # NOI18N
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
            self.lst_watersheds.setToolTipText("List of watersheds")
            jScrollPane2.setViewportView(self.lst_watersheds)

            lbl_select_file.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            lbl_select_file.setText("DSS File Downloads")

            self.txt_select_file.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)")

            btn_select.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_select.setText("...")
            btn_select.setToolTipText("Select File...")
            btn_select.actionPerformed = self.select_file

            btn_execute.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_execute.setText("Save and Execute Configuration")
            btn_execute.setToolTipText("Save and Execute Configuration")
            btn_execute.actionPerformed = self.execute
            btn_execute.setHorizontalTextPosition(SwingConstants.CENTER)

            btn_save.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_save.setText("Save Configuration")
            btn_save.setToolTipText("Save Configuration")
            btn_save.actionPerformed = self.save
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER)

            btn_close.setFont(Font("Tahoma", 0, 14))
            # NOI18N
            btn_close.setText("Close")
            btn_close.setToolTipText("Close GUI")
            btn_close.actionPerformed = self.close
            btn_close.setHorizontalTextPosition(SwingConstants.CENTER)

            try:
                self.txt_select_file.setText(self.configurations["dss"])
                idxs = self.product_index(
                    self.configurations["product_ids"], self.api_products
                )
                self.lst_products.setSelectedIndices(idxs)
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
                        .addComponent(jScrollPane1)
                        .addGroup(
                            layout.createSequentialGroup()
                            .addGroup(
                                layout.createParallelGroup(
                                    GroupLayout.Alignment.LEADING
                                )
                                .addComponent(lbl_select_file)
                                .addGroup(
                                    layout.createSequentialGroup()
                                    .addComponent(
                                        self.txt_select_file,
                                        GroupLayout.PREFERRED_SIZE,
                                        429,
                                        GroupLayout.PREFERRED_SIZE,
                                    )
                                    .addPreferredGap(
                                        LayoutStyle.ComponentPlacement.RELATED
                                    )
                                    .addComponent(btn_select)
                                )
                            )
                            .addGap(0, 0, Short.MAX_VALUE)
                        )
                        .addGroup(
                            GroupLayout.Alignment.TRAILING,
                            layout.createSequentialGroup()
                            .addComponent(btn_execute)
                            .addGap(18, 18, 18)
                            .addComponent(btn_save)
                            .addPreferredGap(
                                LayoutStyle.ComponentPlacement.RELATED,
                                GroupLayout.DEFAULT_SIZE,
                                Short.MAX_VALUE,
                            )
                            .addComponent(btn_close),
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
                    .addComponent(lbl_select_file)
                    .addPreferredGap(
                        LayoutStyle.ComponentPlacement.RELATED,
                        GroupLayout.DEFAULT_SIZE,
                        Short.MAX_VALUE,
                    )
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
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
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
            self.setLocationRelativeTo(null)

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

        def product_refactor(self, json_):
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

        def product_index(self, prod_select, prod_dict):
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

        def products(self, event):
            """event handler selecting products from the list

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            # index = self.lst_products.selectedIndex
            if not event.getValueIsAdjusting():
                pass
                # print(self.api_products[self.lst_products.getSelectedValue()])

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
                file_chooser.set_current_dir(File(_dir))
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
            selected_products = self.lst_products.getSelectedValues()

            watershed_id = self.api_watersheds[selected_watershed]["id"]
            watershed_slug = self.api_watersheds[selected_watershed]["slug"]
            product_ids = [self.api_products[p]["id"] for p in selected_products]

            # Get, set and save jutil.configurations
            self.configurations["watershed_id"] = watershed_id
            self.configurations["watershed_slug"] = watershed_slug
            self.configurations["product_ids"] = product_ids
            self.configurations["dss"] = self.txt_select_file.getText()
            DictConfig(self.config_path).write(self.configurations)

            msg = []
            for k, v in sorted(self.configurations.items()):
                v = "\n".join(v) if isinstance(v, list) else v
                msg.append("{}: {}".format(k, v))

            j_frame = JFrame()
            j_frame.setAlwaysOnTop(TRUE)
            JOptionPane.showMessageDialog(
                j_frame,
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
            self.outer_class.go_config["Subcommand"] = "grid"
            self.outer_class.go_config["Slug"] = self.configurations["watershed_slug"]
            self.outer_class.go_config["Products"] = self.configurations["product_ids"]
            self.outer_class.execute(
                self.outer_class.go_config, self.configurations["dss"]
            )
            self.close(event)

        def close(self, event):
            """close the UI

            Parameters
            ----------
            event : ActionEvent
                component-defined action
            """
            self.dispose()
            sys.exit()


if __name__ == "__main__":
    # tesing #
    cui = CumulusUI()
    cui.set_config_file(r"C:\Users\dev\projects\rts-utils\test_cumulus.json")
    cui.parameters({"Host": "develop-cumulus-api.corps.cloud", "Scheme": "https"})
    cui.show()
