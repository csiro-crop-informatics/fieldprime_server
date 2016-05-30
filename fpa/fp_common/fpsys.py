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
from contextlib import closing
import os
from passlib.apps import custom_app_context as pwd_context
from passlib.apps import mysql_context

import ***REMOVED***
import util
from const import LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL, LOGIN_TYPE_MYSQL
#from models import getFpsysDbConnection         # circularity here, could move APP* to separate module
import models

class FPSysException(Exception):
    pass

def getFpsysDbConnection():
#-----------------------------------------------------------------------
# Get mysql connection to fpsys database.
#
    host = os.environ.get('FP_MYSQL_PORT_3306_TCP_ADDR', 'localhost')
    #print 'host {0} user {1} pw {2}'.format(host, fpDBUser(), fpPassword())
    return mdb.connect(host, models.fpDBUser(), models.fpPassword(), 'fpsys')

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

def getProjectUsers(projIdOrName):
#-----------------------------------------------------------------------
# Get (***REMOVED***) users associated with specified project.
# Returns tuple of dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the user login ids, the values are tuples (name, permissions).
#
    # Get project id:
    if isinstance(projIdOrName, basestring):
        projId = _getProjectIdFromName(projIdOrName)
        if projId is None:
            return None, 'bad project name'
    else:
        projId = projIdOrName
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
    
class UserProjectPermissions:
    PERMISSION_VIEW = 0 # i.e. they have access to the project - hmm
    PERMISSION_ADMIN = 0x1
    def __init__(self, permissions):
        self._permissions = permissions
    def hasPermission(self, perm):
        return bool(self._permissions & perm)
    def hasAdminRights(self):
        return self.hasPermission(self.PERMISSION_ADMIN)

class UserProject:
# Class to hold details of project with user.
    PERMISSION_VIEW = 0 # i.e. they have access to the project
    PERMISSION_ADMIN = 0x1

    def __init__(self, projectId, projectName, dbname, ident, access):
        self._projectId = projectId
        self._projectName = projectName
        self._dbname = dbname
        self._ident = ident
        self._access = access
    def projectId(self): return self._projectId
    def getProjectId(self): return self._projectId

    def projectName(self): return self._projectName
    def getProjectName(self): return self._projectName
    def dbname(self): return self._dbname
    def ident(self): return self._ident
    def access(self): return self._access

    @staticmethod
    def getUserProject(username, projectId):
    # Returns UserProject, None, or raises FPSysException.
        try:
            con = getFpsysDbConnection()
            qry = """
                select p.id, p.name, up.permissions, p.dbname from user u join userProject up
                on u.id = up.user_id and u.login = %s join project p on p.id = up.project_id
                where up.project_id = %s"""
            cur = con.cursor()
            cur.execute(qry, (username, projectId))
            if cur.rowcount != 1:
                return None
            row = cur.fetchone()
            cur.close()
            con.close()
            return UserProject(row[0], row[1], row[3], username, row[2])
        except mdb.Error, e:
            raise FPSysException('Failed getUserProject:' + str(e))

    def hasPermission(self, perm):
        return bool(self._access & perm)

    def hasAdminRights(self):
        return self.hasPermission(self.PERMISSION_ADMIN)

    def db(self):
        return models.getDbConnection(self.dbname())

    def getModelProject(self):
        return models.Project.getById(self.db(), self.getProjectId())

def getUserProjects(username):
#-----------------------------------------------------------------------
# Get project available to specified user - this should be a valid ***REMOVED*** user.
# Returns tuple, project dictionary and errorMessage (which will be None if no error).
# The dictionary keys are the project names, the values are the permissions (for the specified user).
    try:
        con = getFpsysDbConnection()
        qry = """
            select p.id, p.name, up.permissions, p.dbname from user u join userProject up
            on u.id = up.user_id and u.login = %s join project p on p.id = up.project_id"""
        cur = con.cursor()
        cur.execute(qry, (username,))
        userProjs = []
        for row in cur.fetchall():
            np = UserProject(row[0], row[1], row[3], username, row[2])
            userProjs.append(np)
        return (userProjs, None)
    except mdb.Error, e:
        return (None, 'Failed system login:' + str(e))

