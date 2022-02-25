# Java

from java.lang import Short
from java.awt import Font, Point
from javax.swing import JFrame, JButton, JLabel, JTextField, JList, JCheckBox
from javax.swing import JScrollPane, JOptionPane, SwingConstants
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon
from java.io import File

import os
import json
import sys
from collections import OrderedDict


from rtsutils.cavi.jython import jutil, ICON
from rtsutils.config import DictConfig
from rtsutils import go


false = 0
true = 1
null = None


class CumulusUI():
    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    def show(self):
        self.ui = self.UI()
        self.ui.setVisible(1)

    @classmethod
    def set_config_file(cls, cfg):
        """Set the cumulus configuration file"""
        cls.config_path = cfg


    @classmethod
    def endpoint(cls, d):
        cls.go_config.update(d)


    class UI(JFrame):
        def __init__(self):
            super(CumulusUI.UI, self).__init__()
            self.Outer = CumulusUI()

            if self.Outer.config_path is None:
                JOptionPane.showMessageDialog(None, "No configuration file path provided\n\nExiting program", "Missing Configuration File", JOptionPane.ERROR_MESSAGE)
                sys.exit(1)


            self.config_path = self.Outer.config_path
            self.go_config = self.Outer.go_config

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

            btn_save = JButton();
            self.txt_select_file = JTextField();
            btn_select = JButton();
            lbl_select_file = JLabel();
            jScrollPane1 = JScrollPane();
            self.lst_products = JList();
            jScrollPane2 = JScrollPane();
            self.lst_watersheds = JList();

            self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setTitle("Cumulus Configuration");
            self.setIconImage(ImageIcon(ICON).getImage());
            self.setLocation(Point(10, 10));
            self.setLocationByPlatform(1);
            self.setName("CumulusCaviUi");
            self.setResizable(0);

            btn_save.setFont(Font("Tahoma", 0, 18));
            btn_save.setText("Save Configuration");
            btn_save.setActionCommand("save");
            btn_save.actionPerformed = self.save;


            self.txt_select_file.setFont(Font("Tahoma", 0, 18));
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)");

            btn_select.setFont(Font("Tahoma", 0, 18));
            btn_select.setText("...");
            btn_select.setToolTipText("Select File...");
            btn_select.actionPerformed = self.select_file;

            lbl_select_file.setText("DSS File Downloads");

            self.lst_products = JList(sorted(self.api_products.keys()), valueChanged = self.products)
            self.lst_products.setBorder(BorderFactory.createTitledBorder(None, "Products", 2, 2, Font("Tahoma", 0, 14)));
            self.lst_products.setFont(Font("Tahoma", 0, 14));
            


            self.lst_watersheds = JList(sorted(self.api_watersheds.keys()), valueChanged = self.watersheds)
            self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(None, "Watersheds", 2, 2, Font("Tahoma", 0, 14)));
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14));
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

            
            try:
                self.txt_select_file.setText(self.configurations["dss"])
                self.lst_products.setSelectedIndices(idxs)
                idxs = self.product_index(self.configurations["product_ids"], self.api_products)
                idx = self.watershed_index(self.configurations["watershed_slug"], self.api_watersheds)
                self.lst_watersheds.setSelectedIndex(idx)
            except KeyError as ex:
                print("KeyError: missing {}".format(ex))


            jScrollPane1.setViewportView(self.lst_products);
            jScrollPane2.setViewportView(self.lst_watersheds);

            layout = GroupLayout(self.getContentPane());
            self.getContentPane().setLayout(layout);
            layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                            .addGap(0, 0, Short.MAX_VALUE)
                            .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, 399, GroupLayout.PREFERRED_SIZE)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                            .addComponent(btn_select))
                        .addGroup(layout.createSequentialGroup()
                            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                                .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING, false)
                                    .addComponent(jScrollPane2, GroupLayout.DEFAULT_SIZE, 451, Short.MAX_VALUE)
                                    .addComponent(jScrollPane1))
                                .addComponent(lbl_select_file))
                            .addGap(0, 0, Short.MAX_VALUE)))
                    .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE))
                .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                    .addContainerGap(GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addComponent(btn_save)
                    .addGap(145, 145, 145))
            );
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(jScrollPane2, GroupLayout.PREFERRED_SIZE, 201, GroupLayout.PREFERRED_SIZE)
                    .addGap(18, 18, 18)
                    .addComponent(jScrollPane1, GroupLayout.DEFAULT_SIZE, 278, Short.MAX_VALUE)
                    .addGap(18, 18, 18)
                    .addComponent(lbl_select_file)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                        .addComponent(btn_select))
                    .addGap(18, 18, 18)
                    .addComponent(btn_save)
                    .addContainerGap())
            );

            self.pack()
            self.setLocationRelativeTo(None)


        def watersheds(self, event):
            index = self.lst_watersheds.selectedIndex
            if not event.getValueIsAdjusting():
                pass
                # print(self.api_watersheds[self.lst_watersheds.getSelectedValue()])

        def watershed_refactor(self, json_):
            return OrderedDict({
                "{}:{}".format(d['office_symbol'], d['name']): d 
                for d in json_
                })
        
        def watershed_index(self, wss, d):
            try:
                idx = [
                    i
                    for i, k in enumerate(sorted(d.keys()))
                    if wss == d[k]["slug"]
                ][0]
            except IndexError as ex:
                print(ex)
                print("setting index to 0")
                idx = 0
            finally:
                return idx


        def product_refactor(self, json_):
            return OrderedDict({
                "{}".format(d['name'].replace("_", " ").title()): d 
                for d in json_
                })


        def product_index(self, ps, d):
            return [
                i
                for i, k in enumerate(sorted(d.keys()))
                if d[k]["id"] in ps
            ]


        def products(self, event):
            index = self.lst_products.selectedIndex
            if not event.getValueIsAdjusting():
                pass
                # print(self.api_products[self.lst_products.getSelectedValue()])

        def select_file(self, event):
            fc = jutil.FileChooser(self.txt_select_file)
            fc.title = "Select Output DSS File"
            try:
                _dir = os.path.dirname(self.txt_select_file)
                fc.set_current_dir(File(_dir))
            except TypeError as ex:
                print(ex)
            fc.show()
            self.txt_select_file.setText(fc.output_path)

        def save(self, event):
            selected_watershed = self.lst_watersheds.getSelectedValue()
            selected_products = self.lst_products.getSelectedValues()
            
            
            watershed_slug = self.api_watersheds[selected_watershed]["slug"]
            product_ids = [self.api_products[p]["slug"] for p in selected_products]
            
            # Get, set and save jutil.configurations
            self.configurations["watershed_slug"] = watershed_slug
            self.configurations["product_ids"] = product_ids
            self.configurations["dss"] = self.txt_select_file.getText()
            DictConfig(self.config_path).write(self.configurations)




