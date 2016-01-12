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
import os
import ***REMOVED***

import util
from models import dbName4Project, fpDBUser, fpPassword         # circularity here, could move APP* to separate module
from const import LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL, LOGIN_TYPE_MYSQL
from passlib.apps import custom_app_context as pwd_context
from passlib.apps import mysql_context


def getFpsysDbConnection():
    host = os.environ.get('FP_MYSQL_PORT_3306_TCP_ADDR', 'localhost')
    return mdb.connect(host, fpDBUser(), fpPassword(), 'fpsys')


def _getProjectIdFromName(projName):
#-----------------------------------------------------------------------
# Return project id or None on error.
#
    try:
        con = getFpsysDbConnection()
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
        con = getFpsysDbConnection()
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
        con = getFpsysDbConnection()
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
    if projId is None:
        return None, 'bad project name'
    try:
        con = getFpsysDbConnection()
        qry = 'select login, name, userProject.permissions from user join userProject on id = user_id where project_id = %s'
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
        con = getFpsysDbConnection()
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
        con = getFpsysDbConnection()
        qry = "select dbname from project where name = %s"
        cur = con.cursor()
        cur.execute(qry, (projectName,))
        foo = cur.fetchone()
        return None if foo is None else foo[0]
    except mdb.Error, e:
        return None


def add***REMOVED***UserToProject(ident, project, perms):
#-----------------------------------------------------------------------
# Add user with given ident to specified project with specified permissions.
# Note user db entry created if not already present.
# Returns error message on error or None
# MFK Note overlap with add***REMOVED***User()
#
    try:
        ***REMOVED***Name = ***REMOVED***.getUserName(ident)
    except ***REMOVED***.Error, e:
        return str(e)
#     # Check ***REMOVED*** user exists, and get name:
#     ***REMOVED***Server = ***REMOVED***.***REMOVED***Server(***REMOVED***.SERVER_URL)
#     if not ***REMOVED***Server:
#         return 'Cannot connect to ***REMOVED*** server'
#     ***REMOVED***User = ***REMOVED***Server.getUserByIdent(ident)
#     if ***REMOVED***User is None:
#         return 'Unknown ident'
#     ***REMOVED***Name = ***REMOVED***User.given_name + ' ' + ***REMOVED***User.surname

    # Get project id:
    projId = _getProjectIdFromName(project)
    if projId is None:
        return None, 'bad project name'
    try:
        con = getFpsysDbConnection()
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
            cur.execute('insert user (login,name,login_type) values (%s,%s,%s)', (ident, ***REMOVED***Name, LOGIN_TYPE_***REMOVED***))
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
        con = getFpsysDbConnection()
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

def add***REMOVED***User(login):
#-----------------------------------------------------------------------
# Returns None on success, else error message.
#
    try:
        ***REMOVED***Name = ***REMOVED***.getUserName(login)
        con = getFpsysDbConnection()
        qry = "insert user (login, name, login_type) values (%s,%s,%s)"
        cur = con.cursor()
        cur.execute(qry, (login, ***REMOVED***Name, LOGIN_TYPE_***REMOVED***))
        con.commit()
        con.close()
    except (***REMOVED***.Error, mdb.Error) as e:
        return str(e)
    return None

def addLocalUser(login, fullname, password):
# Returns None on success, else error message.
    # check strings for bad stuff?
    try:
        con = getFpsysDbConnection()
        qry = "insert user (login, name, passhash, login_type) values (%s,%s,%s,%s)"
        cur = con.cursor()
        cur.execute(qry, (login, fullname, pwd_context.encrypt(password), LOGIN_TYPE_LOCAL))
        con.commit()
        con.close()
    except mdb.Error, e:
        return str(e)
    return None


### Password Stuff: ####################################################################################