def addOrUpdateUserProjectById(userId, projId, perms):
#-----------------------------------------------------------------------
# Add user with given id to specified project with specified permissions.
# Note user db entry created if not already present.
# Returns error message on error or None
# MFK Note overlap with add***REMOVED***User()
#
    try:
        con = getFpsysDbConnection()
        cur = con.cursor()

        # Check user isn't already in project:
        qry = 'select user_id from userProject'
        qry += ' where project_id = %s and user_id = %s'
        cur.execute(qry, (projId, userId))
        if cur.rowcount > 0:
            # Update:
            cur.execute('update userProject set permissions = %s where user_id = %s and project_id = %s',
                        (perms, userId, projId))
        else:
            # Insert into userProject table:
            cur.execute('insert userProject (user_id, project_id, permissions) values (%s, %s, %s)',
                        (userId, projId, perms))
        con.commit()
        con.close()
    except mdb.Error, e:
        return 'Failed user add ({})'.format(e)
    return None

def addUserToProject(userId, projectName, perms):
#-----------------------------------------------------------------------
# Add user with given id to specified project with specified permissions.
# Note user db entry created if not already present.
# Returns error message on error or None
# MFK Note overlap with add***REMOVED***User()
#
    # Get project id:
    projId = _getProjectIdFromName(projectName)
    if projId is None:
        return None, 'bad project name'
    try:
        con = getFpsysDbConnection()
        cur = con.cursor()

        # Check user isn't already in project:
        qry = 'select user_id from userProject'
        qry += ' where project_id = %s and user_id = %s'
        cur.execute(qry, (projId, userId))
        if cur.rowcount > 0:
            return 'User already configured for this project'

        # Insert into userProject table:
        cur.execute('insert userProject (user_id, project_id, permissions) values (%s, %s, %s)',
                    (userId, projId, perms))
        con.commit()
        con.close()
    except mdb.Error, e:
        return 'Failed user add ({})'.format(e)
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

#     # Check ***REMOVED*** user exists, and get name:
#     ***REMOVED***Server = ***REMOVED***.***REMOVED***Server(***REMOVED***.SERVER_URL)
#     if not ***REMOVED***Server:
#         return 'Cannot connect to ***REMOVED*** server'
#     ***REMOVED***User = ***REMOVED***Server.getUserByIdent(ident)
#     if ***REMOVED***User is None:
#         return 'Unknown ident {0}'.format(ident)
#     ***REMOVED***Name = ***REMOVED***User.given_name + ' ' + ***REMOVED***User.surname

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

#         # update user table (in case name in ***REMOVED*** has changed):
#         cur.execute('update user set name = %s where id = %s', (***REMOVED***Name, userFpId))
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

def addLocalUser(login, fullname, password, email):
# Returns None on success, else error message.
    # check strings for bad stuff?
    try:
        con = getFpsysDbConnection()
        qry = "insert user (login, name, passhash, login_type, email) values (%s,%s,%s,%s,%s)"
        cur = con.cursor()
        cur.execute(qry, (login, fullname, pwd_context.encrypt(password), LOGIN_TYPE_LOCAL, email))
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
# Return true if password OK, false if not, or None if something bad happened.
    # Check if the username exists and get login type:
    try:
        con = getFpsysDbConnection()
        qry = "select login_type, passhash from user where login = %s"
        cur = con.cursor()
        cur.execute(qry, (username,))
        resRow = cur.fetchone()
        cur.close()
        con.close()
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

### Users: ############################################################################

class User:
# In memory instance of fpsys.user.
# NB, we don't include passhash for security reasons, but could retrieve
# it on demand (not required attow).
#
    PERMISSION_CREATE_USER = 0x1
    PERMISSION_CREATE_PROJECT = 0x2
    PERMISSION_OMNIPOTENCE = 0x4
    def __init__(self, id, ident, name, login_type, permissions, email):
        self._id = id
        self._ident = ident
        self._name = name
        self._login_type = login_type
        self._permissions = permissions
        self._email = email

    def getId(self):
        return self._id
    def getIdent(self):
        return self._ident
    def getName(self):
        return self._name
    def setName(self, name):
        if util.isValidName(name):
            self._name = name
        else:
            raise FPSysException("invalid name")
    def getEmail(self):
        return self._email
    def setEmail(self, email):
        if util.isValidEmail(email):
            self._email = email
        else:
            raise FPSysException("invalid email address")
