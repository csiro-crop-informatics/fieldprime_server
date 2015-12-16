# util.py
# Michael Kirk 2014
#
# Handy functions.
#

import time, sys
import cgi

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

def initLogging(app, justPrint=False):
#----------------------------------------------------------------------------
# Set up logging, which is then done with the flog() function.
# By default flog() does nothing. This function can change that.
# If justPrint is true, then flog will just print its argument.
# Otherwise - if logging is flagged by the presence of file
# app.config['FP_FLAG_DIR'] + "/dolog" - it will append its argument
# to the file app.config['FPLOG_FILE']. We do this check once
# in this init function rather than with every call in the hope that
# it is less cost at each log call.
# MFK perhaps shouldn't write to FPLOG_FILE since this used by
# fpLog below, which is used for logging connections, and is always on.
#
    global flog
    import os.path
    if os.path.isfile(app.config['FP_FLAG_DIR'] + "/dolog"):
        if justPrint:
            flog = lambda x:sys.stdout.write('flog: ' + str(x)+'\n')
            return

        # Lookup the logging file name, create a function to log to it, and
        # set the flog module global func to that function. So hopefully
        # the module namespace will not end up with either logfilename or
        # flogServer in it, but the function will work nonetheless.
        logfilename = app.config['FPLOG_FILE']
        def flogServer(msg):
            print 'file flog'
            try:     # Don't crash out if logging not working
                f = open(logfilename, 'a')
                print >>f, 'flog@{0}\t{1}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), msg)
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

