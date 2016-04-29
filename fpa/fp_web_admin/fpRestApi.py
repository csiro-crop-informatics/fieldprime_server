# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
# see http://blog.miguelgrinberg.com/post/restful-authentication-with-flask, or more
# recent and better, find the github page for flask_httpauth
#
# Todo:
# - long term time out, or numUses value for token. To limit damage from stolen token.
# - If we create userProject in wrap_api, update original funcs to use it.
#

from flask import Blueprint, current_app, request, Response, jsonify, g, abort, url_for
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from functools import wraps
import simplejson as json
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import re

import fp_common.models as models
import fp_common.fpsys as fpsys
import websess
from fp_common.const import LOGIN_TIMEOUT, LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL
import fpUtil
import fp_common.util as util
from const import *

### Initialization: ######################################################################
webRest = Blueprint('webRest', __name__)

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('fptoken')
multi_auth = MultiAuth(basic_auth, token_auth)

def mkdbg(msg):
    pass
    #print msg

### Constants: ###########################################################################

API_PREFIX = '/fpv1/'

### Response functions: ##################################################################
#^-----------------------------------
#: API responses are in json format. Each response is a JSON object, which may contain 
#: the following fields:
#: success : indicates operation succeeded, value is informational string.
#: error : indicates operation failed, value is informational string 
#:     NB each response should contain either a success or error field.
#: url : resource url, eg url of newly created resource.
#: data : JSON object or array, eg requested data
#$

def apiResponse(succeeded, statusCode, msg=None, data=None, url=None):
#-----------------------------------------------------------------------------------------
# Return standard format json object for the API. This may contain the following fields.
# success : Mandatory, string indication of success
#    
    obj = {}
    if succeeded:
        obj['success'] = msg if msg is not None else 'ok'
    else:
        obj['error'] = msg if msg is not None else 'error'
    if url is not None: obj['url'] = url
    if data is not None: obj['data'] = data 
    return Response(json.dumps(obj), status=statusCode, mimetype='application/json')

def jsonErrorReturn(errmsg, statusCode):
    return apiResponse(False, statusCode, msg=errmsg)

def jsonReturn(jo, statusCode):
    return Response(json.dumps(jo), status=statusCode, mimetype='application/json')

def jsonSuccessReturn(msg='success', statusCode=HTTP_OK):
    return apiResponse(True, statusCode, msg=msg)


def fprGetError(jsonResponse):
# Returns the error message from the response, IF there was an error, else None.
# This function intended to abstract the way we encode errors in the response,
# all users of the rest api should use this to get errors.
    if "error" in jsonResponse:
        return jsonResponse["error"]
    return None

def fprHasError(jsonResponse):
    return "error" in jsonResponse

def fprData(jsonResponse):
    return jsonResponse["data"]

# @webRest.errorhandler(401)
# def custom_401(error):
#     print 'in custom_401'
#     return Response('<Why access is denied string goes here...>', 401)
#                     #, {'WWWAuthenticate':'Basic realm="Login Required"'})


class FPRestException(Exception):
    pass

### Authentication: ######################################################################

@webRest.route(API_PREFIX + 'token', methods=['GET'])
@basic_auth.login_required
def urlGetToken():
#-------------------------------------------------------------------------------------------------
# Returns, in a JSON object, a token for user.
# The returned token may be used as a basic authentication username
# for subsequent calls to the api (for up to 600 seconds).
# This is in place of repeatedly sending the real username and password.
# When using the token as the username, the password is not used, so any
# value can be given.
#
    token = generate_auth_token(g.userName)
    retObj = {'token': token.decode('ascii'), 'duration': 600}
    #retObj = jsonify({'token': token.decode('ascii'), 'duration': 600})
    return apiResponse(True, HTTP_OK, data=retObj) #, url=url_for('urlGetUser'))
    
# @webRest.route(API_PREFIX + 'grant/<login>/<permission>', methods=['GET'])
# @basic_auth.login_required
# def authUser(login, permission):
#     pass


def generate_auth_token(username, expiration=600):
# Return a token for the specified username. This can be used
# to authenticate as the user, for the specified expiration
# time (which is in seconds).
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    token = s.dumps({'id': username})
    mkdbg('generate_auth_token: {}'.format(token))
    return token

def verify_auth_token(token):
# MFK need to pass back expired indication somehow    
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        mkdbg('verify_auth_token:SignatureExpired token: {}'.format(token))
        return None    # valid token, but expired
    except BadSignature:
        mkdbg('verify_auth_token:BadSignature token: {}'.format(token))
        return None    # invalid token
    user = data['id']
    return user

@basic_auth.verify_password
def verify_password(user, password):
# Password check.
# This is invoked by the basic_auth.login_required decorator.
# If verification is successful:
#    g.userName is set to the user login
#    g.newToken is set to a new authentication token
#
    # try to authenticate with username/password
    check = fpsys.userPasswordCheck(user, password)
    if not check:
        mkdbg('verify_password: fpsys.userPasswordCheck failed')
        return False
    fpsys.fpSetupG(g, userIdent=user)
    g.newToken = generate_auth_token(user)
    return True

