# websess.py
# Michael Kirk 2013
#

import sha, shelve, time, os
import fp_common.models as models
import fp_common.fpsys as fpsys

#
# Masks and functions for project permissions:
#
PROJECT_ACCESS_ALL = 0xffffffff
PROJECT_ACCESS_ADMIN = 0x00000001
def adminAccess(perms):
    return bool(perms & PROJECT_ACCESS_ADMIN)

#
# WebSess
# Server side session object. Once created, a session will have an id, and state
# is stored in the file system. This may be retrieved by specifying an existing
# id on creation of WebSess object (eg the id originally created may be sent in
# a cookie stored by the browser). Sessions can report how long since last use,
# where "use" is actually a function call to set the last use time.
# The stored state includes:
# . Last use time
# . User name
# . User password
#
# It also provides a database connection, which is generated on request, using the
# stored username and password.
#
class WebSess(object):
    def __init__(self, forceNew=False, sid=None, timeout=900, sessFileDir='/tmp'):
    #------------------------------------------------------------------
        self.mTimeout = timeout
        # set sid or create new one:
        if not forceNew and sid:
            self.mSid = sid
        else:
            self.mSid = sha.new(repr(time.time())).hexdigest()  # Should we salt this?

        # create if necessary session storage dir:
        if not os.path.exists(sessFileDir):
            try:
                os.mkdir(sessFileDir, 02770)
            # If the apache user can't create it manually
            except OSError, e:
                errmsg =  """%s when trying to create the session directory. Create it as '%s'""" % (e.strerror, os.path.abspath(sessFileDir))
                raise OSError, errmsg
        # create  or open session file:
        self.sessFile = sessFileDir + '/sess_' + self.mSid
        self.data = shelve.open(self.sessFile, writeback=True)
        os.chmod(self.sessFile, 0660)

    def close(self):
    #------------------------------------------------------------------
        sessFile = self.sessFile
        self.data.close()
        os.remove(sessFile)

    def sid(self):
    #------------------------------------------------------------------
        return self.mSid

    def resetLastUseTime(self):
    #------------------------------------------------------------------
        self.data['lastvisit'] = repr(time.time())

    def _getLastUseTime(self):
    #------------------------------------------------------------------
        lv = self.data.get('lastvisit')
        return float(lv) if lv else False

    def _timeSinceUse(self):
    #------------------------------------------------------------------
        return float(time.time() - float(self.data.get('lastvisit')))

    def setProject(self, project, dbname, access):
    #------------------------------------------------------------------
        self.data['projectName'] = project
        self.data['dbname'] = dbname
        self.data['projectAccess'] = access
        if hasattr(self, 'mDBsess'):
            del(self.mDBsess)

    def getProjectName(self):
    #------------------------------------------------------------------
        return self.data.get('projectName')

    def getProject(self):
    #------------------------------------------------------------------
    # Return project object, or None.
    # This is a handy function, but it may hide, in the calling code,
    # a reference to the db (in that there is a reference in here,
    # and this is not the models module. But it really is quite neat.
    #
        return models.getProjectByName(self.db(), self.data.get('projectName'))

    def getDbName(self):
    #------------------------------------------------------------------
        return self.data.get('dbname')

    def getProjectAccess(self):
    #------------------------------------------------------------------
        return self.data.get('projectAccess')

    def setUserIdent(self, user):
    #------------------------------------------------------------------
        self.data['userident'] = user

    def getUserIdent(self):
    #------------------------------------------------------------------
        return self.data.get('userident')

    def getUser(self):
    #------------------------------------------------------------------
    # Get user object (from fpsys) for current user. Or None if not possible.
        ident = self.getUserIdent()
        if ident is None:
            return None
        return fpsys.User.getByLogin(ident)

    def setLoginType(self, loginType):
    #------------------------------------------------------------------
        self.data['loginType'] = loginType

    def getLoginType(self):
    #------------------------------------------------------------------
        return self.data.get('loginType')

    def valid(self):
    #------------------------------------------------------------------
        valid = self.data.get('userident') and self._timeSinceUse() < self.mTimeout
        if valid:
            self.resetLastUseTime()
        return valid

    def adminRights(self):
    #------------------------------------------------------------------
    # Does this session have admin rights for its current project?
        return self.getProjectAccess() & PROJECT_ACCESS_ADMIN

    def db(self):
    #------------------------------------------------------------------
    # Returns sqlalchemy Session object.
    # Note the dbsess doesn't get saved in the shelf, but is cached in this object.
        if not hasattr(self, 'mDBsess'):
            self.mDBsess = models.getDbConnection(self.getDbName())
        return self.mDBsess