class WaterExtractUI():
    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    def show(self):
        self.ui = self.UI()
        self.ui.setVisible(1)

    @classmethod
    def set_config_file(cls, cfg):
        """Set the cumulus configuration file"""
        cls.config_path = cfg


    @classmethod
    def endpoint(cls, d):
        cls.go_config.update(d)


    class UI(JFrame):
        def __init__(self):
            super(CumulusUI.UI, self).__init__()
            self.Outer = CumulusUI()

            if self.Outer.config_path is None:
                JOptionPane.showMessageDialog(None, "No configuration file path provided\n\nExiting program", "Missing Configuration File", JOptionPane.ERROR_MESSAGE)
                sys.exit(1)


            self.config_path = self.Outer.config_path
            self.go_config = self.Outer.go_config

            self.configurations = DictConfig(self.config_path).read()

            self.go_config["Endpoint"] = "watersheds"
            ws_out, stderr = go.get(self.go_config)
            self.go_config["Endpoint"] = "products"
            ps_out, stderr = go.get(self.go_config)
            if "error" in stderr:
                print(stderr)
                sys.exit(1)

            self.api_watersheds = self.watershed_refactor(json.loads(ws_out))

            jScrollPane1 = JScrollPane();
            self.lst_watersheds = JList();
            lbl_select_file = JLabel();
            txt_select_file = JTextField();
            btn_select = JButton();
            btn_save = JButton();
            cbx_apart = JCheckBox();
            txt_apart = JTextField();

            self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setResizable(false);


            self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(null, "Watersheds", 2, 2, Font("Tahoma", 0, 14)));
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14));
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            jScrollPane1.setViewportView(self.lst_watersheds);

            lbl_select_file.setFont(Font("Tahoma", 0, 14));
            lbl_select_file.setText("DSS File Downloads");

            txt_select_file.setFont(Font("Tahoma", 0, 18));
            txt_select_file.setToolTipText("FQPN to output file (.dss)");

            btn_select.setFont(Font("Tahoma", 0, 18));
            btn_select.setText("...");
            btn_select.setToolTipText("Select File...");
            btn_select.setActionCommand("select_file");

            btn_save.setFont(Font("Tahoma", 0, 18));
            btn_save.setText("Save Configuration");
            btn_save.setToolTipText("Write configuration to file");
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER);

            cbx_apart.setFont(Font("Tahoma", 0, 14));
            cbx_apart.setText("DSS A part");
            cbx_apart.setToolTipText("DSS A part override");

            txt_apart.setEditable(false);
            txt_apart.setFont(Font("Tahoma", 0, 14));
            txt_apart.setToolTipText("DSS A part override");

            layout = GroupLayout(self.getContentPane());
            self.getContentPane().setLayout(layout);
            layout.setHorizontalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                    .addGap(0, 156, Short.MAX_VALUE)
                    .addComponent(btn_save, GroupLayout.PREFERRED_SIZE, 205, GroupLayout.PREFERRED_SIZE)
                    .addGap(139, 139, 139))
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                        .addGroup(layout.createSequentialGroup()
                            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                                .addComponent(txt_select_file)
                                .addGroup(layout.createSequentialGroup()
                                    .addComponent(lbl_select_file)
                                    .addGap(0, 0, Short.MAX_VALUE)))
                            .addGap(18, 18, 18)
                            .addComponent(btn_select))
                        .addComponent(jScrollPane1)
                        .addGroup(layout.createSequentialGroup()
                            .addComponent(cbx_apart)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                            .addComponent(txt_apart)))
                    .addContainerGap())
            );
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(jScrollPane1, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addGap(18, 18, 18)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(cbx_apart)
                        .addComponent(txt_apart, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                    .addGap(18, 18, 18)
                    .addComponent(lbl_select_file)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                        .addComponent(btn_select))
                    .addGap(10, 10, 10)
                    .addComponent(btn_save)
                    .addContainerGap())
            );

            self.pack()
            self.setLocationRelativeTo(None)


        def watersheds(self, event):
            index = self.lst_watersheds.selectedIndex
            if not event.getValueIsAdjusting():
                pass
                # print(self.api_watersheds[self.lst_watersheds.getSelectedValue()])

        def watershed_refactor(self, json_):
            return OrderedDict({
                "{}:{}".format(d['office_symbol'], d['name']): d 
                for d in json_
                })
        
        def watershed_index(self, wss, d):
            try:
                idx = [
                    i
                    for i, k in enumerate(sorted(d.keys()))
                    if wss == d[k]["slug"]
                ][0]
            except IndexError as ex:
                print(ex)
                print("setting index to 0")
                idx = 0
            finally:
                return idx


        def select_file(self, event):
            fc = jutil.FileChooser(self.txt_select_file)
            fc.title = "Select Output DSS File"
            try:
                _dir = os.path.dirname(self.txt_select_file)
                fc.set_current_dir(File(_dir))
            except TypeError as ex:
                print(ex)
            fc.show()
            self.txt_select_file.setText(fc.output_path)


        def save(self, event):
            selected_watershed = self.lst_watersheds.getSelectedValue()
            selected_products = self.lst_products.getSelectedValues()
            
            
            watershed_slug = self.api_watersheds[selected_watershed]["slug"]
            product_ids = [self.api_products[p]["slug"] for p in selected_products]
            
            # Get, set and save jutil.configurations
            self.configurations["watershed_slug"] = watershed_slug
            self.configurations["product_ids"] = product_ids
            self.configurations["dss"] = self.txt_select_file.getText()
            DictConfig(self.config_path).write(self.configurations)








if __name__ == "__main__":
    # tesing #
    cui = WaterExtractUI()
    # set the configuration file the UI will read/write too
    cui.set_config_file(r"C:\Users\dev\projects\rts-utils\test_extract.json")
    # print(cui.config_path)


    # test endpoint updates
    cui.endpoint({"Host": "192.168.2.35", "Scheme": "http"})
    # print(cui.go_config)
    
    
    cui.show()