#     def passhash(self):
#         return self._passhash
    def getLoginType(self):
        return self._login_type

    def hasPermission(self, perm):
        return bool(self._permissions & perm)
    def allowPasswordChange(self):
    # As in show the password change form in the admin page - only appropriate for mysql or local.
        return self._login_type == LOGIN_TYPE_MYSQL or self._login_type == LOGIN_TYPE_LOCAL

    @staticmethod
    def getByLogin(ident):
    # Return list of all Users, or None on error.
        try:
            con = getFpsysDbConnection()
            qry = "select id, login, name, login_type, permissions, email from user where login = %s"
            cur = con.cursor()
            cur.execute(qry, (ident,))
            resRow = cur.fetchone()
            if resRow is None:
                return None
            return User(resRow[0], resRow[1], resRow[2], resRow[3], resRow[4], resRow[5])
        except mdb.Error, e:
            util.flog('Error in User.getByLogin: {0}'.format(str(e)))
            return None # what about error message?

    @staticmethod
    def getAll():
    # Return list of all Users, or None on error.
        try:
            con = getFpsysDbConnection()
            qry = "select id, login, name, login_type, permissions, email from user"
            cur = con.cursor()
            cur.execute(qry)
            users = []
            for resRow in cur:
                users.append(User(resRow[0], resRow[1], resRow[2], resRow[3], resRow[4], resRow[5]))
            return users
        except mdb.Error:
            util.flog('Error in User.getAll')
            return None

    def setPassword(self, newPassword):
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
            cur.execute(qry, (pwd_context.encrypt(newPassword), LOGIN_TYPE_LOCAL, self.getId()))
            con.commit()
            con.close()
        except mdb.Error, e:
            util.flog('Error in User.setPassword: {0}'.format(str(e)))
            return 'Error in User.setPassword: {0}'.format(str(e))
        return None

    def save(self):
    # Update database with current values for name, email. FOR LOCAL users only.
    # Returns None on success else error message
    # NB, password is done separately.
    #
        if self.getLoginType() != LOGIN_TYPE_LOCAL:
            return "Operation not allowed for non-local user"
        try:
            con = getFpsysDbConnection()
            qry = "update user set name=%s, email=%s where id = %s"
            cur = con.cursor()
            cur.execute(qry, (self.getName(), self.getEmail(), self.getId()))
            con.commit()
            con.close()
        except mdb.Error, e:
            util.flog('Error in User.save: {0}'.format(str(e)))
            return 'Error in User.save: {0}'.format(str(e))
        return None

    def omnipotent(self):
        return self._permissions & self.PERMISSION_OMNIPOTENCE

    @staticmethod
    def sHasPermission(login, perm):
        usr = User.getByLogin(login)
        if usr is None:
            return False
        return bool(usr._permissions & perm)

    @staticmethod
    def delete(ident):
    # Returns None on success else error message.
        rows = 0;
        try:
            con = getFpsysDbConnection()
            qry = "delete from user where login = %s"
            cur = con.cursor()
            cur.execute(qry, (ident,))
            rows = cur.rowcount
            con.commit()
            con.close()
        except mdb.Error, e:
            util.flog('Error in User.delete: {0}'.format(str(e)))
            return 'Error in User.delete: {0}'.format(str(e))
        if rows == 1:
            return None
        elif rows == 0:
            return "User not found"
        else:
            return "Unexpected error, multiple deletes occurred"


### Projects: ############################################################################

class Project():
    def __init__(self, projId, name, dbName):
        self._id = projId
        self._name = name
        self._dbName = dbName

    def getId(self):
        return self._id

    def getName(self):
        return self._name
    def setName(self, name):
        self._name = name

    def dbName(self):
        return self._dbName

    def db(self):
        return models.getDbConnection(self.dbName())

    def saveName(self):
    # Save the current name to database.
    # Returns None on success, else an error message.
        try:
            con = getFpsysDbConnection()
            qry = "update project set name = %s where id = %s"
            cur = con.cursor()
            cur.execute(qry, (self._name, self._id))
