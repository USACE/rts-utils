from hec.heclib.dss  import HecDss
from hec.heclib.util import Heclib
from hec.heclib.util import HecTime
from hec.io          import TimeSeriesContainer
from hec.script      import Constants
from java.lang       import System
from java.text       import SimpleDateFormat
from java.util       import Calendar
from java.util       import TimeZone
import getopt, json, os, re, string, sys, traceback, urllib2

progName  = os.path.split(sys.argv[0])[1]
version   = "1.1"
verDate   = "03-Jul-2019"
sdfOutput = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS ")

'''
Version history
    1.0  11-Jun-2019 MDP Initial version

    1.1  03-Jul-2019 MDP Improved error handling
                         Added listing of time series not retrieved
'''

def output(message, continuation=False, newline=True) :
	'''
	Outputs a message with a time stamp
	'''
	global lastNewLine
	prefix1 = sdfOutput.format(System.currentTimeMillis())
	prefix2 = " " * len(prefix1)
	prefix3 = ""
	prefix = prefix1
	if continuation :
		try :
			if not lastNewLine : prefix = prefix3
			else               : prefix = prefix2
		except :
			lastNewLine = True

	lines = message.split("\n")
	sys.stdout.write("%s%s" % (prefix, lines[0]))
	for i in range(1, len(lines)) :
		sys.stdout.write("\n%s%s" % (prefix2, lines[i]))
	if newline : sys.stdout.write("\n")
	lastNewLine = newline

def usage(message=None) :
	'''
	Spew a usage blurb (with an optional message) and exit
	'''
	blurb = '''
	%s v %s (%s) - retrieves time series from CWMS RADAR web service and stores to DSS

	Usage   : %s [options]

	Options : -i infile
	          --in infile
	              Specifies the input file which has a lines formatted as :
	                 <office>/<CWMS time series ID> = <dss pathname>
	              Defaults to stdin (piped or redirected input).
	              Blank lines and lines starting with "#" are ignored.

	          -d dssfile
	          --dss-file dssfile
	              Specifies the HEC-DSS file to write to. Defaults to
	              cwms-data.dss in the current directory.

	          -v version
	          --dss-version version
	              Specifies the version of HEC-DSS file to create if the file
	              doesn't already exist. Must be 6 or 7. Defaults to 7.

	          -b begin_time
	          --begin begin_time
	              Specifies the beginning of the time window to retrieve.
	              Must be in web time format yyyy-mm-dd[Thh[:mm][:ss]], e.g.,
	                  2019-05-15, 2019-02-28T04:00
		      or in web duration format for time offset before current, e.g.,
	                  P30D, P7D, P16H, P1D4H
	              Defaults to 24 hours before current time.

	          -e end_time
	          --end end_time
	              Specifies the ending of the time window to retrieve.
	              Must be in web time format yyyy-mm-dd[Thh[:mm][:ss]], e.g.,
	                  2019-05-15, 2019-02-28T04:00
		      or in web duration format for time offset before current, e.g.,
	                  P30D, P7D, P16H, P1D4H
	              Defaults to current time.

	          -z time_zone
	          --tz time_zone
	              Specifies the time zone. This is used to interpretet the
	              begin_time and end_time, as well as the times of the values
	              retrieved. Defaults to UTC.
	''' % (progName, version, verDate, progName)
	if message : print("\n%s" % message)
	print(blurb)
	exit()

