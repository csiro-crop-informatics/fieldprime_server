# websess.py
# Michael Kirk 2013
#

import sha, shelve, time, os
import fp_common.models as models
import fp_common.fpsys as fpsys
from flask import g

class FPsessException(Exception):
    pass


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
# WebSess objects store the following data:
# data['id'] - fpsys.project.id
# data['projectName'] - fpsys.project.name
# data['dbname'] - fpsys.project.dbname
# data['projectAccess'] - fpsys.userProject.permissions
# data['lastvisit'] - timestamp of last use
# data['userident'] - user ident
# data['loginType'] - password validation method. Only used in fpRestApi.urlLogin, which is not currently used.
#

class FPsess(object):
    def __init__(self, userIdent, projId):
        self.userIdent = userIdent
        self.projId = projId
        
        # Get sys project:
        sysProj = fpsys.Project.getById(projId) # get fpsys project
        if sysProj is None:
            raise FPsessException('Specified project not found')

        # Check access:
        try:
            perms = sysProj.getUserPermissions(userIdent)
        except fpsys.FPSysException as fpse:
            raise FPsessException(fpse)
        user = fpsys.User.getByLogin(userIdent)
        if user is None:
            raise FPsessException('Specified user not found')

        if perms is None and not user.omnipotent():
            raise FPsessException('Not authorized')

        # get model db session and project:
        dbsess = sysProj.db()
        modelProj = models.Project.getById(dbsess, projId)# get model project
        if modelProj is None:
            raise FPsessException('Specified project not found')

        # Setup globals
        self.sysProj = sysProj
        self.dbsess = dbsess
        self.modelProj = modelProj
        self.userProjectPermissions = perms
        self.canAdmin = user.omnipotent() or perms.hasAdminRights()

    def setProject(self, userProject):
    #------------------------------------------------------------------
        self.__init__(self.userIdent, userProject.projectId())

    def getProjectName(self):
    #------------------------------------------------------------------
        return self.modelProj.getName()

    def getProjectId(self):
    #------------------------------------------------------------------
        return self.modelProj.getId()

    def getProject(self):
    #------------------------------------------------------------------
        return self.modelProj

    def getDbName(self):
    #------------------------------------------------------------------
        return self.sysProj.dbName()

    def getProjectAccess(self):
    #------------------------------------------------------------------
        return self.userProjectPermissions

    def getUserIdent(self):
    #------------------------------------------------------------------
        return self.userIdent

    def getUser(self):
    #------------------------------------------------------------------
    # Get user object (from fpsys) for current user. Or None if not possible.
        ident = self.getUserIdent()
        if ident is None:
            return None
        return fpsys.User.getByLogin(ident)

    def adminRights(self):
    #------------------------------------------------------------------
    # Does this session have admin rights for its current project?
        return self.canAdmin

    def db(self):
    #------------------------------------------------------------------
    # Returns sqlalchemy Session object.
        return self.dbsess
    
    def close(self):
        pass


