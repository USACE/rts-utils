"""Cumulus UI
"""

from java.lang import Short
from java.awt import Font, Point
from javax.swing import JFrame, JButton, JLabel, JTextField, JList
from javax.swing import JScrollPane, JOptionPane, SwingConstants
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, JRootPane
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon
import javax.swing.border as border

from java.io import File


import os
import json
import sys
from collections import OrderedDict


from rtsutils import go, TRUE, FALSE, null
from rtsutils.cavi.jython import jutil
from rtsutils.utils import CLOUD_ICON
from rtsutils.utils.config import DictConfig


class CumulusUI():
    go_config = {
        "Scheme": "https",
        "Subcommand": "get",
        "StdOut": "true",
    }
    config_path = None

    def show(self):
        self.ui = self.UI()
        self.ui.setVisible(TRUE)

    @classmethod
    def execute(cls, cfg):
        stdout, stderr = go.get(cfg, subprocess_=FALSE)
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

            # self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE); 
            self.setTitle("Cumulus Configuration");
            self.setAlwaysOnTop(TRUE);
            self.setIconImage(ImageIcon(CLOUD_ICON).getImage());
            self.setLocation(Point(10, 10));
            self.setLocationByPlatform(TRUE);
            self.setName("CumulusCaviUI"); # NOI18N
            self.setResizable(FALSE);

            self.lst_products = JList(sorted(self.api_products.keys()), valueChanged = self.products)
            self.lst_products.setBorder(BorderFactory.createTitledBorder(null, "Products", border.TitledBorder.CENTER, border.TitledBorder.TOP, Font("Tahoma", 0, 14))); # NOI18N
            self.lst_products.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.lst_products.setToolTipText("List of products");
            jScrollPane1.setViewportView(self.lst_products);

            self.lst_watersheds = JList(sorted(self.api_watersheds.keys()), valueChanged = self.watersheds)
            self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(null, "Watersheds", border.TitledBorder.CENTER, border.TitledBorder.TOP, Font("Tahoma", 0, 14))); # NOI18N
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            self.lst_watersheds.setToolTipText("List of watersheds");
            jScrollPane2.setViewportView(self.lst_watersheds);

            lbl_select_file.setFont(Font("Tahoma", 0, 14)); # NOI18N
            lbl_select_file.setText("DSS File Downloads");

            self.txt_select_file.setFont(Font("Tahoma", 0, 14)); # NOI18N
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)");

            btn_select.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_select.setText("...");
            btn_select.setToolTipText("Select File...");
            btn_select.actionPerformed = self.select_file;

            btn_execute.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_execute.setText("Save and Execute Configuration");
            btn_execute.setToolTipText("Save and Execute Configuration");
            btn_execute.actionPerformed = self.execute;
            btn_execute.setHorizontalTextPosition(SwingConstants.CENTER);

            btn_save.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_save.setText("Save Configuration");
            btn_save.setToolTipText("Save Configuration");
            btn_save.actionPerformed = self.save;
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER);

            btn_close.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_close.setText("Close");
            btn_close.setToolTipText("Close GUI");
            btn_close.actionPerformed = self.close;
            btn_close.setHorizontalTextPosition(SwingConstants.CENTER);
            
            try:
                self.txt_select_file.setText(self.configurations["dss"])
                idxs = self.product_index(self.configurations["product_ids"], self.api_products)
                self.lst_products.setSelectedIndices(idxs)
                idx = self.watershed_index(self.configurations["watershed_id"], self.api_watersheds)
                self.lst_watersheds.setSelectedIndex(idx)
            except KeyError as ex:
                print("KeyError: missing {}".format(ex))


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
            self.setLocationRelativeTo(null)
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


            jf = JFrame()
            jf.setAlwaysOnTop(TRUE)
            JOptionPane.showMessageDialog(jf, "\n\n".join(msg), "Updated Config", JOptionPane.INFORMATION_MESSAGE)


        def execute(self, event):
            self.save(event)
            self.Outer.go_config["Subcommand"] = "grid"
            self.Outer.go_config["Slug"] = self.configurations["watershed_slug"]
            self.Outer.go_config["Products"] = self.configurations["product_ids"]
            self.Outer.execute(self.Outer.go_config)
            self.close(event)

        def close(self, event):
            self.dispose()
            sys.exit()


if __name__ == "__main__":
    # tesing #
    cui = CumulusUI()
    cui.set_config_file(r"C:\Users\dev\projects\rts-utils\test_cumulus.json")
    cui.parameters({"Host": "develop-cumulus-api.corps.cloud", "Scheme": "https"})
    cui.show()
