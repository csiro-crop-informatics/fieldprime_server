# fpsys.py
# Michael Kirk 2015
#
# To manage access to the fpsys database.
# This db (attow) holds information about ***REMOVED*** users and which projects
# they have access to.
#
# Since we are only doing a little with the fpsys database, we are just using
# sql directly rather than sqlalchemy.
#

import MySQLdb as mdb

from fp_common.models import APPUSR, APPPWD          # circularity here, could move APP* to separate module
import fp_common.util as util
import ***REMOVED***

def _getDbConnection():
    return mdb.connect('localhost', APPUSR, APPPWD, 'fpsys')


def _getProjectIdFromName(projName):
#-----------------------------------------------------------------------
# Return project id or None on error.
#
    try:
        con = _getDbConnection()
        qry = "select id from project where name = %s"
        cur = con.cursor()
        cur.execute(qry, (projName,))
        resRow = cur.fetchone()
        return None if resRow is None else resRow[0]
    except mdb.Error, e:
        return None


def _getUserIdFromIdent(ident):
#-----------------------------------------------------------------------
# Return project id or None on if non-existent, or other error.
#
    try:
        con = _getDbConnection()
        cur = con.cursor()
        cur.execute("select id from user where login = %s", (ident,))
        resRow = cur.fetchone()
        return None if resRow is None else resRow[0]
    except mdb.Error, e:
        return None


def deleteUser(project, ident):
#-----------------------------------------------------------------------
# Return None or string error message on error.
#
    # Get project id:
    projId = _getProjectIdFromName(project)
    if projId is None:
        return 'bad project name'
    try:
        con = _getDbConnection()
        cur = con.cursor()
        # Get user id:
        uid = _getUserIdFromIdent(ident)
        if uid is None:
            return 'bad user ident'
        # Do the delete:
        if 1 != cur.execute('delete from userProject where project_id=%s and user_id=%s', (projId, uid)):
            return "Error deleting {0} from {1}".format(ident, project)
        con.commit()
        con.close()
        return None
    except mdb.Error, e:
        return 'Failed system login ' + str(e)

def getProjectUsers(project):
#-----------------------------------------------------------------------
# Get (***REMOVED***) users associated with specified project.
# Returns tuple of dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the user login ids, the values are tuples (name, permissions).
#
    # Get project id:
    projId = _getProjectIdFromName(project)
    #print 'projId' + projId
    if projId is None:
        return None, 'bad project name'
    try:
        con = _getDbConnection()
        qry = 'select login, name, permissions from user join userProject on id = user_id where project_id = %s'
        cur = con.cursor()
        cur.execute(qry, (projId,))
        users = {}
        for row in cur.fetchall():
            users[row[0]] = row[1], row[2]
        return (users, None)
    except mdb.Error, e:
        return (None, 'Failed system login')

class UserProject:
    def __init__(self, projectName, dbname, ident, access):
        self.projectName = projectName
        self.dbname = dbname
        self.ident = ident
        self.access = access

    def name(self):
        return self.projectName

def getProjects(username):
#-----------------------------------------------------------------------
# Get project available to specified user - this should be a valid ***REMOVED*** user.
# Returns tuple, project dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the project names, the values are the permissions (for the specified user).
    try:
        con = _getDbConnection()
        qry = """
            select p.name, up.permissions, p.dbname from user u join userProject up
            on u.id = up.user_id and u.login = %s join project p on p.id = up.project_id"""
        cur = con.cursor()
        cur.execute(qry, (username,))
        userProjs = []
        for row in cur.fetchall():
            np = UserProject(row[0], row[2], username, row[1])
            userProjs.append(np)
        return (userProjs, None)
    except mdb.Error, e:
        return (None, 'Failed system login:' + str(e))


def getProjectDBname(projectName):
#-----------------------------------------------------------------------
# Returns dbname for named project or None on error.
#
    try:
        con = _getDbConnection()
        qry = "select dbname from project where name = %s"
        cur = con.cursor()
        cur.execute(qry, (projectName,))
        foo = cur.fetchone()
        return None if foo is None else foo[0]
    except mdb.Error, e:
        return None


def addUserToProject(ident, project, perms):
#-----------------------------------------------------------------------
# Add user with given ident to specified project with specified permissions.
# Note user db entry created if not already present.
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

    # Get project id:
    projId = _getProjectIdFromName(project)
    if projId is None:
        return None, 'bad project name'
    print 'here 1'
    try:
        con = _getDbConnection()
        cur = con.cursor()
        # Get user id if exists
        userFpId = _getUserIdFromIdent(ident)

        # Check user isn't already in project:
        qry = 'select login from user join userProject on id = user_id'
        qry += ' where project_id = %s and login = %s'
        cur.execute(qry, (projId, ident))
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
        cur.execute('insert userProject (user_id, project_id, permissions) values (%s, %s, %s)',
                    (userFpId, projId, perms))
        con.commit()
        con.close()
    except mdb.Error, e:
        return 'Failed user add'
    print 'here 2'
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

    # Get project id:
    projId = _getProjectIdFromName(project)
    if projId is None:
        return None, 'bad project name'

    try:
        con = _getDbConnection()
        cur = con.cursor()
        # Check user exists in fpsys
        userFpId = _getUserIdFromIdent(ident)
        if userFpId is None:
            return 'User not found for update'

        # Check user is already in project and get the id:
        qry = 'select user_id from user join userProject on id = user_id'
        qry += ' where project_id = %s and login = %s'
        cur.execute(qry, (projId, ident))
        if cur.rowcount != 1:
            return 'User not found for this project'

        # update user table (in case name in ***REMOVED*** has changed):
        cur.execute('update user set name = %s where id = %s', (***REMOVED***Name, userFpId))
        # Update userProject table:
        cur.execute('update userProject set permissions=%s where user_id=%s and project_id = %s',
                    (perms, userFpId, projId))
        con.commit()
        con.close()
    except mdb.Error, e:
        return (None, 'Failed system login')
    return None

