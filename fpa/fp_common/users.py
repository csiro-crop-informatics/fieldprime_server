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