@token_auth.verify_token
def verify_token(token):
# Note parameter is retrieved from www-authenticate header, and if there we should use it.
# But in the absence, we look in cookie - and then perhaps in json?
# NB - it turns out this function is not called in the absence of www-authenticate header.
# So the cookie functionality is useful only in that it allows you to
# add a dummy token value in the www-authenticate header, under the assumption
# that you're passing a cooky with the correct value in it.
    mkdbg('verify_token({})'.format(token))
    user = verify_auth_token(token)
    if not user: # Try with cooky
        ctoken = request.cookies.get(NAME_COOKIE_TOKEN)
        mkdbg('verify_token  cooky {}'.format(str(ctoken)))
        if ctoken is None: return False
        user = verify_auth_token(ctoken)
        if not user:
            mkdbg('verify_token: not user')
            return False
    # Reset token
    g.newToken = generate_auth_token(user)
    mkdbg('verify_token newToken: {}'.format(g.newToken))
    fpsys.fpSetupG(g, userIdent=user)
    return True


##########################################################################################
### Access Points: #######################################################################
##########################################################################################

def wrap_api_func(func):
#-------------------------------------------------------------------------------------------------
# Get parameters dictionary from request (assumed to be in context). This can be from json, or
# from form if json is not present. This param dictionary, and the user are passed to func.
# Resets token cookie, with g.newToken, assumed to be set (perhaps we should be doing that here).
# func should return a response.
# request is assumed to be available
# func should have first params: userid, params.
# If there is a parameter 'projId' in **kwargs, then g.userProject is set. Unless the
# user doesn't have at least view access to the project, in which case authorization error
# is returned. NB, this may be a nuisance where you want an omnipotent user to be able to do
# things without being configured to have access to each project (in which case, don't call
# the parameter 'projId'). One option here would be to set g.userProject to a dummy UserProject
# object with full permissions.
#
    @wraps(func)
    def inner(*args, **kwargs):
        if request.json is None and request.form is not None:
            params = request.form
        elif request.json is not None: # and request.form is None:   Note if both json and form, we use json only
            params = request.json
        else:
            return jsonErrorReturn('Missing parameters', HTTP_BAD_REQUEST)
        
        if 'projId' in kwargs:
            # Check permissions and get UserProject object:
            try:
                up = fpsys.UserProject.getUserProject(g.userName, kwargs['projId'])
            except fpsys.FPSysException as fpse:
                return jsonErrorReturn('Unexpected error: {}'.format(fpse), HTTP_SERVER_ERROR)
            if up is None:
                return jsonErrorReturn('No access for user {} to project'.format(g.userName), HTTP_UNAUTHORIZED)
            if isinstance(up, basestring):
                return jsonErrorReturn('Unexpected error: {}'.format(up), HTTP_SERVER_ERROR)
            g.userProject = up

        ret = func(g.userName, params, *args, **kwargs)
        ret.set_cookie(NAME_COOKIE_TOKEN, g.newToken)
        return ret
    return inner


### TraitInstance Attribute: #################################################################

def _checkTiAttributeStuff(projId, tiId):
#----------------------------------------------------------------------------------------------
# Check permissions for ti attribute ops. If OK, returns the ti,
# else returns error Response.
    # Check user has rights for this operation:
    up = g.userProject
    if up is None or not up.hasPermission(fpsys.UserProject.PERMISSION_ADMIN):
        return jsonErrorReturn('Requires project admin rights', HTTP_UNAUTHORIZED)
    
    # Check ti is in project:
    ti = models.getTraitInstance(models.getDbConnection(up.dbname()), tiId)
    if ti is None:
        return jsonErrorReturn('invalid trait instance', HTTP_BAD_REQUEST)
    if ti.getTrial().getProject().getId() != projId:
        return jsonErrorReturn('invalid trait instance for project', HTTP_BAD_REQUEST)
    return ti

