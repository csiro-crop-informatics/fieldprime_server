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

###  Logging: ##################################################################
# We want a logging system that can be turned on or off by use of a flag file:
# 'dolog' in the app.config[FP_FLAG_DIR] folder.
#

ldbg = False
def ldebug(txt):
#-------------------------------------------------------------------------------------------------
# For debug output when running locally for debugging. Prints message if ldbg true.
    if ldbg:
        print txt

def flog(msg) :
# Logging function called externally, initLogging should be called first.
# This default version does nothing, but may be overwritten.
    pass

def initLogging(app):
    import os.path
    if os.path.isfile(app.config['FP_FLAG_DIR'] + "/dolog"):
        global flog
        # Lookup the logging file name, create a function to log to it, and
        # set the flog module global func to that function. So hopefully
        # the module namespace will not end up with either logfilename or
        # flogServer in it, but the function will work nonetheless.
        logfilename = app.config['FPLOG_FILE']
        def flogServer(msg):
            try:     # Don't crash out if logging not working
                f = open(logfilename, 'a')
                print >>f, '{0}\t{1}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), msg)
                f.close
            except Exception, e:
                pass
        flog = flogServer


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

################################################################################