#             if cur.rowcount != 1:
#                 return 'Error updating project {} {} {}'.format(cur.rowcount,self._name, self._id)
            con.commit()
            con.close()
            return None
        except mdb.Error, e:
            errmsg = 'Error updating project: {0}'.format(str(e))
            util.flog(errmsg)
            return errmsg

    def getUserPermissions(self, username):
    # Returns UserProjectPermissions for username in project (if present), or None
    # if not such userProject, or raises FPSysException on db error.
        try:
            con = getFpsysDbConnection()
            qry = """
                select up.permissions from user u join userProject up
                on u.id = up.user_id and u.login = %s where up.project_id = %s"""
            cur = con.cursor()
            cur.execute(qry, (username, self._id))
            if cur.rowcount != 1:
                return None
            row = cur.fetchone()
            cur.close()
            con.close()
            return UserProjectPermissions(row[0])
        except mdb.Error, e:
            raise FPSysException('Failed getUserPermissions:' + str(e))
        
    def getUsers(self):
    #-----------------------------------------------------------------------
    # Get users associated with access to project.
    # Returns list of tuples (ident, permissions).
    # Raises FPSysException on error.
    #
        try:
            con = getFpsysDbConnection()
            with closing(con.cursor()) as cur:
                qry = 'select login, userProject.permissions from user join userProject ' + \
                    'on id=user_id where project_id=%s'
                cur.execute(qry, (self.getId(),))
                users = []
                for row in cur.fetchall():
                    users.append((row[0], row[1]))
                return users
        except mdb.Error as e:
            raise FPSysException('DB error: {}'.format(str(e)))


    @staticmethod
    def getById(pid):
    # Return project instance or None or errormsg
    # Could be change to get by id or name easily enough..
        try:
            con = getFpsysDbConnection()
            qry = "select id, name, dbname from project where id = %s"
            cur = con.cursor()
            cur.execute(qry, (pid,))
            resRow = cur.fetchone()
            if resRow is None:
                return None
            return Project(resRow[0], resRow[1], resRow[2])
        except mdb.Error, e:
            errmsg = 'Error in Project.getById: {0}'.format(str(e))
            util.flog(errmsg)
            return errmsg
        
    @staticmethod
    def getModelProjectById(pid):
    # Returns object/None/errorString
        fpsysProj = Project.getById(pid)
        if not isinstance(fpsysProj, Project):
            return fpsysProj
        dbc = models.getDbConnection(fpsysProj.dbName())
        mproj = models.Project.getByName(dbc, fpsysProj.getName())
        return mproj

    @staticmethod
    def delete(projId):
    # Delete specified project.
    # If project has own database, with no other projects in it, then delete
    # database, and records in fpsys.
        proj = Project.getById(projId)
        if not isinstance(proj, Project):
            return "Cannot find project"
        dbname = proj.dbName()

        # delete within database first:
        dbc = proj.db()
        models.Project.delete(dbc, projId)
        count = models.Project.countProjects(dbc)
        dbc.close()

        # delete from fpsys:
        try:
            con = getFpsysDbConnection()
            cur = con.cursor()
            cur.execute("delete from project where id = %s", (projId,))
            con.commit()
            cur.close()
            con.close()
            # If no projects left in database, delete the database:
            if count == 0:
                con = getFpsysDbConnection()
                cur = con.cursor()
                cur.execute("drop database {}".format(dbname))
                con.commit()
                cur.close()
                con.close()
        except mdb.Error, e:
            errmsg = 'Error in Project.getById: {0}'.format(str(e))
            util.flog(errmsg)
            return errmsg

        # remove database if no other projects in it:
        #return "NOT IMPLEMENTED"
        return None

    @staticmethod
    def getAllProjects():
    #-----------------------------------------------------------------------
    # Get list of all projects (as Project), or raises FPSysException.
        try:
            con = getFpsysDbConnection()
            qry = 'select id, name, dbname from project p'
            cur = con.cursor()
            cur.execute(qry)
            projects = []
            for row in cur.fetchall():
                projects.append(Project(row[0], row[1], row[2]))
            return projects
        except mdb.Error, e:
            raise FPSysException(str(e))

def getProjectDBname(projectSpecifier):
#-----------------------------------------------------------------------
# Returns dbname for project identified by either strint name or int id - r None on error.
#
    # work out if we have a project name or id:
    if isinstance(projectSpecifier, basestring):
        specifier = 'name'
    elif isinstance(projectSpecifier, int):
        specifier = 'id'
    else:
        return None

    try:
        con = getFpsysDbConnection()
        qry = "select dbname from project where {} = %s".format(specifier)
        cur = con.cursor()
        cur.execute(qry, (projectSpecifier,))
        foo = cur.fetchone()
        return None if foo is None else foo[0]
    except mdb.Error, e:
        return None

def fpSetupG(g, userIdent=None, projectName=None):
    g.userName = userIdent
    g.user = None if userIdent is None else User.getByLogin(userIdent)
    g.userProject = None # this has to be set explicitly at the moment


##########################################################################################
