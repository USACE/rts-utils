"""
Extract timeseries data from Water API and save to DSS file
"""

import os
from functools import partial
import json
from string import Template

import java.lang.Class
import java.sql.DriverManager
import java.sql.SQLException
import javax.swing.JOptionPane

from hec.heclib.util import HecTime

from rtsutils import go
from rtsutils.cavi.jython import jutil, status
from rtsutils import USGS_SQL_DB

# set the provider
PROVIDER = "" # your district (MSC)

# set the group
GROUP = "" # timeseries_group defined in Water API

# DSS APART default is an empty string
apart = ""

# set the dss file, A part, and B part
DSSFILENAME = os.path.join(
    status.get_database_directory(),
    "data.dss"
)

USGS_TIMESERIES = "usgs-timeseries"
CWMS_TIMESERIES = "cwms-timeseries"

# SQLITE, JDBC, and Queries
JDBC_URL = "jdbc:sqlite:%s"  % USGS_SQL_DB
JDBC_DRIVER = "org.sqlite.JDBC"
DSS_ATTR_QUERY = Template("""
SELECT dss_parameter, dss_type, dss_unit
FROM dss as d
WHERE d.usgs_code_id = (SELECT id FROM parameter_code as pc WHERE pc.code = '${PCODE}');
""")

# set the scheme, host, and timeout
SCHEME = "https"
HOST = "water-api.corps.cloud"
TIMEOUT = 300

# get the time window
# after = "" # "YYYY-MM-DDTHH:MM:SSZ"
# before = "" # "YYYY-MM-DDTHH:MM:SSZ"
tw = status.get_timewindow()
if tw != None:
    st, et = tw
    after_hec = HecTime(st)
    before_hec = HecTime(et)
    after = "%d-%02d-%02dT%02d:%02d:00Z" % (after_hec.year(), after_hec.month(), after_hec.day(), after_hec.hour(),after_hec.minute())
    before = "%d-%02d-%02dT%02d:%02d:00Z" % (before_hec.year(), before_hec.month(), before_hec.day(), before_hec.hour(),before_hec.minute())
    print("Time window: {}".format(tw))
else:
    msg = "No Forecast open or in \"Setup Tab\""
    javax.swing.JOptionPane.showMessageDialog(
        None,
        msg,
        "No Forecast",
        javax.swing.JOptionPane.ERROR_MESSAGE,
    )
    raise Exception(msg)


# Go Configurations
ENDPOINT = Template("providers/${PROVIDER}/timeseries_groups/${GROUP}/values")
CONFIG = {
    "Scheme": SCHEME,
    "Host": HOST,
    "StdOut": "true",
    "Subcommand": "extract",
    "Endpoint": ENDPOINT.substitute(PROVIDER=PROVIDER, GROUP=GROUP),
    "After": after,
    "Before": before,
    "Timeout": 600,
}


# get the data and save
sub = go.get(out_err=False, is_shell=False)

sub.stdin.write(json.dumps(CONFIG))
sub.stdin.close()

byte_array = bytearray()
stmt = None
conn = None
# prepare sqlite db if needed with USGS datatype
try:
    java.lang.Class.forName(JDBC_DRIVER).newInstance()
except Exception as e:
    raise

for iter_byte in iter(partial(sub.stdout.read, 1), b""):
    byte_array.append(iter_byte)
    if iter_byte == "}":
        bpart = ""
        cpart = ""
        unit = ""
        datatype = ""

        obj = json.loads(str(byte_array))
        byte_array = bytearray()

        dtype = obj["datatype"]
        key_parts = obj["key"].split(".")
        times, values = list(zip(*obj["values"]))
        try:
            if conn is None or conn.isClosed():
                conn = java.sql.DriverManager.getConnection(JDBC_URL)
        except java.sql.SQLException as e:
            raise

        try:
            stmt = conn.createStatement()
            if dtype == USGS_TIMESERIES:
                bpart, pcode = key_parts
                result_set = stmt.executeQuery(DSS_ATTR_QUERY.substitute(PCODE=pcode))
                while result_set.next():
                    cpart = result_set.getString("dss_parameter")
                    datatype = result_set.getString("dss_type")
                    unit = result_set.getString("dss_unit")
                    break

            elif dtype == CWMS_TIMESERIES:
                loc, para, ptype, interval, dur, version = key_parts
            else:
                raise Exception("Datatype {} not supported".format())
        except Exception as e:
            print(e)

        hec_times = [
            HecTime(t, HecTime.MINUTE_GRANULARITY).value()
            for t in times
        ]

        msg = jutil.put_timeseries(
            dssfilename=DSSFILENAME,
            apart=apart,
            bpart=bpart,
            cpart=cpart,
            fpart=USGS_TIMESERIES,
            unit=unit,
            datatype=datatype,
            times=hec_times,
            values=list(values)
        )

        if msg:
            print(msg)

if stmt:
    stmt.close()
if conn:
    conn.close()

std_err = sub.stderr.read()
sub.stderr.close()
sub.stdout.close()
print(std_err)
if "error" in std_err:
    javax.swing.JOptionPane.showMessageDialog(
        None,
        std_err.split("::")[-1],
        "Error",
        javax.swing.JOptionPane.ERROR_MESSAGE,
    )
    quit()

javax.swing.JOptionPane.showMessageDialog(
    None,
    "Program Done",
    "Program Done",
    javax.swing.JOptionPane.INFORMATION_MESSAGE,
)
