#
# Check for server down flag
# If the flag is there, application provides only a 'down for maintenance'
# message.
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

    # MFK Need a place to do things before anything else, hopefully that is here.
    # EG check for flag file indicating system not available
    util.initLogging(application)
    util.flog(application, "wsgi_adm_entry called")
