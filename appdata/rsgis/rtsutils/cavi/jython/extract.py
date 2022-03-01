# Java

from functools import partial
import tempfile
from java.lang import Short
from java.awt import Font, Point
from javax.swing import JDialog, JFrame, JButton, JLabel, JTextField, JList, JCheckBox
from javax.swing import JScrollPane, JOptionPane, SwingConstants
from javax.swing import GroupLayout, LayoutStyle, BorderFactory, WindowConstants
from javax.swing import ListSelectionModel
from javax.swing import ImageIcon
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


def put_ts(site, dss, apart):
    """Save timeseries to DSS File
    
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
    Put to DSS exception handled with a message output saying site not saved, but
    continues on trying additional site/parameter combinations
    """
    
    Site = namedtuple(
        'Site',
        site.keys()
    )(**site)
    parameter, unit, data_type, version = usgs_code[Site.code]
    times = [
        HecTime(t, HecTime.MINUTE_GRANULARITY).value()
        for t in Site.times
    ]
    
    timestep_min = None
    for i, t in enumerate(range(len(times) - 1)):
        ts = abs(times[t + 1] - times[t])
        if ts < timestep_min or timestep_min is None:
            timestep_min = ts
    epart = TimeStep().getEPartFromIntervalMinutes(timestep_min)
    # Set the pathname
    pathname = '/{0}/{1}/{2}//{3}/{4}/'.format(apart, Site.site_number, parameter, epart, version).upper()
    apart, bpart, cpart, _, _, fpart = pathname.split('/')[1:-1]
    
    container = TimeSeriesContainer()
    container.fullName     = pathname
    container.location     = apart
    container.parameter    = parameter
    container.type         = data_type
    container.version      = version
    container.interval     = timestep_min
    container.units        = unit
    container.times        = times
    container.values       = Site.values
    container.numberValues = len(Site.times)
    container.startTime    = times[0]
    container.endTime      = times[-1]
    container.timeZoneID   = tz
    # container.makeAscending()
    if not TimeSeriesMath.checkTimeSeries(container):
        return 'Site: "{}" not saved to DSS'.format(Site.site_number)
    tsc = TimeSeriesFunctions.snapToRegularInterval(container, epart, "0MIN", "0MIN", "0MIN")
    # Put the data to DSS
    try:
        dss.put(tsc)
    except Exception as ex:
        print(ex)
        return 'Site: "{}" not saved to DSS'.format(Site.site_number)


class WaterExtractUI():
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
        sub = go.get(d)
        sub.stdin.write(json.dumps(d))
        byte_array = bytearray()
        for b in iter(partial(sub.stdout.read, 1), b''):
            byte_array.append(b)
            if b == '}':
                obj = json.loads(str(byte_array))
                byte_array = bytearray()
                if 'message' in obj.keys(): raise Exception(obj['message'])
                msg = put_ts(obj, d["dss"], d["apart"])
                if msg: print(msg)



    @classmethod
    def set_config_file(cls, cfg):
        """Set the cumulus configuration file"""
        cls.config_path = cfg


    @classmethod
    def parameters(cls, d):
        cls.go_config.update(d)


    class UI(JFrame):
        def __init__(self):
            super(WaterExtractUI.UI, self).__init__()
            self.Outer = WaterExtractUI()

            if self.Outer.config_path is None:
                JOptionPane.showMessageDialog(None, "No configuration file path provided\n\nExiting program", "Missing Configuration File", JOptionPane.ERROR_MESSAGE)
                sys.exit(1)


            self.config_path = self.Outer.config_path
            self.go_config = self.Outer.go_config

            self.configurations = DictConfig(self.config_path).read()

            self.go_config["Endpoint"] = "watersheds"
            ws_out, stderr = go.get(self.go_config)
            if "error" in stderr:
                print(stderr)
                sys.exit(1)

            self.api_watersheds = self.watershed_refactor(json.loads(ws_out))

