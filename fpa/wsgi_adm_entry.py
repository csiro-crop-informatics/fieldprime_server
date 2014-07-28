#
# wsgi_adm_entry.py
# This is the entry point for the FieldPrime admin pages on the server.
# The function of this file is to export a runnable called "application",
# which will be used by wsgi to service requests.
#


#
# Check for server down flag file. If the flag is there, we export an application
# that provides only a 'down for maintenance' message.
#
import os.path
flagdir = '***REMOVED***/fplog/'
fpdown = os.path.isfile(flagdir + "/fpdown")
if fpdown:
    import sys
    def application(environ, start_response):
        status = '200 OK'
        output = 'FieldPrime is currently down for maintenance'
        response_headers = [('Content-type', 'text/plain'),
                            ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
else:
    from fp_web_admin import app as application
    from fp_common import util
    application.config['SESS_FILE_DIR'] =  '***REMOVED***/fpa/wsessions'
    application.config['FP_FLAG_DIR'] =  flagdir

    # MFK Need a place to do things before anything else, hopefully that is here.
    # EG check for flag file indicating system not available
    util.initLogging(application)
    util.flog("wsgi_adm_entry called")


# Code to add log message to file (delete?):
#import time
#def LogDebug(hdr, text):
##-------------------------------------------------------------------------------------------------
## Writes stuff to file system (for debug) - not routinely used..
#    f = open('/tmp/fieldPrimeDebug','a')
#    print >>f, '{0}\t{1}:{2}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), hdr, text)
#    f.close
#
#LogDebug('wsgi', 'admin entry')
