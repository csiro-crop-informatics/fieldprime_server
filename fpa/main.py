#
# wsgi_adm_entry.py
# Michael Kirk 2013
# Tim Erwin 2016
# This is the entry point for the FieldPrime admin pages on the server.
# The function of this file is to export a runnable called "application",
# which will be used by wsgi to service requests.
#

import os, sys
import logging

#Setup path for application code
app_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_path)

from fp_common.util import fpServerDown, activateVirtualenv, initLogging

#Activate python virtualenv if set
activateVirtualenv()

#
# Maintenance Mode
#
# Check for server down flag file. If the flag is there, we export an application
# that provides only a 'down for maintenance' message.
#
if fpServerDown():

    def application(environ, start_response):
        #TODO: Template maintenance message"
        status = '500 Server Down'
        output = '<h1>Sorry, FieldPrime is currently down for maintenance</h1>'
        response_headers = [('Content-type', 'text/html'),
                            ('Content-Length', str(len(output))),
                            ('Cache-Control', 'no-cache, no-store, must-revalidate')]
        start_response(status, response_headers)
        return [output]
# 
# Production Mode
#
else:

    from fp_web_admin import app as application
    # Setup logging:
    initLogging(application)


#
# Development Mode ($> flask run or $> python fp_admin_entry.wsgi)
#
if __name__ == '__main__':

    from fp_web_admin import app as application
    initLogging(application,level=logging.DEBUG)
    application.run()