#
# ~~~~~~~~~~~~ START OF THE JAVA PANE ~~~~~~~~~~~~
#
            jScrollPane1 = JScrollPane();
            self.lst_watersheds = JList();
            lbl_select_file = JLabel();
            self.txt_select_file = JTextField();
            btn_select = JButton();
            btn_execute = JButton();
            self.cbx_apart = JCheckBox();
            self.txt_apart = JTextField();
            btn_save = JButton();
            btn_close = JButton();

            self.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
            self.setTitle("Extract Time Series Configuration");
            self.setAlwaysOnTop(true);
            self.setIconImage(ImageIcon(EXTRACT_ICON).getImage());
            self.setLocation(Point(10, 10));
            self.setLocationByPlatform(true);
            self.setName("WaterExtractUI");
            self.setResizable(false);


            self.lst_watersheds = JList(sorted(self.api_watersheds.keys()), valueChanged = self.watersheds)
            self.lst_watersheds.setBorder(BorderFactory.createTitledBorder(null, "Watersheds", 2, 2, Font("Tahoma", 0, 14)));
            self.lst_watersheds.setFont(Font("Tahoma", 0, 14));
            self.lst_watersheds.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
            jScrollPane1.setViewportView(self.lst_watersheds);

            lbl_select_file.setFont(Font("Tahoma", 0, 14));
            lbl_select_file.setText("DSS File Downloads");

            self.txt_select_file.setFont(Font("Tahoma", 0, 18));
            self.txt_select_file.setToolTipText("FQPN to output file (.dss)");

            btn_select.setFont(Font("Tahoma", 0, 18));
            btn_select.setText("...");
            btn_select.setToolTipText("Select File...");
            btn_select.actionPerformed = self.select_file;

            btn_execute.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_execute.setText("Save and Execute Configuration");
            btn_execute.setToolTipText("Save and Execute Configuration");
            btn_execute.setHorizontalTextPosition(SwingConstants.CENTER);
            btn_execute.actionPerformed = self.execute;

            btn_save.setFont(Font("Tahoma", 0, 14)); # NOI18N
            btn_save.setText("Save Configuration");
            btn_save.setToolTipText("Save Configuration");
            btn_save.setHorizontalTextPosition(SwingConstants.CENTER);
            btn_save.actionPerformed = self.save;

            btn_close.setFont(Font("Tahoma", 0, 14));
            btn_close.setText("Close");
            btn_close.setToolTipText("Close GUI");
            btn_close.setHorizontalTextPosition(SwingConstants.CENTER);
            btn_close.actionPerformed = self.close;


            self.cbx_apart.setFont(Font("Tahoma", 0, 14));
            self.cbx_apart.setText("DSS A part");
            self.cbx_apart.setToolTipText("DSS A part override");
            self.cbx_apart.actionPerformed = self.check_apart;

            self.txt_apart.setEditable(false);
            self.txt_apart.setFont(Font("Tahoma", 0, 14));
            self.txt_apart.setToolTipText("DSS A part override");

# set the checkbox and checkbox input text field
            try:
                self.txt_apart.setText(self.configurations["apart"])
                if self.configurations["apart"] != "" and self.configurations["watershed_slug"] != self.configurations["apart"]:
                    self.cbx_apart.selected = true
                    self.txt_apart.editable = true

                self.txt_select_file.setText(self.configurations["dss"])
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
                        .addGroup(layout.createSequentialGroup()
                            .addGroup(layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                                .addComponent(self.txt_select_file)
                                .addGroup(layout.createSequentialGroup()
                                    .addComponent(lbl_select_file)
                                    .addGap(0, 0, Short.MAX_VALUE)))
                            .addGap(18, 18, 18)
                            .addComponent(btn_select))
                        .addComponent(jScrollPane1, GroupLayout.DEFAULT_SIZE, 480, Short.MAX_VALUE)
                        .addGroup(layout.createSequentialGroup()
                            .addComponent(self.cbx_apart)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                            .addComponent(self.txt_apart))
                        .addGroup(layout.createSequentialGroup()
                            .addComponent(btn_execute)
                            .addGap(18, 18, 18)
                            .addComponent(btn_save)
                            .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                            .addComponent(btn_close)))
                    .addContainerGap())
            );
            layout.setVerticalGroup(
                layout.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(layout.createSequentialGroup()
                    .addContainerGap()
                    .addComponent(jScrollPane1, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                    .addGap(18, 18, 18)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(self.cbx_apart)
                        .addComponent(self.txt_apart, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
                    .addGap(18, 18, 18)
                    .addComponent(lbl_select_file)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.UNRELATED)
                    .addGroup(layout.createParallelGroup(GroupLayout.Alignment.BASELINE)
                        .addComponent(self.txt_select_file, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE)
                        .addComponent(btn_select))
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED, 17, Short.MAX_VALUE)
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
            if not self.cbx_apart.selected:
                selected_watershed = self.lst_watersheds.getSelectedValue()
                self.txt_apart.setText(self.api_watersheds[selected_watershed]["slug"])

            if not event.getValueIsAdjusting():
                pass
                # print(self.api_watersheds[self.lst_watersheds.getSelectedValue()])

        def watershed_refactor(self, json_):
            return OrderedDict({
                "{}:{}".format(d['office_symbol'], d['name']): d 
                for d in json_
                })
        
        def watershed_index(self, wss, d):
            idx = None
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


        def check_apart(self, event):
            self.txt_apart.editable = self.cbx_apart.selected


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

            watershed_id = self.api_watersheds[selected_watershed]["id"]
            watershed_slug = self.api_watersheds[selected_watershed]["slug"]


            # Get, set and save jutil.configurations
            self.configurations["watershed_id"] = watershed_id
            self.configurations["watershed_slug"] = watershed_slug
            self.configurations["apart"] = self.txt_apart.getText()
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

    cui = WaterExtractUI()
    cui.set_config_file(r"C:\Users\u4rs9jsg\projects\rts-utils\test_extract.json")
    cui.parameters({"Host": "develop-water-api.corps.cloud", "Scheme": "https"})
    cui.show()
