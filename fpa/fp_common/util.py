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
