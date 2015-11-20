# users.py
# Michael Kirk 2015
#
# Functions for managing FieldPrime user identities.
#
#
#

import MySQLdb as mdb
import util
import models
import ***REMOVED***
from passlib.apps import custom_app_context as pwd

from const import LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL
from fpsys import getFpsysDbConnection

