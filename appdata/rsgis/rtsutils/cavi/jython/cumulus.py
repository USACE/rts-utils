# Java

import tempfile
from java.lang import Short
from java.awt import Font, Point
from javax.swing import JDialog, JFrame, JButton, JLabel, JTextField, JList, JCheckBox
from javax.swing import JScrollPane, JOptionPane, SwingConstants
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon
import javax.swing.border as border

from java.io import File

from hec.heclib.dss import HecDSSUtilities


import os
import json
import sys
from collections import OrderedDict


from rtsutils.cavi.jython import jutil, CLOUD_ICON, EXTRACT_ICON
from rtsutils.config import DictConfig
from rtsutils import go


false = 0
true = 1
null = None


class CumulusUI(JDialog):
    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    def show(self):
        self.ui = self.UI()
        self.ui.setVisible(true)

    @classmethod
    def execute(cls):
        d = DictConfig(cls.config_path).read()
        stdout, stderr = go.get(d, false)
        if "error" in stderr:
            print(stderr)
            sys.exit(1)
        else:
            print(stdout)


    @classmethod
    def set_config_file(cls, cfg):
        """Set the cumulus configuration file"""
        cls.config_path = cfg


    @classmethod
    def parameters(cls, d):
        cls.go_config.update(d)

    @classmethod
    def process(cls):
        d = DictConfig(cls.config_path).read()
        print(d)
        # stdout, stderr = go.get(d)
        # if "error" in stderr:
        #     print(stderr)
        #     sys.exit()
        # else:
        #     print(stdout)
            # _, fp = stdout.split('::')
            # if os.path.exists(fp):
            #     dss7 = HecDSSUtilities()
            #     dss7.setDSSFileName(fp)
            #     dss6_temp = os.path.join(tempfile.gettempdir(), 'dss6.dss')
            #     dss7.convertVersion(dss6_temp)
            #     dss6 = HecDSSUtilities()
            #     dss6.setDSSFileName(dss6_temp)
            #     dss6.copyFile(d["dss"])
            #     dss7.close()
            #     dss6.close()
            #     try:
            #         os.remove(fp)
            #         os.remove(dss6_temp)
            #     except Exception as err:
            #         print(err)



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

#
# ~~~~~~~~~~~~ START OF THE JAVA PANE ~~~~~~~~~~~~
#
            jScrollPane1 = JScrollPane();
            self.lst_products = JList();
            jScrollPane2 = JScrollPane();
            self.lst_watersheds = JList();
            lbl_select_file = JLabel();
            self.txt_select_file = JTextField();
            btn_select = JButton();
            btn_execute = JButton();
            btn_save = JButton();
            btn_close = JButton();

            self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setTitle("Cumulus Configuration");
            self.setAlwaysOnTop(true);
            self.setIconImage(ImageIcon(CLOUD_ICON).getImage());
            self.setLocation(Point(10, 10));
            self.setLocationByPlatform(true);
            self.setName("CumulusCaviUI"); # NOI18N
            self.setResizable(false);

            self.lst_products = JList(sorted(self.api_products.keys()), valueChanged = self.products)
            self.lst_products.setBorder(BorderFactory.createTitledBorder(null, "Products", border.TitledBorder.CENTER, border.TitledBorder.TOP, Font("Tahoma", 0, 14))); # NOI18N
            self.lst_products.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.lst_products.setToolTipText("List of products");
            # jScrollPane1.setViewportView(self.lst_products);

            self.lst_watersheds = JList(sorted(self.api_watersheds.keys()), valueChanged = self.watersheds)
            self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(null, "Watersheds", border.TitledBorder.CENTER, border.TitledBorder.TOP, Font("Tahoma", 0, 14))); # NOI18N
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            self.lst_watersheds.setToolTipText("List of watersheds");
            # jScrollPane2.setViewportView(self.lst_watersheds);

            lbl_select_file.setFont(Font("Tahoma", 0, 14)); # NOI18N
            lbl_select_file.setText("DSS File Downloads");

            self.txt_select_file.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)");

            btn_select.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_select.setText("...");
            btn_select.setToolTipText("Select File...");
            btn_select.setActionCommand("");

            btn_execute.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_execute.setText("Save and Execute Configuration");
            btn_execute.setToolTipText("Save and Execute Configuration");
            btn_execute.setActionCommand("");
            btn_execute.setHorizontalTextPosition(SwingConstants.CENTER);

            btn_save.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_save.setText("Save Configuration");
            btn_save.setToolTipText("Save Configuration");
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER);

            btn_close.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_close.setText("Close");
            btn_close.setToolTipText("Close GUI");
            btn_close.setHorizontalTextPosition(SwingConstants.CENTER);
            
            try:
                self.txt_select_file.setText(self.configurations["dss"])
                idxs = self.product_index(self.configurations["product_ids"], self.api_products)
                self.lst_products.setSelectedIndices(idxs)
                idx = self.watershed_index(self.configurations["watershed_id"], self.api_watersheds)
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
                        .addComponent(jScrollPane1)
                        .addGroup(layout.createSequentialGroup()
                            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                                .addComponent(lbl_select_file)
                                .addGroup(layout.createSequentialGroup()
                                    .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, 429, GroupLayout.PREFERRED_SIZE)
                                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                                    .addComponent(btn_select)))
                            .addGap(0, 0, Short.MAX_VALUE))
                        .addGroup(GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                            .addComponent(btn_execute)
                            .addGap(18, 18, 18)
                            .addComponent(btn_save)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .addComponent(btn_close))
                        .addComponent(jScrollPane2))
                    .addContainerGap())
            );
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(jScrollPane2, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addGap(18, 18, 18)
                    .addComponent(jScrollPane1, GroupLayout.PREFERRED_SIZE, 280, GroupLayout.PREFERRED_SIZE)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                    .addComponent(lbl_select_file)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                        .addComponent(btn_select))
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(btn_execute)
                        .addComponent(btn_save)
                        .addComponent(btn_close))
                    .addContainerGap())
            );

            self.pack()
            self.setLocationRelativeTo(None)
#
# ~~~~~~~~~~~~ END OF THE JAVA PANE ~~~~~~~~~~~~
#


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
                    if wss == d[k]["id"]
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
            idxs = [
                i
                for i, k in enumerate(sorted(d.keys()))
                if d[k]["id"] in ps
            ]
            return idxs


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
            
            
            watershed_id = self.api_watersheds[selected_watershed]["id"]
            product_ids = [self.api_products[p]["id"] for p in selected_products]
            
            # Get, set and save jutil.configurations
            self.configurations["watershed_id"] = watershed_id
            self.configurations["product_ids"] = product_ids
            self.configurations["dss"] = self.txt_select_file.getText()
            DictConfig(self.config_path).write(self.configurations)

            msg = ["{}: {}".format(k, v) for k, v in sorted(self.configurations.items())]

            JOptionPane.showMessageDialog(None, "\n".join(msg), "Updated Config", JOptionPane.INFORMATION_MESSAGE)

        def execute(self, event):
            self.save(event)
            self.Outer.execute()
            self.close(event)

        def close(self, event):
            self.setVisible(false)
            self.dispose()




if __name__ == "__main__":
    # tesing #
    cui = CumulusUI()
    cui.set_config_file(r"C:\Users\u4rs9jsg\projects\rts-utils\test_cumulus.json")
    cui.parameters({"Host": "develop-cumulus-api.corps.cloud", "Scheme": "https"})
    cui.show()
