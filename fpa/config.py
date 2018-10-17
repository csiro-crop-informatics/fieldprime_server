# config.py
# Michael Kirk 2013
# Tim Erwin 2016
#
# Configuration for web service for FieldPrime browser login.
# For use by flask: app.config.from_object()
# Can be used to customize a server installation
#

from conf.default_config import *
from conf.jwt import *

#
# Development Server
#
DEBUG = True                                                # Flask debug mode
FP_LOG_LEVEL = logging.DEBUG                                # Logging level
