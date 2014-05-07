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