def localPasswordCheck(user, password):
#-----------------------------------------------------------------------
# Validate 'system' user/password, returning boolean indicating success.
# A system user/pass is a mysql user/pass.
#
    phash = ''
    try:
        con = getFpsysDbConnection()
        qry = "select passhash from user where login = %s and login_type = %s"
        cur = con.cursor()
        cur.execute(qry, (user, LOGIN_TYPE_LOCAL))
        resRow = cur.fetchone()
        if resRow is None:
            return None
        phash = resRow[0]
        return pwd_context.verify(password, phash)
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
        con = mdb.connect('localhost', dbName4Project(user), password, dbName(user));
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
# Return true if password OK, false if not, or None if something bad happened.
    # Check if the username exists and get login type:
    try:
        con = getFpsysDbConnection()
        qry = "select login_type, passhash from user where login = %s"
        cur = con.cursor()
        cur.execute(qry, (username,))
        resRow = cur.fetchone()
        if resRow is None:
            util.flog('Login attempt by unknown user: {0}'.format(username))
            return None
        loginType = resRow[0]
        phash = resRow[1]
    except mdb.Error, e:
        util.flog('Error in userPasswordCheck: {0}'.format(str(e)))
        return None # what about error message?
    if loginType == LOGIN_TYPE_LOCAL:
        return pwd_context.verify(password, phash)
    elif loginType == LOGIN_TYPE_SYSTEM:
        return systemPasswordCheck(username, password)
    elif loginType == LOGIN_TYPE_***REMOVED***:
        return ***REMOVED***PasswordCheck(username, password)
    elif loginType == LOGIN_TYPE_MYSQL:
        return mysql_context.verify(password, phash)
    else:
        util.flog('Unexpected login type: {0}'.format(loginType))
        return None

class User:
    USER_CREATE_PERMISSION = 0x1
    def __init__(self, id, name, passhash, login_type, permissions):
        self._id = id
        self._name = name
        self._passhash = passhash
        self._login_type = login_type
        self._permissions = permissions

    @staticmethod
    def getByLogin(ident):
        try:
            con = getFpsysDbConnection()
            qry = "select id, name, passhash, login_type, permissions from user where login = %s"
            cur = con.cursor()
            cur.execute(qry, (ident,))
            resRow = cur.fetchone()
            if resRow is None:
                return None
            return User(resRow[0], resRow[1], resRow[2], resRow[3], resRow[4])
        except mdb.Error, e:
            util.flog('Error in User.getByLogin: {0}'.format(str(e)))
            return None # what about error message?

    def name(self):
        return self._name
    def passhash(self):
        return self._passhash
    def login_type(self):
        return self._login_type
    def hasCreatePermissions(self):
        return bool(self._permissions & self.USER_CREATE_PERMISSION)
    def allowPasswordChange(self):
    # As in show the password change form in the admin page - only appropriate for mysql or local.
        return self._login_type == LOGIN_TYPE_MYSQL or self._login_type == LOGIN_TYPE_LOCAL
    
    def changePassword(self, newPassword):
    # Returns error message, or None for success.
    # NB, this only allowed for mysql and local types, and note that mysql get converted
    # to local types in the process (mysql only supported for historical users).
        if not isinstance(newPassword, basestring): return 'Unexpected password type'
        if len(newPassword) < 4: return 'password too short'
        if not self.allowPasswordChange(): return 'Cannot change this password type'
        try:
            con = getFpsysDbConnection()
            qry = "update user set passhash = %s, login_type = %s where id = %s"
            cur = con.cursor()
            cur.execute(qry, (pwd_context.encrypt(newPassword), LOGIN_TYPE_LOCAL, self._id))
            con.commit()
            con.close()
        except mdb.Error, e:
            util.flog('Error in User.changePassword: {0}'.format(str(e)))
            return 'Error in User.changePassword: {0}'.format(str(e))
        return None

    @staticmethod
    def has_create_user_permissions(login):
        usr = User.getByLogin(login)
        if usr is None:
            return False
        return usr.hasCreatePermissions()

