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
from default_config import *

#
# Development Server
#
DEBUG = True                                                # Flask debug mode
FP_ROOT = os.environ.get('FIELDPRIME_ROOT','/app')          # Base path to application
FP_LOG_DIR = FP_ROOT + '/fplog'                            # Path to logs
FP_LOG_FILE = FP_LOG_DIR + '/fp.log'                         # FP logfile
FP_LOG_LEVEL = logging.DEBUG                                # Logging level
FP_FLAG_DIR = FP_LOG_DIR                                    # Path to file flag directory
