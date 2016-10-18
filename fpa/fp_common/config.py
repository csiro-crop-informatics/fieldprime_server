# config.py
# Michael Kirk 2013
#
# Configuration for web service for FieldPrime browser login.
# For use by flask: app.config.from_object()
# Can be used to customize a server installation
#

import os

# Public server settings
if True:
    FP_ROOT = os.environ.get('FP_ROOT', '/srv/www/fpserver/')
    PUBLIC_HTML_ROOT = FP_ROOT + 'htdocs/'
    URL_HOST_PART = 'https://localhost/'
else:
    FP_ROOT = '/var/www/fieldprime/'
    PUBLIC_HTML_ROOT = '/var/www/html/'
    URL_HOST_PART = 'https://localhost/'


# Flask config params:
MAX_CONTENT_LENGTH = 16 * 1024 * 1024             # Limit the size of file uploads
SECRET_KEY = '** REMOVED **'   # NB FieldPrime also uses this explicitly
# DEBUG = True

# FieldPrime config params:
PHOTO_UPLOAD_FOLDER = FP_ROOT + 'photos/'
DATA_ACCESS_MODULE = 'fp_common.models'      # Name of the py file providing the data access layer.
CATEGORY_IMAGE_FOLDER = PUBLIC_HTML_ROOT + 'fpt/categoryImages/'
CATEGORY_IMAGE_URL_BASE = URL_HOST_PART + 'fpt/categoryImages/'
FP_ADMIN_EMAIL = 'root@localhost'
CRASH_REPORT_UPLOAD_FOLDER = FP_ROOT + 'crashReports/'
FPPWFILE = FP_ROOT + 'fppw'
SECFILE = FP_ROOT + 'fpsec'
FP_DB_CREATE_FILE = FP_ROOT + 'fprime.create.tables.sql'
SESS_FILE_DIR =  FP_ROOT + 'wsessions'
FLAG_DIR = FP_ROOT + 'fplog'

# Log file to write to:
FPLOG_FILE = FP_ROOT + 'fplog/fp.log'
FP_FLAG_DIR = FP_ROOT + 'fplog/'