def makeTimeSeriesContainer(tsData, timeZone, pathname=None) :
	'''
	Construct a TimeSeriesContainer object from a python dictionary that was
	created from a single "time-series" returned from the CWMS RADAR web
	service
	'''
	#---------------#
	# initial setup #
	#---------------#
	tsc = None
	try :
		tz = TimeZone.getTimeZone(timeZone)
		sdf8601 = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX")
		sdfHecTime = SimpleDateFormat("ddMMMyyyy, HH:mm")
		cal = Calendar.getInstance()
		for obj in sdf8601, sdfHecTime, cal :
			obj.setTimeZone(tz)
		ht = HecTime()
		times, values, qualities = [], [], []
		#------------------#
		# process the data #
		#------------------#
		if tsData.has_key("regular-interval-values") :
			#----------------------------------------#
			# regular time series (a lot to process) #
			#----------------------------------------#
			rts = tsData["regular-interval-values"]
			intvlStr = rts["interval"]
			unit = rts["unit"].split()[0]
			if intvlStr.startswith("PT") :
				intvlNum, intvlUnit = int(intvlStr[2:-1]), intvlStr[-1]
				try :
					factor, field = {
						"M" : ( 1, Calendar.MINUTE),
						"H" : (60, Calendar.HOUR_OF_DAY)
					}[intvlUnit]
				except KeyError :
					raise Exception("Unexpected interval: %s" % intvlStr)
			else :
				intvlNum, intvlUnit = int(intvlStr[1:-1]), intvlStr[-1]
				try :
					factor, field = {
						"Y" : (1440 * 365, Calendar.YEAR),
						"M" : (1440 * 30,  Calendar.MONTH),
						"D" : (1440,       Calendar.DATE)
					}[intvlUnit]
				except KeyError :
					raise Exception("Unexpected interval: %s" % intvlStr)
			intvl = intvlNum * factor
			segmentCount = rts["segment-count"]
			cal.setTimeInMillis(sdf8601.parse(rts["segments"][0]["first-time"]).getTime())
			for i in range(segmentCount) :
				for j in range(rts["segments"][i]["value-count"]) :
					ht.set(sdfHecTime.format(cal.getTimeInMillis()))
					v, q = rts["segments"][i]["values"][j]
					times.append(ht.value())
					values.append(v)
					qualities.append(q)
					cal.add(field, intvlNum)
				if i < segmentCount - 1 :
					nextBegin = sdf8601.parse(rts["segments"][i+1]["first-time"]).getTime()
					time = cal.getTimeInMillis()
					while time < nextBegin :
						ht.set(sdfHecTime.format(time))
						times.append(ht.value())
						values.append(Constants.UNDEFINED)
						qualities.append(0)
						cal.add(field, intvlNum)
						time = cal.getTimeInMillis()
		elif tsData.has_key("irregular-interval-values") :
			#------------------------------#
			# irregular time series (easy) #
			#------------------------------#
			its = tsData["irregular-interval-values"]
			unit = its["unit"].split()[0]
			intvl = 0
			for t, v, q in its["values"] :
				ht.set(sdfHecTime.format(sdf8601.parse(t)))
				times.append(ht.value())
				values.append(v)
				qualities.append(q)
		else :
			raise Exception("Time series has no values")
		#--------------------------------------------------#
		# code common to regular and irregular time series #
		#--------------------------------------------------#
		tsc = TimeSeriesContainer()
		tsc.times             = times
		tsc.values            = values
		tsc.quality           = qualities
		tsc.numberValues      = len(times)
		tsc.startTime         = times[0]
		tsc.endTime           = times[-1]
		tsc.interval          = intvl
		tsc.units             = unit
		tsc.timeZoneID        = timeZone
		tsc.timeZoneRawOffset = tz.getRawOffset()

		name = tsData["name"]
		loc, param, paramType, intv, dur, ver = name.split(".")
		if pathname :
			#---------------------------#
			# use pathname if specified #
			#---------------------------#
			A, B, C, D, E, F = 1, 2, 3, 4, 5, 6
			parts = pathname.split("/")
			parts[D] = ''
			tsc.fullName = "/".join(parts)
			tsc.watershed = parts[A]
			try    : tsc.location, tsc.subLocation = parts[B].split("-", 1)
			except : tsc.location = parts[B]
			try    : tsc.parameter, tsc.subParameter = parts[C].split("-", 1)
			except : tsc.parameter = parts[C]
			try    : tsc.version, tsc.subVersion = parts[F].split("-", 1)
			except : tsc.version = parts[F]
		else :
			#--------------------------------------#
			# no pathname, use CWMS time series id #
			#--------------------------------------#
			try    : tsc.location, tsc.subLocation = loc.split("-", 1)
			except : tsc.location = loc
			try    : tsc.parameter, tsc.subParameter = param.split("-", 1)
			except : tsc.parameter = param
			try    : tsc.version, tsc.subVersion = ver.split("-", 1)
			except : tsc.version = ver
		tsc.type = {
			"Total" : "PER-CUM",
			"Max"   : "PER-MAX",
			"Min"   : "PER-MIN",
			"Const" : "INST-VAL",
			"Ave"   : "PER-AVER",
			"Inst"  : ("INST-VAL", "INST-CUM")[param.startswith("Precip")]
		}[paramType]
	except :
		output(traceback.format_exc())
	return tsc

def main() :
	#-------#
	# setup #
	#-------#
	reTime       = re.compile("^((?:[0-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])$", re.I)
	reDuration   = re.compile("^(-?)P(?=\d|T\d)(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)([DW]))?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$", re.I)
	reInputLine  = re.compile("^((\w+)\s*/\s*((?:[^.]+[.]){5}[^.]+?))\s*=\s*((?:/(.*)){6}/)$")
	inFileName   = None
	dssFileName  = "cwms-data.dss"
	dssVersion   = 7
	beginTime    = None
	endTime      = None
	duration     = None
	timeZoneStr  = None
	timeZone     = None
	beginTimeCal = None
	endTimeCal   = None
	inputLines   = None
	timeseries   = {}
	urlTemplate  = "http://cwms-data.usace.army.mil/cwms-data/timeseries?office=%s&name=%s&begin=@&end=@&timezone=@&format=json"
	#--------------------------#
	# process the command line #
	#--------------------------#
	try :
		opts, args = getopt.getopt(sys.argv[1:], "i:d:v:b:e:z:", ["in=", "dss-file=", "dss-version=", "begin=", "end=", "tz="])
		if args : raise Exception("Unexpected argument(s) encountered: %s" % args)
	except Exception as exc :
		usage(str(exc))
	for opt, arg in opts :
		if   opt in ("-i", "--in")          : inFileName  = arg
		elif opt in ("-d", "--dss-file")    : dssFileName = arg
		elif opt in ("-v", "--dss-version") : dssVersion  = arg
		elif opt in ("-b", "--begin")       : beginTime   = arg
		elif opt in ("-e", "--end")         : endTime     = arg
		elif opt in ("-z", "--tz")          : timeZoneStr = arg
	#--------------------#
	# validate arguments #
	#--------------------#
	try :
		dssVersion = int(dssVersion)
		if dssVersion not in (6, 7) : raise Exception
	except :
		usage("Invalid DSS version: %s" % dssVersion)
	if beginTime :
		if not reTime.match(beginTime) and not reDuration.match(beginTime) :
			usage("Invalid time for begin_time: %s" % beginTime)
