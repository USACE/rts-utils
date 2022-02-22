# Java
from java.lang import Short
from java.awt import Font, Point
from javax.swing import JFrame, JButton, JLabel, JTextField, JList
from javax.swing import JScrollPane
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon

import util


false = 0
true = 0
null = None


class CumulusUI(JFrame):
    def __init__(self, cfg):
        super(CumulusUI, self).__init__()

        # self.cfg = cfg
        self.cfg_in = util.configuration(cfg)
        
        self.api_watersheds = cumulus_api.watersheds(api_ws)
        self.api_products = cumulus_api.products(api_ps)

        btn_save = JButton();
        self.txt_select_file = JTextField();
        btn_select = JButton();
        lbl_select_file = JLabel();
        jScrollPane1 = JScrollPane();
        self.lst_products = JList();
        jScrollPane2 = JScrollPane();
        self.lst_watersheds = JList();

        self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        self.setTitle("Cumulus util.configuration");
        self.setIconImage(ImageIcon(ICON).getImage());
        self.setLocation(Point(10, 10));
        self.setLocationByPlatform(1);
        self.setName("CumulusCaviUi");
        self.setResizable(0);

        btn_save.setFont(Font("Tahoma", 0, 18));
        btn_save.setText("Save util.configuration");
        btn_save.setActionCommand("save");
        btn_save.actionPerformed = self.save;


        self.txt_select_file.setFont(Font("Tahoma", 0, 18));
        self.txt_select_file.setToolTipText("FQPN to output file (.dss)");
        self.txt_select_file.setText(self.cfg_in["dss"])

        btn_select.setFont(Font("Tahoma", 0, 18));
        btn_select.setText("...");
        btn_select.setToolTipText("Select File...");
        btn_select.actionPerformed = self.dssfile;

        lbl_select_file.setText("DSS File Downloads");

        self.lst_products = JList(sorted(self.api_products.keys()), valueChanged = self.products)
        self.lst_products.setBorder(BorderFactory.createTitledBorder(None, "Products", 2, 2, Font("Tahoma", 0, 14)));
        self.lst_products.setFont(Font("Tahoma", 0, 14));
        jScrollPane1.setViewportView(self.lst_products);

        self.lst_watersheds = JList(sorted(self.api_watersheds.keys()), valueChanged = self.watersheds)
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

    def products(self, event):
        index = self.lst_products.selectedIndex
        if not event.getValueIsAdjusting():
            pass
            # print(self.api_products[self.lst_products.getSelectedValue()])

    def dssfile(self, event):
        fc = FileChooser(self.txt_select_file)
        fc.title = "Select Output DSS File"
        # _dir = os.path.dirname(self.dss_path)
        # fc.set_current_dir(File(_dir))
        fc.show()
        print(fc.selectedFile)

    def save(self, event):
        selected_watershed = self.lst_watersheds.getSelectedValue()
        selected_products = self.lst_products.getSelectedValues()
        
        watershed_slug = self.api_watersheds[selected_watershed]["slug"]
        product_ids = [self.api_products[p]["id"] for p in selected_products]
        
        
        # Get, set and save util.configurations
        self.cfg_in["watershed_slug"] = watershed_slug
        self.cfg_in["product_ids"] = product_ids
        self.cfg_in["dss"] = self.txt_select_file
        util.configuration(self.cfg, self.cfg_in)
        


if __name__ == "__main__":
    # api files are actually temp files from Go download
    cui = CumulusUI(
        r"C:\Users\dev\projects\jython\cumulus.json",
        r"C:\Users\dev\projects\jython\api_watersheds.json",
        r"C:\Users\dev\projects\jython\api_products.json"
    )
    cui.setVisible(1)

    # capi = CumulusAPI()
    # ws_dict = capi.watersheds(r"C:\Users\dev\projects\jython\api_watersheds.json")
    # ps_dict = capi.products(r"C:\Users\dev\projects\jython\api_products.json")
    
    
    # print(sorted(ps_dict.keys()))