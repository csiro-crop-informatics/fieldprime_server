#
# wsgi_adm_entry.py
# Michael Kirk 2013
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
        status = '500 Server Down'
        output = '<h1>Sorry, FieldPrime is currently down for maintenance</h1>'
        response_headers = [('Content-type', 'text/html'),
                            ('Content-Length', str(len(output))),
                            ('Cache-Control', 'no-cache, no-store, must-revalidate')]
        start_response(status, response_headers)
        return [output]
else:
    from fp_web_admin import app as application
    from fp_common import util
    application.config['SESS_FILE_DIR'] =  '***REMOVED***/fpa/wsessions'
    application.config['FP_FLAG_DIR'] =  flagdir

    # Setup logging:
    util.initLogging(application)
    util.flog("wsgi_adm_entry called")
