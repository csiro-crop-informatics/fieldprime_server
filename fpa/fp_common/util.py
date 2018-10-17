# util.py
# Michael Kirk 2014
#
# Handy functions.
#

import time, sys, os
import cgi
import re
import logging
from functools import wraps

def fpServerDown():
    '''
    Return status of FieldPrime Server

    Creation of file fpdown in flagdir will result in server 
    down for maintenance message.
    '''
  
    from config import FP_LOG_DIR 
    fpdown = os.path.isfile(FP_LOG_DIR + "/fpdown")

    return fpdown

def activateVirtualenv(virt_activate_file=os.environ.get('FP_VIRTUALENV',None)):
    '''
    Activate Python Virtualenv

    Uses python virtualenv activate_this.py location to enable python virtual environment
    Only used in app entrypoint .wsgi. Uses environment variable FP_VIRTUALENV or 
    falls back to config variable FP_VIRTUALENV from config.py
    '''
    # If not set using environment variable or directly via call try config
    if virt_activate_file is None:
        from config import FP_VIRTUALENV
        virt_activate_file = FP_VIRTUALENV

    if virt_activate_file and os.path.exists(virt_activate_file):
        execfile(virt_activate_file, dict(__file__=virt_activate_file))

def initLogging(app,level=None):
    '''
    Setup logging of FieldPrime Server

    Uses logfile FP_LOG_FILE and logging level FP_LOG_LEVEL from config.py
    '''
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['FP_LOG_FILE'], maxBytes=1024 * 1024 * 100, backupCount=10)

    # If level not set get from config
    if level is None:
        level = app.config['FP_LOG_LEVEL']
    file_handler.setLevel(level)

    #formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

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

def falseIfNotString(func):
    @wraps(func)
    def new_func(candidate):
        if isinstance(candidate, basestring):
            return func(candidate)
        else:
            return False
    return new_func
    
@falseIfNotString
def isValidIdentifier(candidate):
# Return boolean indicating whether candidate (assumed to be a string)
# is a valid identifier. Where valid means starting with a letter or
# underscore, followed by some number of letters, digits, or underscores.
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$", candidate) is not None

@falseIfNotString
def isValidInteger(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
    
@falseIfNotString
def isValidEmail(email):
# Return boolean indicating whether email looks like an email address.
    return re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email) is not None

@falseIfNotString
def isValidName(candidate):
# Returns boolean.
# Valid if starts with letter. Only contains letters, space, hyphen
    return re.match("[A-Za-z][ \-a-zA-Z0-9]*$", candidate) is not None

@falseIfNotString
def isValidPassword(candidate):
# Need to write this    
# Returns boolean.
# Valid if starts with letter. Only contains letters, space, hyphen
    return re.match("[A-Za-z ][\-a-zA-Z0-9]*$", candidate) is not None

def epoch2dateTime(timestamp):
# Return readable date/time string from timestamp (assumed to be in milliseconds).
# A time of zero (presumably a default rather than real time) is returned as empty string.
    return '' if timestamp == 0 else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000))

def formatJapDate(jdate):
    year = jdate / 10000
    month = (jdate % 10000) / 100
    day = jdate % 100
    return '{0}/{1}/{2}'.format(day, month, year)

def formatJapDateSortFormat(jdate):
    year = jdate / 10000
    month = (jdate % 10000) / 100
    day = jdate % 100
    return '{0}-{1}-{2}'.format(year, str(month).zfill(2), str(day).zfill(2))

def alertFieldPrimeAdmin(app, msg):
#---------------------------------------------------------------
# Bring msg to the attention of the configured FieldPrime admin.
#

# Ideally send an email, might take a bit to get this to work though..
#     import smtplib
#     from email.mime.text import MIMEText
#     sender = 'fieldprime_noreply@csiro.au'
#     recipient = app.config['FP_ADMIN_EMAIL']
#     emsg = MIMEText(msg)
#     emsg['Subject'] = 'FieldPrime Alert'
#     emsg['From'] = sender
#     emsg['To'] = recipient
#
#     # Send the message via our own SMTP server, but don't include the envelope header.
#     s = smtplib.SMTP('localhost')
#     s.sendmail(sender, [recipient], emsg.as_string())
#     s.quit()
    flog('ADMINALERT:' + msg)


def escapeHtml(html):
#-----------------------------------------------------------------------
# Make html safe, hopefully, currently just using cgi.escape.
    return None if html is None else cgi.escape(html)

def quote(col):
#-----------------------------------------------------------------------
# uses double-quoting style to escape existing quotes
    if col is None:
        return ''
    return '"{}"'.format(str(col).replace('"', '""'))

def removeLineEnds(txt):
#-----------------------------------------------------------------------
# Replace line ends with spaces
    if txt is None:
        return ''
    return txt.replace('\n', ' ')

###  Logging: ##################################################################
# We want a logging system that can be turned on or off by use of a flag file:
# 'dolog' in the app.config[FP_FLAG_DIR] folder.
#

def flog(msg) :
# Logging function called externally, initLogging should be called first.
# This default version does nothing, but may be overwritten.
# Note that initLogging() below changes this function. Hence you should
# not import this function by name, or you will just get a copy of this
# default version. You must instead import util, and call util.flog().
    pass

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

# Old way:
# def LogDebug(hdr, text):
# #-------------------------------------------------------------------------------------------------
# # Writes stuff to file system (for debug) - not routinely used..
#     f = open('/tmp/fieldPrimeDebug','a')
#     print >>f, "--- " + hdr + ": ---"
#     print >>f, text
#     print >>f, "------------------"
#     f.close


### End Logging ################################################################
################################################################################

