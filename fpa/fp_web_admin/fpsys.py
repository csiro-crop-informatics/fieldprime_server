# fpsys.py
# Michael Kirk 2015
#
# To manage access to the fpsys database.
# This db (attow) holds information about ***REMOVED*** users and which projects
# they have access to.
#

import MySQLdb as mdb

import fp_common.models as models
import fp_common.util as util
import ***REMOVED***

def _getDbConnection():
    return mdb.connect('localhost', models.APPUSR, models.APPPWD, 'fpsys')

def deleteUser(project, ident):
    try:
        con = _getDbConnection()
        cur = con.cursor()
        if 1 != cur.execute('select id from user where login = %s', (ident)):
            return "User {0} not found".format(ident)
        uid = cur.fetchone()[0]
        if 1 != cur.execute('delete from userProject where project=%s and user_id=%s', (project, uid)):
            return "Error deleting {0} from {1}".format(ident, project)
        con.commit()
        con.close()
        return None
    except mdb.Error, e:
        return (None, 'Failed system login ' + str(e))

def getProjectUsers(project):
#-----------------------------------------------------------------------
# Get (***REMOVED***) users associated with specified project.
# Returns tuple of dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the user login ids, the values are tuples (name, permissions).
    try:
        con = _getDbConnection()
        qry = 'select login, name, permissions from user join userProject on id = user_id where project = %s'
        cur = con.cursor()
        cur.execute(qry, (project))
        users = {}
        for row in cur.fetchall():
            users[row[0]] = row[1], row[2]
        return (users, None)
    except mdb.Error, e:
        return (None, 'Failed system login')

def getProjects(username):
#-----------------------------------------------------------------------
# Get project available to specified user - this should be a valid ***REMOVED*** user.
# Returns tuple, project dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the project names, the values are the permissions (for the specified user).
    try:
        con = _getDbConnection()
        qry = """
            select up.project, up.permissions from user u join userProject up
            on u.id = up.user_id and u.login = %s"""
        cur = con.cursor()
        cur.execute(qry, (username))
        projects = {}
        for row in cur.fetchall():
            projects[row[0]] = row[1]
        return (projects, None)
    except mdb.Error, e:
        return (None, 'Failed system login')

def createUser(ident, project, perms):
#-----------------------------------------------------------------------
# Returns error message on error or None
#
    # Check ***REMOVED*** user exists, and get name:
    ***REMOVED***Server = ***REMOVED***.***REMOVED***Server(***REMOVED***.SERVER_URL)
    if not ***REMOVED***Server:
        return 'Cannot connect to ***REMOVED*** server'
    ***REMOVED***User = ***REMOVED***Server.getUserByIdent(ident)
    if ***REMOVED***User is None:
        return 'Unknown ident'
    ***REMOVED***Name = ***REMOVED***User.given_name + ' ' + ***REMOVED***User.surname
    try:
        con = _getDbConnection()
        cur = con.cursor()
        # Does user exist in fpsys?
        userFpId = None
        if 1 == cur.execute('select id from user where login = %s', (ident)):
            userFpId = cur.fetchone()[0]

        # Check user isn't already in project:
        qry = 'select login from user join userProject on id = user_id'
        qry += ' where project = %s and login = %s'
        cur.execute(qry, (project, ident))
        if cur.rowcount == 1:
            return 'User already configured for this project'
        # Insert or update user:
        # We don't really have to update, but in case name has changed in ***REMOVED*** we do.
        if userFpId is None:
            cur.execute('insert user values (null, %s, %s)', (ident, ***REMOVED***Name))
            userFpId = cur.lastrowid
        else:
            cur.execute('update user set name = %s where id = %s', (***REMOVED***Name, userFpId))
        # Insert into userProject table:
        cur.execute('insert userProject values (%s, %s, %s)', (userFpId, project, perms))
        con.commit()
        con.close()
    except mdb.Error, e:
        return (None, 'Failed system login')
    return None

def updateUser(ident, project, perms):
#-----------------------------------------------------------------------
# Returns error message on error or None
#
    # Check ***REMOVED*** user exists, and get name:
    ***REMOVED***Server = ***REMOVED***.***REMOVED***Server(***REMOVED***.SERVER_URL)
    if not ***REMOVED***Server:
        return 'Cannot connect to ***REMOVED*** server'
    ***REMOVED***User = ***REMOVED***Server.getUserByIdent(ident)
    if ***REMOVED***User is None:
        return 'Unknown ident {0}'.format(ident)
    ***REMOVED***Name = ***REMOVED***User.given_name + ' ' + ***REMOVED***User.surname
    try:
        con = _getDbConnection()
        cur = con.cursor()
        # Check user exists in fpsys
        userFpId = None
        if 1 == cur.execute('select id from user where login = %s', (ident)):
            userFpId = cur.fetchone()[0]
        else:
            return 'User not found for update'

        # Check user is already in project and get the id:
        qry = 'select user_id from user join userProject on id = user_id'
        qry += ' where project = %s and login = %s'
        cur.execute(qry, (project, ident))
        if cur.rowcount != 1:
            return 'User not found for this project'
        userFpId = cur.fetchone()[0]

        # update user table (in case name in ***REMOVED*** has changed):
        cur.execute('update user set name = %s where id = %s', (***REMOVED***Name, userFpId))
        # Update userProject table:
        cur.execute('update userProject set permissions=%s where user_id=%s and project = %s',
                    (perms, userFpId, project))
        con.commit()
        con.close()
    except mdb.Error, e:
        return (None, 'Failed system login')
    return None

