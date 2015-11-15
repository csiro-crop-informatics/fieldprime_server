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

from const import LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***
from fpsys import getFpsysDbConnection

def localPasswordCheck(user, password):
#-----------------------------------------------------------------------
# Validate 'system' user/password, returning boolean indicating success.
# A system user/pass is a mysql user/pass.
#
    phash = ''
    try:
        con = getFpsysDbConnection()
        qry = "select password from user where login = %s"
        cur = con.cursor()
        cur.execute(qry, (user,))
        resRow = cur.fetchone()
        if resRow is None:
            return None
        phash = resRow[0]
        return pwd.verify(password, phash)
    except mdb.Error, e:
        return None





def systemPasswordCheck(user, password):
#-----------------------------------------------------------------------
# Validate 'system' user/password, returning boolean indicating success.
# A system user/pass is a mysql user/pass.
#
    def dbName(username):
    #-----------------------------------------------------------------------
    # Map username to the database name.
        return 'fp_' + username

    try:
        con = mdb.connect('localhost', models.dbName4Project(user), password, dbName(user));
        con.close()
        return True
    except mdb.Error, e:
        #util.flog('system password check failed')
        return False

def ***REMOVED***PasswordCheck(username, password):
#-----------------------------------------------------------------------
# Validate ***REMOVED*** user/password, returning boolean indicating success
#
#     if username == '***REMOVED***' and password == 'm':
#         return True;
    ***REMOVED***Server = ***REMOVED***.***REMOVED***Server(***REMOVED***.SERVER_URL)
    if not ***REMOVED***Server:
        util.flog('Cannot connect to ***REMOVED*** server')
        return False
    ***REMOVED***User = ***REMOVED***Server.getUserByIdent(username)
    if ***REMOVED***User is None:
        util.flog('The supplied username is unknown.')
        return False
    if not ***REMOVED***User.authenticate(password):
        #util.flog('wrong ***REMOVED*** password')
        return False
    return True;

def userPasswordCheck(username, password):
    if systemPasswordCheck(username, password):
        return LOGIN_TYPE_SYSTEM
    elif ***REMOVED***PasswordCheck(username, password):  # Not a main project account, try as ***REMOVED*** user.
        # For ***REMOVED*** check, we should perhaps first check in a system database
        # as to whether the user is known to us. If not, no point checking ***REMOVED*** credentials.
        #
        # OK, valid ***REMOVED*** user. Find project they have access to:
        return LOGIN_TYPE_***REMOVED***
    else:
        return None
