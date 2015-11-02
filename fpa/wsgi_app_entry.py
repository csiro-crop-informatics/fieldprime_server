#
# wsgi_app_entry.py
# Michael Kirk 2013
# This is the entry point for the FieldPrime scoring device web services.
# The function of this file is to export a runnable called "application",
# which will be used by wsgi to service requests.
#

FP_ROOT = '***REMOVED***/'
#FP_ROOT = '/var/www/fieldprime/'

#
# Check for server down flag file. If the flag is there, we export an application
# that provides only a 'down for maintenance' message.
#
import os.path
flagdir = FP_ROOT + 'fplog/'
fpdown = os.path.isfile(flagdir + "/fpdown")
if fpdown:
    import sys
    def application(environ, start_response):
        # MFK - need to define protocol for error returns for device pages.
        # Sometime the device is expecting a json response. So need to put
        # error code in there, or perhaps better return HTTP error status
        # and ensure devices check for that.
        status = '500 Server Down'
        output = 'FieldPrime is currently down for maintenance'
        response_headers = [('Content-type', 'text/plain'),
                            ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
else:
    if False:    # For testing at a different location to the main one (WSGIPythonPath) configured in apache.
        import sys
        sys.path.insert(0, FP_ROOT + 'fptest/fpa')
    from fp_app_api import app as application
    from fp_common import util
    application.config['SESS_FILE_DIR'] =  FP_ROOT + 'fpa/wsessions'
    application.config['FP_FLAG_DIR'] = flagdir

    # Setup logging:
    util.initLogging(application)
    #util.flog("wsgi_app_entry called")