@webRest.route(API_PREFIX + 'projects/<int:projId>/ti/<int:tiId>/attribute', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateTiAttribute(userid, params, projId, tiId):
#----------------------------------------------------------------------------------------------
# Create attribute for the TI specified in the URL.
# The attribute name must be present as a url parameter "name".
#
    ti = _checkTiAttributeStuff(projId, tiId)
    if not isinstance(ti, models.TraitInstance):
        return ti

    # Get name proposed for attribute:
    name = request.json.get('name')
    if not name:
        return jsonErrorReturn('invalid name', HTTP_BAD_REQUEST)

    # Create or rename attribute for the ti:
    tiAtt = ti.getAttribute()
    if tiAtt is None:
        # Create it:
        att = ti.createAttribute(name)
        if att is None:
            return jsonErrorReturn('Cannot create attribute, may be invalid name', HTTP_BAD_REQUEST)
    else:
        # Reset the name:
        tiAtt.setName(name)  # error return
    return jsonSuccessReturn("Attribute Created")

@webRest.route(API_PREFIX + 'projects/<int:projId>/ti/<int:tiId>/attribute', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteTiAttribute(userid, params, projId, tiId):
#----------------------------------------------------------------------------------------------
    ti = _checkTiAttributeStuff(projId, tiId)
    if not isinstance(ti, models.TraitInstance):
        return ti
    errmsg = ti.deleteAttribute()
    if errmsg is None:
        return jsonSuccessReturn("Attribute Deleted")
    else:
        return jsonErrorReturn(errmsg, HTTP_SERVER_ERROR)

### Users: ####################################################################################

@webRest.route(API_PREFIX + 'users', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateUser(userid, params):
#----------------------------------------------------------------------------------------------
#^-----------------------------------
#: POST: API_PREFIX + 'users
#: Access: Requesting user needs create user permissions.
#: Input: {
#:   'ident': ,
#:   'password': ,
#:   'fullname': ,
#:   'loginType': ,
#:   'email': 
#: }
#: Success Response:
#:   Status code: HTTP_CREATED
#:   url: <new user url>
#:   
#$   
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER):
        return jsonErrorReturn("no user create permission", HTTP_UNAUTHORIZED)
    
    try:
        # check all details provided (should be infra)
        login = params.get('ident')
        loginType = params.get('loginType')
        if login is None or loginType is None:
            return jsonErrorReturn("login and loginType required", HTTP_BAD_REQUEST)
        loginType = int(loginType)
        
        # check if user already exists
        if fpsys.User.getByLogin(login) is not None:
            return jsonErrorReturn("User with that login already exists", HTTP_BAD_REQUEST)
    
        # create them
        if loginType == LOGIN_TYPE_LOCAL:
            password = params.get('password')
            fullname = params.get('fullname')
            email = params.get('email')
            # Validation - should be by infrastructure..
            if password is None or fullname is None:
                return jsonErrorReturn("password and fullname required for local user", HTTP_BAD_REQUEST)        
            if not util.isValidName(fullname):
                return jsonErrorReturn('Invalid user name', HTTP_BAD_REQUEST)
            if not util.isValidPassword(password):
                return jsonErrorReturn('Invalid password', HTTP_BAD_REQUEST)
            if not util.isValidEmail(email):
                return jsonErrorReturn("Invalid email address", HTTP_BAD_REQUEST)
            errmsg = fpsys.addLocalUser(login, fullname, password, email)
        elif loginType == LOGIN_TYPE_***REMOVED***:
            errmsg = fpsys.add***REMOVED***User(login)
        else:
            errmsg = 'Invalid loginType'
        if errmsg is not None:
            return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
        return apiResponse(True, HTTP_CREATED, msg='User {} created'.format(login),
                url=url_for('webRest.urlGetUser', ident=login, _external=True))
    except Exception, e:
        return jsonErrorReturn('Problem in REST create user: ' + str(e), HTTP_BAD_REQUEST)
    
@webRest.route(API_PREFIX + 'users', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetUsers(userid, params):
#^-----------------------------------
#: GET: API_PREFIX + users
#: Requesting user needs omnipotence permissions.
#: Input: none
#: Success Response:
#:   Status code: HTTP_CREATED
#:   data: [
#:     {
#:       'url':<user url>,
#:       'fullname':<user name>,
#:       'email':<user email>
#:     }
#:   ]
#$   
    # Check permissions:
    if not g.user.omnipotent():
        return jsonErrorReturn("No permission", HTTP_UNAUTHORIZED)

    users = fpsys.User.getAll()
    if users is None:
        return jsonErrorReturn('Problem getting users', HTTP_SERVER_ERROR)
    retUsers = [{'url':url_for('webRest.urlGetUser', ident=u.getIdent()),
                 'fullname':u.getName(),
                 'email':u.getEmail(),
                 'ident':u.getIdent()
                 } for u in users]
    return apiResponse(True, HTTP_OK, data=retUsers)
    
@webRest.route(API_PREFIX + 'users/<ident>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetUser(userid, params, ident):
#^-----------------------------------
#: GET: API_PREFIX + users/<ident>
#: Requesting user needs create user permissions, or to be the requested user.
#: Input: none
#: Success Response:
#:   Status code: HTTP_CREATED
#:   data: {
#:     'fullname':<user name>,
#:     'email':<user email>,
#:   }
#$   
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_CREATE_USER) and userid != ident:
        return jsonErrorReturn("no permission to access user", HTTP_UNAUTHORIZED)
        
    user = fpsys.User.getByLogin(ident)
    if user is None:
        return jsonErrorReturn("Cannot access user", HTTP_BAD_REQUEST)
    retObj = {'fullname':user.getName(), 'email':user.getEmail()}
    return apiResponse(True, HTTP_OK, data=retObj)

@webRest.route(API_PREFIX + 'users/<ident>', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteUser(userid, params, ident):
#----------------------------------------------------------------------------------------------
#^
#: DELETE: API_PREFIX + 'users/<ident>
#: Requesting user needs create user permissions, and cannot delete self.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#$   
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER) and userid != ident:
        return jsonErrorReturn("no permission to delete user", HTTP_UNAUTHORIZED)
    errmsg = fpsys.User.delete(ident)
    if errmsg is not None:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)  # need to distinguish server error, user not found..
    return apiResponse(True, HTTP_OK)

@webRest.route(API_PREFIX + 'users/<ident>', methods=['PUT'])
@multi_auth.login_required
@wrap_api_func
def urlUpdateUser(userid, params, ident):
#----------------------------------------------------------------------------------------------
#^-----------------------------------
#: PUT: API_PREFIX + users/<ident>
#: Access: Requesting user needs create user permissions, or to be the updated user.
#: Only LOCAL users can be updated (not ***REMOVED***).
#: Input: {
#:   'oldPassword': ,
#:   'fullname': ,
#:   'email': 
#:   'password': ,
#: }
#: All input fields optional other than oldPassword which must correctly specify the
#: current password if the requesting user is not the user being updated - i.e. user
#: self modification cannot be effected with token authorization alone.
#: Success Response:
#:   Status code: HTTP_CREATED
#$   
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_CREATE_USER):
        if userid != ident:
            return jsonErrorReturn("no user update permission", HTTP_UNAUTHORIZED)
        oldPass = params.get('oldPassword')
        if oldPass is None or not fpsys.localPasswordCheck(ident, oldPass):
            return jsonErrorReturn("Invalid current password", HTTP_UNAUTHORIZED)                
        
    try:
        user = fpsys.User.getByLogin(ident)
        if user is None:
            return jsonErrorReturn("user not found", HTTP_NOT_FOUND)
        if user.getLoginType() != LOGIN_TYPE_LOCAL:
            return jsonErrorReturn("Cannot update non-local users", HTTP_UNAUTHORIZED)
                    
        password = params.get('password')
        if password is not None and util.isValidPassword(password):
            errmsg = user.setPassword(password) # should be exception
            if errmsg is not None:
                return jsonErrorReturn('Problem updating password: ' +  errmsg, HTTP_BAD_REQUEST)            
            
        fullname = params.get('fullname')
        if fullname is not None:
            user.setName(fullname)
        email = params.get('email')
        if email is not None:
            user.setEmail(email)
        
        if fullname is not None or email is not None:       
            errmsg = user.save()
            if errmsg is not None:
                return jsonErrorReturn('Problem in updateUser: ' +  errmsg, HTTP_BAD_REQUEST)
        return apiResponse(True, HTTP_OK)
    except Exception, e:
        return jsonErrorReturn('Problem in updateUser: ' + str(e), HTTP_BAD_REQUEST)
    

### Projects: ############################################################################

@webRest.route(API_PREFIX + 'projects', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetProjects(userid, params):
# MFK maybe restrict contact details to admin?    
#^-----------------------------------
#: GET: API_PREFIX + projects
#: Gets projects accessible to calling user.
#: Input: none
#: Success Response:
#:   Status code: HTTP_CREATED
#:   data: [
#:     {
#:       'url': <project url>,
#:       'projectName':<user url>,
#:       //'contactName':<user name>,
#:       //'contactEmail':<user email>
#:     }
#:   ]
#$   
    (plist, errmsg) = fpsys.getUserProjects(g.userName)
    if errmsg:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    retProjects = [{'projectName':p.getProjectName(),
                    'url':url_for('webRest.urlGetProject', projId=p.getProjectId())
                    } for p in plist]
    return apiResponse(True, HTTP_OK, data=retProjects)

@webRest.route(API_PREFIX + 'projects/<int:projId>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetProject(userid, params, projId):
#^-----------------------------------
#: GET: API_PREFIX + projects/<projId>
#: Get project - which must be accessible to calling user.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [
#:     {
#:       'projectName':<user url>
#:     }
#:   ]
#$   
    if g.userProject is None:
        return jsonErrorReturn('no permissions', HTTP_UNAUTHORIZED)
    ret = {'projectName':g.userProject.getProjectName()}
    return apiResponse(True, HTTP_OK, data=ret)

@webRest.route(API_PREFIX + 'projects', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateProject(userid, params):
#-----------------------------------------------------------------------------------------
# TODO: Perhaps rather than contact name and email, we should require an FP user ident,
# this should be just be the adminLogin.    
#^-----------------------------------
#: POST: API_PREFIX + 'projects'
#: Access: Requesting user needs create omnipotenct permissions.
#: Input: {
#:   'projectName': ,
#:   'contactName': <Name of contact person>,
#:   'contactEmail': <email of contact person>,
#:   'ownDatabase': Boolean - currently must be True,
#:   'adminLogin': <FieldPrime ident of user to have admin access>
#: }
#: NB, ownDatabase is assumed to be true, and a new database is created for the
#: project. To create a project within an existing database, an API call on
#: an existing project would be needed (to create sub project).
#: Success Response:
#:   Status code: HTTP_CREATED
#:   url: <url of created project>
#:
#$   
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_OMNIPOTENCE):
        return jsonErrorReturn("No permission for project creation", HTTP_UNAUTHORIZED)
    try:
        # todo parameter checks, perhaps, checks are done in makeNewProject
        projectName = params.get('projectName')
        contactName = params.get('contactName')
        contactEmail = params.get('contactEmail')
        ownDatabase = params.get('ownDatabase')
        adminLogin = params.get('adminLogin')
        if ownDatabase == 'true':
            ownDatabase = True
        elif ownDatabase == 'false':
            ownDatabase = False
        else:
            ownDatabase = True

        # Check admin user exists:
        adminUser = fpsys.User.getByLogin(adminLogin)
        if adminUser is None:
            return jsonErrorReturn("Unknown admin user ({}) does not exist".format(adminLogin), HTTP_BAD_REQUEST)

        # Create the project:
        proj = models.Project.makeNewProject(projectName, ownDatabase, contactName, contactEmail, adminLogin)
#         if proj is None:
#             print 'proj is None'
#         else:
#             if not isinstance(proj, models.Project):
#                 print 'proj is not proj'
#             else:
#                 print 'proj id {}'.format(proj.getId())
#         if isinstance(proj, basestring):
#             return jsonErrorReturn(proj, HTTP_BAD_REQUEST)

        # Add the adminUser to the project:
        errmsg = fpsys.addUserToProject(adminUser.getId(), projectName, 1)  #MFK define and use constant
        if errmsg is not None:
            return jsonErrorReturn('project {} created, but could not add user {} ({})'.format(projectName,
                adminLogin, errmsg), HTTP_BAD_REQUEST)
    except Exception, e:
        return jsonErrorReturn('Problem creating project: ' + str(e), HTTP_BAD_REQUEST)

    # Return representation of the project, or a link to it?
    return apiResponse(True, HTTP_CREATED, msg='Project {} created'.format(projectName),
                url=url_for('webRest.urlGetProject', projId=proj.getId(), _external=True))

def getCheckProjectsParams(params):
    pxo = {}
    
    projectName = params.get('projectName')
    if projectName is not None and not util.isValidIdentifier(projectName):
        raise FPRestException('Invalid project name')
    pxo['projectName'] = projectName
    
    contactName = params.get('contactName')
    if contactName is not None and not util.isValidName(contactName):
        raise FPRestException('Invalid contact name')
    pxo['contactName'] = contactName
    
    contactEmail = params.get('contactEmail')
    if contactEmail is not None and not util.isValidEmail(contactEmail):
        raise FPRestException('Invalid email')
    pxo['contactEmail'] = contactEmail
    
    adminLogin = params.get('adminLogin')
    if adminLogin is not None:
        adminUser = fpsys.User.getByLogin(adminLogin)
        if adminUser is None:
            raise FPRestException("Unknown admin user ({}) does not exist".format(adminLogin))
    return {
            'projectName':projectName,
            'contactName':contactName,
            'contactEmail':contactEmail,
            'adminLogin':adminLogin
            }

@webRest.route(API_PREFIX + 'projects/<int:xprojId>', methods=['PUT'])
@multi_auth.login_required
@wrap_api_func
def urlUpdateProject(userid, params, xprojId):
#----------------------------------------------------------------------------------------------
#^-----------------------------------
#: PUT: API_PREFIX + projects/<ident>
#: Access: Requesting user needs omnipotence, or to have admin access to the project.
#: Input: {
#:   'projectName': <Project name>,
#:   'contactName': <Name of contact person>,
#:   'contactEmail': <email of contact person>,
#:   'adminLogin': <FieldPrime ident of user to have admin access> NOT SUPPORTED
#: }
#: Success Response:
#:   Status code: HTTP_OK
#$   
    try:
        # Check permissions:
        userProject = fpsys.UserProject.getUserProject(g.userName, xprojId)
        if userProject is None and not g.user.omnipotent():
                return jsonErrorReturn('No permissions', HTTP_UNAUTHORIZED)

        pxo = getCheckProjectsParams(params)
    except Exception, e:
        return jsonErrorReturn('Problem project update: ' + str(e), HTTP_BAD_REQUEST)
    
    # now update stuff:
    # Need to update name in both fpsys and project database.
    # Other details in project database.
    
    # get fpsys proj obj:
    sysProj = fpsys.Project.getById(xprojId)
    if sysProj is None:
        return jsonErrorReturn('Project not found', HTTP_NOT_FOUND)

    # get local proj obj:
    lproj = models.Project.getById(sysProj.db(), xprojId)
    if lproj is None:
        return jsonErrorReturn('Cannot get project', HTTP_SERVER_ERROR)
        
    if pxo['projectName'] is not None:
        sysProj.setName(pxo['projectName'])
        errmsg = sysProj.saveName()
        if errmsg is not None:
            return jsonErrorReturn(errmsg, HTTP_SERVER_ERROR)
        lproj.setName(pxo['projectName'])
    if pxo['contactName'] is not None:
        lproj.setContactName(pxo['contactName'])
    if pxo['contactEmail'] is not None:
        lproj.setContactEmail(pxo['contactEmail'])

    lproj.save()  # check worked..
    return apiResponse(True, HTTP_OK)

@webRest.route(API_PREFIX + 'projects/<int:xprojId>', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteProject(userid, params, xprojId):
#----------------------------------------------------------------------------------------------
#^
#: DELETE: API_PREFIX + 'projects/<id>
#: Requesting user needs omnipotence permissions.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#$   
    # check permissions
    if not g.user.omnipotent():
        return jsonErrorReturn("no permission to delete project", HTTP_UNAUTHORIZED)
    errmsg = fpsys.Project.delete(xprojId)
    if errmsg is not None:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)  # need to distinguish server error, user not found..
    return apiResponse(True, HTTP_OK)

@webRest.route(API_PREFIX + 'projects/<int:xprojId>/users/', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlAddProjectUser(userid, params, xprojId):
#----------------------------------------------------------------------------------------------
#^
#: POST: API_PREFIX + 'projects/<id>/users/<ident>
#: Requesting user needs omnipotence permissions or admin access to project.
#: Input: {
#:   "ident":<ident>,
#:   "admin":<boolean>
#: }
#: Success Response:
#:   Status code: HTTP_OK
#$   
    # check permissions
    userProject = fpsys.UserProject.getUserProject(g.userName, xprojId)
    if userProject is None and not g.user.omnipotent():
            return jsonErrorReturn('No permissions', HTTP_UNAUTHORIZED)

    ident = params.get('ident')
# check user exists:

#     if ident is not None and not util.isValidIdentifier(projectName):
#         raise FPRestException('Invalid project name')
#     pxo['projectName'] = projectName
#     
#     contactName = params.get('contactName')
#     if contactName is not None and not util.isValidName(contactName):
#         raise FPRestException('Invalid contact name')
#     pxo['contactName'] = contactName
    
    
    fpsys.addUserToProject(ident, projectName, perms)

#@webRest.route(API_PREFIX + 'XXXprojects/<path:path>', methods=['POST'])
@basic_auth.login_required
def old_createProject(path):
    return 'You want path: %s' % path

    # top level dir called 'projects'? 'users'
    parent = request.json.get('parent')
    name = request.json.get('name')
    if parent is None or name is None:
        abort(HTTP_BAD_REQUEST)    # missing arguments

    # Need check user has permission. Need parent project, or path perhaps: /fp/projects/foo/bar
    # create the project:
    proj = models.Project();


### Trials: ############################################################################

# Todo trial delete
TEST_trial = '''
FP=http://0.0.0.0:5001/fpv1

# Get token:
curl -u fpadmin:foo -i -X GET $FP/token

# Create trial:
curl -u fpadmin:foo -i -X POST -H "Content-Type: application/json" \
     -d '{"trialName":"testCreateTrial"}' $FP/projects/1/trials
     
curl -u fpadmin:foo -i -X POST -H "Content-Type: application/json" \
     -d '{"trialName":"testCreateTrial2", "trialYear":2016, "trialSite":"yonder", "trialAcronym":"123",
     "nodeCreation":"false", "rowAlias":"range", "colAlias":"run"}' $FP/projects/1/trials 

TRIAL_URL=<url from create>
# Get Trial:
curl -u fpadmin:foo -i $TRIAL_URL

# Delete Trial:
curl -u fpadmin:foo -i -X DELETE $TRIAL_URL
     
'''
    
@webRest.route(API_PREFIX + 'projects/<int:projId>/trials', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateTrial(userid, params, projId):
# Parameters can be form or json.    
# Expects following parameters - all optional bar trialName.
#   trialName : name project - must be appropriate.
#   trialYear : text
#   trialSite : text
#   trialAcronym : text
#   nodeCreation : 'true' or 'false'
#   rowAlias : text
#   colAlias : text
#   
# If successful, returns in the json the URL for the created trial.
#
    # Check permissions:
    # We should have trial creation permissions, but this should be project specific
    # preferably with inheritance
    # At least need to check user has access to project
    mkdbg('urlCreateTrial({}, {})'.format(userid, projId))
    userProj = fpsys.UserProject.getUserProject(userid, projId)
    if userProj is None:
        return jsonErrorReturn("No project access for user", HTTP_UNAUTHORIZED)
    elif isinstance(userProj, basestring):
        return jsonErrorReturn("Error in trial creation: {}".format(userProj), HTTP_SERVER_ERROR)
    elif not isinstance(userProj, fpsys.UserProject):
        return jsonErrorReturn("Error in trial creation", HTTP_SERVER_ERROR)

    trialName = params.get('trialName')
    trialYear = params.get('trialYear')
    trialSite = params.get('trialSite')
    trialAcronym = params.get('trialAcronym')
    nodeCreation = params.get('nodeCreation')
    rowAlias = params.get('rowAlias')
    colAlias = params.get('colAlias')
        
    # check trial name provided and valid format:
    if trialName is None or not util.isValidIdentifier(trialName):
        return jsonErrorReturn("Invalid trial name", HTTP_BAD_REQUEST)        

    # check trial doesn't already exist:
    # Need to get project first, as this will identify the database
    # Tricky this - see websess. Probably need class Project in fpsys, getting details from
    # fpsys projects and within db project class
    proj = fpsys.Project.getModelProjectById(projId)
    if proj is None:
        return jsonErrorReturn("Error retrieving project in trial creation", HTTP_SERVER_ERROR)
    try:
        trial = proj.newTrial(trialName, trialSite, trialYear, trialAcronym)
    except models.DalError as e:
        return jsonErrorReturn("Error creating trial creation: {}".format(e.__str__()), HTTP_BAD_REQUEST)

    trial.setTrialProperty('nodeCreation', nodeCreation)
    trial.setNavIndexNames(rowAlias, colAlias)
    return apiResponse(True, HTTP_CREATED, msg='Trial {} created'.format(trialName),
            url=url_for('webRest.urlGetTrial', _external=True, projId=projId, trialId=trial.getId()))


@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetTrial(userid, params, projId, trialId):
    # check user has access to project
    trial = models.getTrial(g.userProject.db(), trialId)
    returnJson = { # perhaps we should have trial.getJson()
        "name":trial.getName(),
        "year":trial.getYear(),
        "site":trial.getSite(),
        "acronym":trial.getAcronym(),
        "nodeCreation":trial.getTrialProperty('nodeCreation'),
        "rowAlias":trial.navIndexName(0),
        "colAlias":trial.navIndexName(1)
    }
    return apiResponse(True, HTTP_OK, data=returnJson)
    
@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteTrial(userid, params, projId, trialId):
    # Need project admin access to delete
    if not g.userProject.hasAdminRights():
        return jsonErrorReturn('No administration access', HTTP_UNAUTHORIZED)
    models.Trial.delete(g.userProject.db(), trialId)
    return jsonSuccessReturn("Trial Deleted", HTTP_OK)
    
    
@webRest.route(API_PREFIX + 'projects/<int:projId>/trials<int:trialId>/nodes', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateNode(userid, params, projId, trialId):
#-----------------------------------------------------------------------------------------
# MFK, could have complex object, including attributes, or could have everything atomic,
# and have separate access point to create attributes and add values to them.
# Or we could have both, eventually. Separately is better I think. Reduces risk of
# unintentionally create new attributes by mistyping names, and allows defining the type
# of an attribute prior to loading values.
#
#
#
#^-----------------------------------
#: API_PREFIX + 'projects/<int:projId>/trials<int:trialId>/nodes'
#: Input JSON object:
#: {
#:   // MANDATORY fields:
#:   index1 : <positive integer>
#:   index2 : <positive integer>
#: 
#:   // OPTIONAL fields:
#:   description : <string>, optional
#:   barcode : <string>
#:   latitude : <number>
#:   longitude : <number>
#:   attributes : Array of {<string:attribute name>:<string:attribute value>}  MFK or should we do these separately?
#: }
#: 
#: Success Response:
#: Status code: HTTP_CREATED
#: url: <new node url>
#: data: absent
#$
    # Check permissions:
    
    # Check node with specified indicies doesn't already exist.
    pass

### Attributes: ##########################################################################

@webRest.route('/projects/<int:projId>/attributes/<int:attId>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlAttributeData(userid, params, projId, attId):
#---------------------------------------------------------------------------------
# Return nodeId:attValue pairs
# These are sorted by node_id.
# This is used in the admin web pages.
#
    # NB, check that user has access to project is done in wrap_api_func.
    natt = models.getAttribute(models.getDbConnection(fpsys.getProjectDBname(projId)), attId)
    vals = natt.getAttributeValues()
    data = []
    for av in vals:
        data.append([av.getNode().getId(), av.getValueAsString()])
    return Response(json.dumps(data), mimetype='application/json')

### Testing: #####################################################################################
TEST_STUFF = '''
#MFK - Could test from python, using requests module.

FP=http://0.0.0.0:5001/fpv1
AUTH=-ufpadmin:foo
alias prj='python -m json.tool'

JH='-H "Content-Type: application/json"'


#
# NB we need to create an initial user with admin permissions (which can then use the REST
# API to create other users):
#
# > mysql
# mysql> use fpsys
# mysql> insert user (login, name, passhash, login_type, permissions)
#        values ('fpadmin', 'FieldPrime Administrator', <PASSHASH>, 3, 1);
#
# use python to get passhash of password.
#

### User tests: ==========================================================================

# Create ***REMOVED*** user:
curl -u mk:m -i -X POST -H "Content-Type: application/json" \
     -d '{"login":"***REMOVED***","loginType":2}' $FP/users

# Get users:
curl $AUTH $FP/users | prj

# Create local user:
curl $AUTH -i -X POST -H "Content-Type: application/json" \
     -d '{"ident":"testu1","password":"m","fullname":"Mutti Krupp","loginType":3,"email":"test@fi.fi"}' $FP/users

# Ideally here we would extract new user url from output, and use that subsequently.

# Get user:
curl $AUTH $FP/users/testu1 | prj

# update user:
curl $AUTH -X PUT -H "Content-Type: application/json" \
    -d '{"fullname":"Muddy Knight", "email":"slip@slop.slap", "oldPassword":"m", "password":"secret"}' $FP/users/testu1

# get to check update:
curl -umk:secret $FP/users/testu1 | prj

# Delete user:
curl $AUTH -XDELETE $FP/users/testu1 

### Project tests: =======================================================================

# Create:
curl $AUTH -X POST -H "Content-Type: application/json" \
    -d '{"projectName":"testProj", "contactName":"js bach", "contactEmail":"bach@harmony.org", "adminLogin":"al"}' $FP/projects
    
# Update
curl $AUTH -X PUT -H "Content-Type: application/json" \
    -d '{"name":"newName", "contactName":"booboo", "contactEmail":"gonty@riff.raff"}' $FP/projects/1

# Delete:
curl $AUTH -X DELETE $FP/projects/1

==========================================================================================

# NB could first set mk in db without create user perms, and check get appropriate error.

# Test access:
curl -i -u kevin:blueberry $FP/projects

# Get token:
curl -u fpadmin:foo -i -X GET $FP/token
curl -u kevin:blueberry -i -X GET $FP/token

'''

# Document the REST API here?
API_REST_DOCO = '''
routes:

projects { /<projName> }
Get - returns ?
Post - create

trials { /<projName> } [ /<trialName> ]

'''

########################################################################################
### Old stuff, NOT in use: #############################################################
########################################################################################

#goEasy = True
def wr_check_session(func):
#-------------------------------------------------------------------------------------------------
# NB - USED FOR WEB ADMIN PAGES, NOT REALLY DIRECT REST.
# Decorator to check if in valid session.
# Generates function that has session as first parameter.
# If returnNoneSess is true, then the function is returned even if session is
# invalid, but with None as the session parameter - this can be used for pages
# that don't require a user to be logged in.
# NB Derived from fpWebAdmin:dec_check_session.
#
    @wraps(func)
    def inner(*args, **kwargs):
# is this secure? what if sid not in cooky?
        print 'wr_check_session'
        sid = request.cookies.get(NAME_COOKIE_SESSION) # Get the session id from cookie (if there)
        if sid is not None:
            sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, current_app.config['SESS_FILE_DIR']) # Create or get session object
        if sid is None or not sess.valid():  # Check if session is still valid
            return 'error: not logged in', 401
        return func(sess, *args, **kwargs) #if not goEasy else func(None, *args, **kwargs)
    return inner


@webRest.route('/trial/<trialId>/trait/<traitId>', methods=['DELETE'])
@wr_check_session
#---------------------------------------------------------------------------------
# Delete specified trait in given trial.
# If this is a local trait, it will be completely removed, along with
# all other records that refer to it.
# If this is a system trait, then the trait itself is not deleted, but
# all references to it within the specified trial are removed.
#
def urlTraitDelete(sess, trialId, traitId):
    if not sess.adminRights() or projectName != sess.getProjectName():
        return fpUtil.badJuju(sess, 'No admin rights')

    trl = models.getTrial(sess.db(), trialId)
    # Delete the trait:
    trl.deleteTrait(traitId)
    # This will probably be called by ajax, so should return json status.
    return dp.dataPage(sess, '', 'Trial Deleted', trialId=trialId)

    errmsg = fpsys.deleteUser(sess.getProjectName(), ident)
    if errmsg is not None:
        return jsonify({"error":errmsg})
    else:
        return jsonify({"status":"good"})

def _jsonErrorReturn(error=None):
#-----------------------------------------------------------------------
# Close the session and return the message. Intended as a return for a HTTP request
# after something bad (and possibly suspicious) has happened.
# MFK Only used in urlLogin, should be jsonErrorReturn instead probably, if this
# is used.
    message = {
            'error': 'An error occurred: ' + error
    }
    resp = jsonify(message)
    #resp.status_code = 500
    return resp


@webRest.route('/restapi/login', methods=["POST"])
def urlLogin():
#-----------------------------------------------------------------------
# Authenticate and get session token for api.
# The request should contain parameters "username" and "password".
#
# Note the use of sessions. On login, a server side session is established (state is stored
# in the file system), and the id of this session is sent back to the browser as a token,
# which should be sent back with each subsequent request.
#
# Every access via the various app.routes above, should go through decorator dec_check_session
# which will check there is a valid session current. If not, eg due to timeout, then it redirects
# to the login screen.
#
#
    error = ""
    if request.method != 'POST':
        return _jsonErrorReturn('non post non expected')  # This shouldn't happen.

    username = request.form.get('username')
    password = request.form.get('password')
    if not username:
        return _jsonErrorReturn('No username')
    elif not password:
        return _jsonErrorReturn('No password')

    # Try fieldprime login, then ***REMOVED***:
    # If it is a known user then what mysql user and password should we use?
    # We should store the ***REMOVED*** user name in the session in case needed for any metadata,
    # Or at least log their login.
    #
    # MFK we shouldn't need to store password if we switch to using system password.
    # even for project accounts. The password is checked here and used to make the
    # timestamped cookie.
    #
    project = None    # For either login type we need to set a project
    access = None
    dbname = None
    loginType = None
    if fpsys.systemPasswordCheck(username, password):
        project = username
        access = websess.PROJECT_ACCESS_ALL
        dbname = models.dbName4Project(project)
        loginType = LOGIN_TYPE_SYSTEM
    elif fpsys.***REMOVED***PasswordCheck(username, password):  # Not a main project account, try as ***REMOVED*** user.
        # For ***REMOVED*** check, we should perhaps first check in a system database
        # as to whether the user is known to us. If not, no point checking ***REMOVED*** credentials.
        #
        # OK, valid ***REMOVED*** user. Find project they have access to:
        loginType = LOGIN_TYPE_***REMOVED***
        project = access = dbname = None
    else:
        util.fpLog(current_app, 'Login failed attempt for user {0}'.format(username))
        return _jsonErrorReturn('invalid username/password')
        error = 'Invalid Password'

    # Create session and return token (session id):
    util.fpLog(current_app, 'Login from user {0}'.format(username))
    sess = websess.WebSess(sessFileDir=current_app.config['SESS_FILE_DIR'])  # Create session object
    sess.resetLastUseTime()
    sess.setUserIdent(username)
    sess.setProject(project, dbname, access)
    sess.setLoginType(loginType)
    return jsonify({'token':sess.sid()})

def checkIdent(candidate):
    re.match('\w\w*')
    
#@webRest.route(API_PREFIX + 'XXXprojects', methods=['POST'])
@basic_auth.login_required
def createProject2():
# Expects JSON object:
#   parent : url for parent project. If missing root is used.
#   name : project name, must be nice
#   contactName :
#   contactEmail :
#
    # top level dir called 'projects'? 'users'
    parentUrl = request.json.get('parent')
    parentProj = models.Project.getByUrl(parentUrl);
    # get project
    name = request.json.get('name')
    parentProj.getByName(name)
    name = checkIdent(name) # check name is valid
    # and doesn't already exist
    if parent is None or name is None:
        abort(HTTP_BAD_REQUEST)    # missing arguments
    # Need check user has permission. Need parent project, or path perhaps: /fp/projects/foo/bar
    # create the project:
    proj = models.Project();
