# config.py
# Michael Kirk 2013
# Tim Erwin 2016
#
# Configuration for web service for FieldPrime browser login.
# For use by flask: app.config.from_object()
# Can be used to customize a server installation
#

import os
import logging

#
# Default config params
# Overridden in config.py with application specific environments (production/development)
#
FP_ROOT = os.environ.get('FP_ROOT','/app/')                 # Base path to application
FP_LOG_DIR = FP_ROOT + 'fplog/'                             # Path to logs
FP_LOG_FILE = FP_LOG_DIR + 'fp.log'                         # FP logfile
FP_LOG_LEVEL = logging.ERROR                                # Logging level
FP_FLAG_DIR = FP_LOG_DIR                                    # Path to file flag directory
FP_VIRTUALENV = None                                        # Path to virtualenv activate_this.py
FP_MYSQL_HOST = os.environ.get('FP_MYSQL_HOST','localhost') # FP mysql database host
FP_MYSQL_PORT = int(os.environ.get('FP_MYSQL_PORT',3306))   # Mysql port: must be an integer


#
# The FieldPrime server can be run in various ways, and accordingly we may need to detect
# part of the URL. The FP_API_PREFIX environment var should be used to indicate what configuration
# we are running as.
#
API_PREFIX = os.environ.get('FP_API_PREFIX', '')

PUBLIC_HTML_ROOT = FP_ROOT + 'html/'
URL_HOST_PART = 'http://localhost/'

# Flask config params:
MAX_CONTENT_LENGTH = 16 * 1024 * 1024             # Limit the size of file uploads
SECRET_KEY = '** REMOVED **'   # NB FieldPrime also uses this explicitly

# FieldPrime config params:
PHOTO_UPLOAD_FOLDER = FP_ROOT + 'photos/'
DATA_ACCESS_MODULE = 'fp_common.models'      # Name of the py file providing the data access layer.
CATEGORY_IMAGE_FOLDER = PUBLIC_HTML_ROOT + 'fpt/categoryImages/'
CATEGORY_IMAGE_URL_BASE = URL_HOST_PART + 'fpt/categoryImages/'
FP_ADMIN_EMAIL = 'enquiries@csiro.au'
CRASH_REPORT_UPLOAD_FOLDER = FP_ROOT + 'crashReports/'
FPPWFILE = FP_ROOT + '.fppw'
SECFILE = FP_ROOT + 'fpsec'
FP_DB_CREATE_FILE = FP_ROOT + 'fprime.create.tables.sql'
SESS_FILE_DIR =  FP_ROOT + 'wsessions'
FLAG_DIR = FP_ROOT + 'fplog'
