# util.py
# Michael Kirk 2014
#
# Handy functions.
#

import time

def isInt(x):
    try:
        int(x)
        return True
    except ValueError:
        return False

def isNumeric(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

def epoch2dateTime(timestamp):
# Return readable date/time string from timestamp (assumed to be in milliseconds).
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000))

def formatJapDate(jdate):
    year = jdate / 10000
    month = (jdate % 10000) / 100
    day = jdate % 100
    return '{0}/{1}/{2}'.format(day, month, year)

ldbg = False
def ldebug(txt):
#-------------------------------------------------------------------------------------------------
# For debug output when running locally for debugging. Prints message if ldbg true.
    if ldbg:
        print txt

def fpLog(app, msg):
#-------------------------------------------------------------------------------------------------
# Write to fplog
# Could put switch here to turn logging on/off, or set level.
# Maybe should record IP address if we have it.
# app is expected to be the wsgi app, and it should have a config
# variable FPLOG_FILE specifying the full path to the file to log to.
# The msg is appended to that file.
#
    try:     # Don't crash out if logging not working
        f = open(app.config['FPLOG_FILE'], 'a')
        print >>f, '{0}\t{1}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), msg)
        f.close
    except Exception, e:
        pass