#		if not beginTime.startswith("-") and not beginTime.upper().startswith("P-") :
#			beginTime = "-%s" % beginTime
		urlTemplate = urlTemplate.replace("&begin=@", "&begin=%s" % beginTime)
	else :
		urlTemplate = urlTemplate.replace("&begin=@", "")
	if endTime :
		if not reTime.match(endTime) and not reDuration.match(endTime) :
			usage("Invalid time for end_time: %s" % endTime)
#		if not endTime.startswith("-") and not endTime.upper().startswith("P-") :
#			endTime = "-%s" % endTime
		urlTemplate = urlTemplate.replace("&end=@", "&end=%s" % endTime)
	else :
		urlTemplate = urlTemplate.replace("&end=@", "")
	if timeZoneStr :
		try :
			timeZone = TimeZone.getTimeZone(timeZoneStr).getID()
		except Exception as exc :
			usage("Invalid time_zone: %s" % timeZoneStr)
	else :
		timeZone = TimeZone.getTimeZone("UTC").getID()
	urlTemplate = urlTemplate.replace("&timezone=@", "&timezone=%s" % timeZone)
	Heclib.zset("MLVL", "", 0)
	Heclib.zset("DSSV", "", dssVersion)
	output("%s %s (%s) starting up" % (progName, version, verDate))
	output("Will store data to %s" % dssFileName)
	#----------------------#
	# parse the input file #
	#----------------------#
	try :
		if inFileName :
			output("Reading %s" % inFileName)
			with open(inFileName) as f : lines = f.read().strip().split("\n")
		else :
			output("Reading stdin")
			lines = sys.stdin.read().strip().split("\n")
	except Exception as exc :
		usage(str(exc))
	for line in [line for line in [line.strip() for line in lines] if line and not line.startswith("#")] :
		m = reInputLine.match(line)
		if not m :
			output("Invalid input line: %s" % line)
			continue
		timeseries.setdefault(m.group(2), {})[m.group(3)] = m.group(4)
	#-------------------#
	# retrieve the data #
	#-------------------#
	jsonData = []
	names = []
	for office in sorted(timeseries.keys()) :
		nameStr = ""
		count = 0
		for tsid in sorted(timeseries[office].keys()) :
			if nameStr and len(nameStr) + len(tsid) > 1500 :
				output("Retrieving %d time series for office %s" % (count, office))
				url = urlTemplate % (office, nameStr)
				session = urllib2.urlopen(url.replace(" ", "%20"))
				names.append((office, nameStr))
				jsonData.append(session.read())
				session.close()
				nameStr = ""
				count = 0
			else :
				if nameStr : nameStr += "|"
				nameStr += tsid
				count += 1
		if nameStr :
			output("Retrieving %d time series for office %s" % (count, office))
			url = urlTemplate % (office, nameStr)
			session = urllib2.urlopen(url.replace(" ", "%20"))
			names.append((office, nameStr))
			jsonData.append(session.read())
			session.close()
			nameStr = ""
			count = 0
	#--------------#
	# write to DSS #
	#--------------#
	processed = set()
	if jsonData :
		dssFile = HecDss.open(dssFileName)
		for i in range(len(jsonData)) :
			office, tsids = names[i]
			try :
				obj = json.loads(jsonData[i])
			except ValueError :
				tsids = tsids.split("|")
				output("Error retrieving data for these time series for %s:\n\t%s\nData = %s" % (office, "\n\t".join(tsids), jsonData[i]))
			timeSeriesData = obj["time-series"]["time-series"]
			for j in range(len(timeSeriesData)) :
				tsid = timeSeriesData[j]["name"]
				pathname = timeseries[office][tsid]
				output("Processing %s/%s" % (office, tsid), newline=False)
				tsc = makeTimeSeriesContainer(timeSeriesData[j], timeZone, pathname)
				if tsc :
					processed.add((office, tsid))
					output(" .. %d values stored to %s" % (tsc.numberValues, tsc.fullName), continuation=True)
					dssFile.put(tsc)
		dssFile.close()
		no_data = {}
		for office in timeseries.keys() :
			for tsid in timeseries[office].keys() :
				if (office, tsid) not in processed : no_data.setdefault(office, []).append(tsid)
		if no_data :
			output("No data were retrieved for the following:")
			for office in sorted(no_data.keys()) :
				for tsid in sorted(no_data[office]) :
					output("    %s/%s = %s" % (office, tsid, timeseries[office][tsid]), continuation=True)
		output("%s %s (%s) Done" % (progName, version, verDate))


if __name__ == "__main__" :
    main()
