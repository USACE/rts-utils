# Java
from itertools import product
import json
import os
import sys
from java.lang import Short
from java.awt import Font, Point
from javax.swing import JFrame, JButton, JLabel, JTextField, JList
from javax.swing import JScrollPane
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon

false = 0
true = 0
null = None

icon = os.path.join(os.path.dirname(__file__), "cloud.png")


class CumulusAPI():
    def __init__(self):
        pass
    
    def watersheds(self, tmp_file):
        with open(tmp_file, "rb") as f:
            return self.ws_refactor(json.load(f))
    
    def ws_refactor(self, json_):
        return {
            "{}:{}".format(d['office_symbol'], d['name']): d 
            for d in json_
            }

    def products(self, tmp_file):
        with open(tmp_file, "rb") as f:
            return self.ps_refactor(json.load(f))

    def ps_refactor(self, json_):
        return {
            "{}".format(d['name'].replace("_", " ").title()): d 
            for d in json_
            }

class CumulusUI(JFrame):
    def __init__(self, cfg, api_ws, api_ps):
        super(CumulusUI, self).__init__()

        cumulus_api = CumulusAPI()
        api_watersheds = cumulus_api.watersheds(api_ws)
        api_products = cumulus_api.products(api_ps)

        btn_save = JButton();
        txt_select_file = JTextField();
        btn_select = JButton();
        lbl_select_file = JLabel();
        jScrollPane1 = JScrollPane();
        lst_products = JList();
        jScrollPane2 = JScrollPane();
        self.lst_watersheds = JList();

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        self.setTitle("Cumulus Configuration");
        self.setIconImage(ImageIcon(icon).getImage());
        self.setLocation(Point(10, 10));
        self.setLocationByPlatform(1);
        self.setName("CumulusCaviUi");
        self.setResizable(0);

        btn_save.setFont(Font("Tahoma", 0, 18));
        btn_save.setText("Save Configuration");
        btn_save.setActionCommand("submit");

        txt_select_file.setFont(Font("Tahoma", 0, 18));
        txt_select_file.setToolTipText("FQPN to output file (.dss)");

        btn_select.setFont(Font("Tahoma", 0, 18));
        btn_select.setText("...");
        btn_select.setToolTipText("Select File...");

        lbl_select_file.setText("DSS File Downloads");

        lst_products.setBorder(BorderFactory.createTitledBorder(None, "Products", 2, 2, Font("Tahoma", 0, 14)));
        lst_products.setFont(Font("Tahoma", 0, 14));
        jScrollPane1.setViewportView(lst_products);

        self.lst_watersheds = JList(sorted(api_watersheds.keys()), valueChanged = self.watersheds)
        self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(None, "Watersheds", 2, 2, Font("Tahoma", 0, 14)));
        self.lst_watersheds.setFont(Font("Tahoma", 0, 14));
        self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

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
                        .addComponent(txt_select_file, GroupLayout.PREFERRED_SIZE, 399, GroupLayout.PREFERRED_SIZE)
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
                    .addComponent(txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addComponent(btn_select))
                .addGap(18, 18, 18)
                .addComponent(btn_save)
                .addContainerGap())
        );

        self.pack()
        self.setLocationRelativeTo(None)

    def watersheds(self, event):
        index = self.lst_watersheds.selectedIndex
        # if not event.getValueIsAdjusting():
        #     _dict = self.basin_meta[self.lst_watershed.getSelectedValue()]

    @property
    def products(self):
        pass
    
    @products.getter
    def products(self):
        pass

    @property
    def dssfile(self):
        pass
    
    @dssfile.getter
    def dssfile(self):
        pass


    def save(self):
        pass



if __name__ == "__main__":
    # api files are actually temp files from Go download
    cui = CumulusUI(
        "cumulus.json",
        r"C:\Users\dev\projects\jython\api_watersheds.json",
        r"C:\Users\dev\projects\jython\api_products.json"
    )
    cui.setVisible(1)

    # capi = CumulusAPI()
    # ws_dict = capi.watersheds(r"C:\Users\dev\projects\jython\api_watersheds.json")
    # ps_dict = capi.products(r"C:\Users\dev\projects\jython\api_products.json")
    
    
    # print(sorted(ps_dict.keys()))