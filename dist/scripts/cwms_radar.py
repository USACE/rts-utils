"""CWMS Radar Data to DSS
"""

import os

import threading

from rtsutils.cavi.jython import status
from rtsutils.cwmsradar import CwmsRADAR

from hec.heclib.util import HecTime
from hec.script import MessageBox

#
tw = status.get_timewindow()
if tw != None:
	st, et = tw
	print("Time window: {}".format(tw))
else:
	MessageBox.showError("No Forecast open or in 'Setup Tab'")
	raise Exception("No Forecast open or in 'Setup Tab'")

class RadarThread(threading.Thread):
	def __init__(self, st, et, tsid, dssid):
		threading.Thread.__init__(self)
		self.st = st
		self.et = et
		self.tsid = tsid
		self.dssid = dssid

	def run(self):
		radar(self.st, self.et, self.tsid, self.dssid)

def radar(st, et, tsid, dssid):
		cwmsdat = CwmsRADAR()
		cwmsdat.begintime = cwmsdat.format_datetime(HecTime(st))
		cwmsdat.endtime = cwmsdat.format_datetime(HecTime(et))
		cwmsdat.dssfile = os.path.join(
			status.get_database_directory(),
			"data.dss"
		)
		cwmsdat.set_tsids([tsid.strip()], [dssid.strip()])
		cwmsdat.run()

with open(os.path.join(status.get_shared_directory(), "cwms_radar.config")) as fp:
	for line in fp.readlines():
		tsid, dssid = line.split(":")
		t = RadarThread(st, et, tsid, dssid)
		t.start()
		t.join()

MessageBox.showInformation("Script Done", "Script Done")
