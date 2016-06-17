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

from flask import Blueprint, current_app, request, Response, jsonify, g, url_for
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_swagger import swagger
from functools import wraps
import simplejson as json
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

import fp_common.models as models
import fp_common.fpsys as fpsys
from fp_common.const import LOGIN_TIMEOUT, LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL
import fpUtil
import fp_common.util as util
from const import *
import fp_common.const as const
from fp_common.fpsys import FPSysException
from flask.helpers import make_response

### Initialization: ######################################################################
webRest = Blueprint('webRest', __name__)

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('fptoken')
multi_auth = MultiAuth(basic_auth, token_auth)

def mkdbg(msg):
    if True:
        print "webRest:" + msg

@webRest.route("/specs")
def spec():
    swag = swagger(current_app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "FieldPrime REST API"
    swag['schemes'] = ['https']
#    swag['basePath'] = '/fpv1'
    swag['host'] = '***REMOVED***'
    swag['security'] = [{"api_key":[], 'basic':[]}]
    swag['consumes'] = ['application/json']
    swag['produces'] = ['application/json']
    defs = swag['definitions']
    defs['Error'] = {
          'properties': {'error':{"description":"Description of error.", 'type':'string'}}
        }
    swag['responses'] = {
        'Unauthorized': {
            "description": "Insufficient access rights for this resource/operation.",
            "schema": {"$ref": "#/definitions/Error"}
        },
        'BadRequest': {
            "description": "Invalid parameters, or server error.",
            "schema": {"$ref": "#/definitions/Error"}
        },
        'ServerError': {
            "description": "Unexpected error on the server.",
            "schema": {"$ref": "#/definitions/Error"}
        }
    }
#     swag['securityDefinitions'] = {
#             "api_key": {
#                         "type": "apiKey",
#                         "name": "api_key",
#                         "in": "header"
#                         }                       
#         }
    
    resp = make_response(jsonify(swag))
    resp.headers['Access-Control-Allow-Origin'] = '*'   # Needed for testing, maybe not eventually..
    return resp

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
def notImplemented():
    return apiResponse(False, HTTP_SERVER_ERROR, "Not implemented yet")
def errorAccess(msg=None):
    return apiResponse(False, HTTP_UNAUTHORIZED,
                       "No access for requested operation" if msg is None else msg)
def errorServer(msg=None):
    errmsg = 'Unexpected error'
    if msg is not None:
        errmsg = errmsg + ': ' + msg
    return apiResponse(False, HTTP_SERVER_ERROR, errmsg)
def errorBadRequest(msg=None):
    return apiResponse(False, HTTP_BAD_REQUEST, "Bad request" if msg is None else msg)

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

### Authentication Checking: #############################################################

def generate_auth_token(username, expiration=600):
# Return a token for the specified username. This can be used
# to authenticate as the user, for the specified expiration
# time (which is in seconds).
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    token = s.dumps({'id': username})
    mkdbg('generate_auth_token: {}, {}'.format(username, token))
    return token

def verify_auth_token(token):
# MFK need to pass back expired indication somehow
# 440 is the login timeout status.
# Not working for project selector timeout
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

@token_auth.error_handler
def auth_error():
    return errorAccess('session expired')

@basic_auth.verify_password
def verify_password(user, password):
# Password check.
# This is invoked by the basic_auth.login_required decorator.
# If verification is successful:
#    g.userName is set to the user login
#    g.newToken is set to a new authentication token
#
    mkdbg('in verify_password {} {}'.format(user, password))
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
# Note parameter is retrieved from Authorization header field, and if there we should use it.
# But in the absence, we look in cookie (and then perhaps in json?).
# NB - it turns out this function is not called in the absence of Authorization header.
# So the cookie functionality is useful only in that it allows you to
# add a dummy token value in the www-authenticate header, under the assumption
# that you're passing a cooky with the correct value in it.
    mkdbg('verify_token({})'.format(token))
    #print 'headers: {}'.format(request.headers)
    user = verify_auth_token(token)
    if not user: # Try with cooky
        ctoken = request.cookies.get(NAME_COOKIE_TOKEN)
        mkdbg('verify_token  cooky {}'.format(str(ctoken)))
        if ctoken is not None:
            user = verify_auth_token(ctoken)
        if not user:
            mkdbg('verify_token: not user')
            return False
    # Reset token
    g.newToken = generate_auth_token(user)
    mkdbg('verify_token newToken: {} {}'.format(g.newToken, user))
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
        mkdbg('json {} form {}'.format('None' if request.json is None else 'NOT None',
                                       'None' if request.form is None else 'NOT None'))
        if request.json is None and request.form is not None:
            params = request.values
        elif request.json is not None: # and request.form is None:   Note if both json and form, we use json only
            params = request.json
        else:
            return errorBadRequest('Missing parameters')

        if 'projId' in kwargs:
            # Check permissions and get UserProject object:
            try:
                up = fpsys.UserProject.getUserProject(g.userName, kwargs['projId'])
            except fpsys.FPSysException as fpse:
                return errorServer('Unexpected error: {}'.format(fpse))
            if up is None:
                return errorAccess('No access for user {} to project'.format(g.userName))
            if isinstance(up, basestring):
                return errorBadRequest('Unexpected error: {}'.format(up))
            g.userProject = up

        ret = func(g.userName, params, *args, **kwargs)
        ret.set_cookie(NAME_COOKIE_TOKEN, g.newToken)
        return ret
    return inner

def project_func(projIdParamName='projId', trialIdParamName=None):
#-------------------------------------------------------------------------------------------------
# Decorator used for requests identifying a specific project, via url parameter with name
# projIdParamName. Various information about the project, and calling user, are retrieved and
# either stored in globals or passed to the decorated function (henceforth func).
#
# Gets parameters dictionary from request (assumed to be in context). This can be from json, or
# from form if json is not present. This param dictionary, is passed to the decorated function.
#
# Resets token cookie, with g.newToken, assumed to be set (perhaps we should be doing that here).
#
# NB: The decorated function should return a response, and should have first params:
# modelProj, params. Flask global request is assumed to be available.
# If the authenticated user is not omnipotent, and does not have at least read access to the
# project, then an authentication error is returned.
#
# If the function is called (as opposed to being not even called due to errors), then the
# following globals are set:
# g.sysProj = fpsys Project instance
# g.dbsess = models db session
# g.modelProj = models Project instance
# g.userProjectPermissions = fpsys.UserProjectPermissions instance, where user is calling
#    user, and this is None if no fpsys userProject record.
# g.canAdmin = boolean indicating user is either omnipotent or has admin access to project.
#
    def theDecorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            mkdbg('json {} form {}'.format('None' if request.json is None else 'NOT None',
                                           'None' if request.form is None else 'NOT None'))
            if request.json is None and request.form is not None:
                params = request.values
            elif request.json is not None: # and request.form is None:   Note if both json and form, we use json only
                params = request.json
            else:
                return errorBadRequest('Missing parameters')

            if projIdParamName is None or projIdParamName not in kwargs:
                return errorServer()

            pid = kwargs[projIdParamName]

            # If calling user has access to specified project, get the fpsys project,
            # model db session, and the model project for passing to func.

            # Get sys project:
            sysProj = fpsys.Project.getById(pid) # get fpsys project
            if sysProj is None:
                return errorBadRequest('Specified project not found')

            # Check access:
            try:
                perms = sysProj.getUserPermissions(g.userName)
            except fpsys.FPSysException as fpse:
                return errorServer(fpse)
            if perms is None and not g.user.omnipotent():
                return errorAccess()

            # get model db session and project:
            dbsess = sysProj.db()
            modelProj = models.Project.getById(dbsess, pid)# get model project
            if modelProj is None:
                return errorBadRequest('Specified project not found')

            # Setup globals
            g.sysProj = sysProj
            g.dbsess = dbsess
            g.modelProj = modelProj
            g.userProjectPermissions = perms
            g.canAdmin = g.user.omnipotent() or perms.hasAdminRights()
            if trialIdParamName is not None:
                trialId = kwargs.get(trialIdParamName)
                if trialId is None: return errorBadRequest('Specified trial not found')
                trial = g.modelProj.getTrialById(trialId)
                if trial is None: return errorBadRequest('Specified trial not found')
                else: g.trial = trial

            ret = func(modelProj, params, *args, **kwargs)
            ret.set_cookie(NAME_COOKIE_TOKEN, g.newToken)
            return ret
        return inner
    return theDecorator

### Authentication: ######################################################################

@webRest.route(API_PREFIX + 'token', methods=['GET'])
@basic_auth.login_required
def urlGetToken():
#^-----------------------------------
#: GET: API_PREFIX + 'token'
#: Returns access token for requesting user. This can be
#: used subsequently to access the API, by passing the
#: token in as a HTTP header: "Authorization: fptoken + <token>"
#: Access: Requesting user needs to exist.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: {
#:     'token': <token>
#:   }
#$
    """
Get access token for the API.
User and password must be supplied to get token. The token can be used to access the api
either Authorization header, or by cookie.
<p>An authorization header must be of the form
<code>"Authorization: fptoken &lt;token&gt;"</code>
<p>Alternatively the token can be supplied as the
cookie value for key <code>"fptoken"</code>.
---
tags:
  - Authentication
responses:
    200:
      description: Token generated
      schema:
        properties:
          data:
             properties:
               token:
                 type: string
                 description: API token
"""
    mkdbg('in urlGetToken')
    token = generate_auth_token(g.userName)
    retObj = {'token': token.decode('ascii'), 'duration': 600}
    return apiResponse(True, HTTP_OK, data=retObj) #, url=url_for('urlGetUser'))

@webRest.route(API_PREFIX + 'tokenUser', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetTokenUser(userid, params):
#^-----------------------------------
#: GET: API_PREFIX + tokenUser
#: Access: valid token.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   data:  {'userId':<user id>}
#$
    """
Get the login name of currently authenticated user.
---
tags:
  - Authentication
responses:
    200:
      description: User login name
      schema:
        properties:
          data:
             properties:
               userId:
                 type: string
                 description: User login id
"""
    mkdbg('in urlGetTokenUser')
    return apiResponse(True, HTTP_OK, data={'userId':userid})

### TraitInstance Attribute: #################################################################

def _checkTiAttributeStuff(projId, tiId):
#----------------------------------------------------------------------------------------------
# Check permissions for ti attribute ops, and that the TI is OK.
# If OK, the TI is returned, otherwise an error Response.
#
    # Check user has rights for this operation:
    if not g.canAdmin:
        return errorAccess('Requires project admin rights')

    # Check ti is in project:
    ti = models.getTraitInstance(g.dbsess, tiId)
    if ti is None:
        return errorBadRequest('invalid trait instance')
    if ti.getTrial().getProject().getId() != projId:
        return errorBadRequest('invalid trait instance for project')
    return ti

@webRest.route(API_PREFIX + 'projects/<int:projId>/ti/<int:tiId>/attribute', methods=['POST'])
@multi_auth.login_required
@project_func()
def urlCreateTiAttribute(mproj, params, projId, tiId):
#^-----------------------------------
#: POST: API_PREFIX + projects/<int:projId>/ti/<int:tiId>/attribute
#: Create attribute for the TI specified in the URL.
#: The attribute name must be present as a parameter "name".
#: Access: requesting user needs project admin permissions.
#: Input: {
#:   'name': <attribute name>,
#: }
#: Success Response:
#:   Status code: HTTP_OK
#:   msg: 'Attribute Created'
#$
    """
Create a new attribute for a trait instance.
---
tags:
  - Attributes
parameters:
    - name: tiId
      in: path
      description: FieldPrime traitInstance id
      required: true
      type: integer
    - name: projId
      in: path
      description: FieldPrime project id
      required: true
      type: integer
    - name: name
      in: body
      description: Name for Attribute
      required: true
      schema:
        properties:
          name:
            description: Attribute name
            type: string
responses:
  201:
    description: Attribute created
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    ti = _checkTiAttributeStuff(projId, tiId) # NB access checked in here
    if not isinstance(ti, models.TraitInstance):
        return ti

    # Get name proposed for attribute:
    #name = request.json.get('name')
    name = params.get('name')
    if not name:
        return errorBadRequest('invalid name')

    # Create or rename attribute for the ti:
    tiAtt = ti.getAttribute()
    if tiAtt is None:
        # Create it:
        att = ti.createAttribute(name)
        if att is None:
            return errorBadRequest('Cannot create attribute, may be invalid name')
    else:
        # Reset the name:
        tiAtt.setName(name)  # error return
        g.dbsess.commit()
    return apiResponse(True, HTTP_OK, msg="Attribute Created")

@webRest.route(API_PREFIX + 'projects/<int:projId>/ti/<int:tiId>/attribute', methods=['DELETE'])
@multi_auth.login_required
@project_func()
def urlDeleteTiAttribute(mproj, params, projId, tiId):
#----------------------------------------------------------------------------------------------
#^
#: DELETE: API_PREFIX + projects/<int:projId>/ti/<int:tiId>/attribute
#: Delete the attribute associated with the specified trait instance.
#: Note the ti itself, or the data within it are not deleted.
#: Access: requesting user needs project admin permissions.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   msg: "Attribute Deleted"
#$
    """
Delete the attribute for a trait instance.
After deletion the trait instance still exists, but is not available \
as an attribute
---
tags:
  - Attributes
parameters:
    - name: tiId
      in: path
      description: FieldPrime traitInstance id
      required: true
      type: integer
    - name: projId
      in: path
      description: FieldPrime project id
      required: true
      type: integer
responses:
  200:
    description: Attribute deleted
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    ti = _checkTiAttributeStuff(projId, tiId) # NB access checked in here
    if not isinstance(ti, models.TraitInstance):
        return ti
    errmsg = ti.deleteAttribute()
    if errmsg is not None:
        return errorServer(errmsg)
    return apiResponse(True, HTTP_OK, msg="Attribute Deleted")

### Users: ####################################################################################

@webRest.route(API_PREFIX + 'users', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateUser(userid, params):
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
    """
Create a user.
---
tags:
  - Users
parameters:
  - in: body
    name: body
    description: User object
    required: true
    schema:
      id: User
      required:
        - email
        - name
      properties:
        loginType:
          type: integer
          description: 2 for ***REMOVED*** user, 3 for FieldPrime local user.
        ident:
          type: string
          description: Login id for new user
        password:
          type: string
          description: Password for new user
        email:
          type: string
          description: Email address of new user
        fullname:
          type: string
          description: Full name of new user
responses:
  201:
    description: User Created.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlCreateUser({},{})'.format(userid, str(params)))
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER):
        return errorAccess("no user create permission")

    try:
        # check all details provided (should be infra)
        login = params.get('ident')
        loginType = params.get('loginType')
        if login is None or loginType is None:
            return errorBadRequest("login and loginType required")
        loginType = int(loginType)

        # check if user already exists
        if fpsys.User.getByLogin(login) is not None:
            return errorBadRequest("User with that login already exists")

        # create them
        if loginType == LOGIN_TYPE_LOCAL:
            password = params.get('password')
            fullname = params.get('fullname')
            email = params.get('email')
            # Validation - should be by infrastructure..
            if password is None or fullname is None:
                return errorBadRequest("password and fullname required for local user")
            if not util.isValidName(fullname):
                return errorBadRequest('Invalid user name')
            if not util.isValidPassword(password):
                return errorBadRequest('Invalid password')
            if not util.isValidEmail(email):
                return errorBadRequest("Invalid email address")
            errmsg = fpsys.addLocalUser(login, fullname, password, email)
        elif loginType == LOGIN_TYPE_***REMOVED***:
            errmsg = fpsys.add***REMOVED***User(login)
        else:
            errmsg = 'Invalid loginType'
        if errmsg is not None:
            return errorBadRequest(errmsg)
        return apiResponse(True, HTTP_CREATED, msg='User {} created'.format(login),
                url=url_for('webRest.urlGetUser', ident=login, _external=True))
    except Exception, e:
        return errorBadRequest('Problem in REST create user: ' + str(e))
    
def userPropertiesObject(user):    
    return {
            'url':url_for('webRest.urlGetUser', ident=user.getIdent()),
            'fullname':user.getName(),
            'email':user.getEmail(),
            'ident':user.getIdent()
           }
    
@webRest.route(API_PREFIX + 'users', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetUsers(mproj, params):
#^-----------------------------------
#: GET: API_PREFIX + users
#: Requesting user needs omnipotence permissions.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [
#:     {
#:       'url':<user url>,
#:       'fullname':<user name>,
#:       'email':<user email>
#:     }
#:   ]
#$
    """
Get user list.
---
tags:
  - Users
responses:
  200:
    description: User list.
    schema:
      properties:
        data:
          type: array
          items:
            schema:
              id: UserProperties
              properties:
                ident:
                  type: string
                  description: user login id
                url:
                 type: string
                 description: user URL
                fullname:
                 type: string
                 description: Full user name
                email:
                 type: string
                 description: user email address        
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    # Check permissions:
    if not g.user.omnipotent():
        return errorAccess("No permission")

    users = fpsys.User.getAll()
    if users is None:
        return errorServer('Problem getting users')
    retUsers = [userPropertiesObject(u) for u in users]
    return apiResponse(True, HTTP_OK, data=retUsers)

@webRest.route(API_PREFIX + 'users/<ident>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetUser(userid, params, ident):
    """
Get user.
---
tags:
  - Users
responses:
  200:
    description: User found.
    schema:
      type: object
      properties:
        data:
            $ref: "#/definitions/UserProperties"
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
#^-----------------------------------
#: GET: API_PREFIX + users/<ident>
#: Requesting user needs create user permissions, or to be the requested user.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   data: {
#:     'fullname':<user name>,
#:     'email':<user email>,
#:   }
#$
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_CREATE_USER) and userid != ident:
        return errorAccess("no permission to access user")

    user = fpsys.User.getByLogin(ident)
    if user is None:
        return errorBadRequest("Cannot access user")
    return apiResponse(True, HTTP_OK, data=userPropertiesObject(user))

@webRest.route(API_PREFIX + 'users/<ident>', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteUser(userid, params, ident):
    """
Delete user.
Requesting user needs create user permissions, and cannot delete self.
Use wisely - there's no going back.
---
tags:
  - Users
responses:
  200:
    description: User Deleted.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
#^---------------------------------
#: DELETE: API_PREFIX + 'users/<ident>
#: Requesting user needs create user permissions, and cannot delete self.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#$
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER) and userid != ident:
        return errorAccess("no permission to delete user")
    errmsg = fpsys.User.delete(ident)
    if errmsg is not None:
        return errorBadRequest(errmsg)  # need to distinguish server error, user not found..
    return apiResponse(True, HTTP_OK)

@webRest.route(API_PREFIX + 'users/<ident>', methods=['PUT'])
@multi_auth.login_required
@wrap_api_func
def urlUpdateUser(userid, params, ident):
    """
Update user properties.
---
tags:
  - Users
parameters:
  - in: body
    name: body
    description: User object
    required: true
    schema:
      properties:
        oldPassword:
          type: string
          description: Current password for user
        password:
          type: string
          description: New password for user
        email:
          type: string
          description: Email address of user
        fullname:
          type: string
          description: Full name of user
responses:
  200:
    description: User updated.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
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
    mkdbg('In urlUpdateUser')
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_CREATE_USER):
        if userid != ident:
            return errorAccess("no user update permission")
        oldPass = params.get('oldPassword')
        if oldPass is None or not fpsys.localPasswordCheck(ident, oldPass):
            return errorAccess("Invalid current password")

    try:
        user = fpsys.User.getByLogin(ident)
        if user is None:
            return jsonErrorReturn("user not found", HTTP_NOT_FOUND)
        if user.getLoginType() != LOGIN_TYPE_LOCAL:
            return errorAccess("Cannot update non-local users")

        password = params.get('password')
        if password is not None and util.isValidPassword(password):
            errmsg = user.setPassword(password) # should be exception
            if errmsg is not None:
                return errorBadRequest('Problem updating password: ' +  errmsg)

        fullname = params.get('fullname')
        if fullname is not None:
            user.setName(fullname)
        email = params.get('email')
        if email is not None:
            user.setEmail(email)

        if fullname is not None or email is not None:
            errmsg = user.save()
            if errmsg is not None:
                return errorBadRequest('Problem in updateUser: ' +  errmsg)
        return apiResponse(True, HTTP_OK)
    except Exception, e:
        return errorBadRequest('Problem in updateUser: ' + str(e))


### Projects: ############################################################################

@webRest.route(API_PREFIX + 'projects', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetProjects(userid, params):
# MFK maybe restrict contact details to admin?
#^-----------------------------------
#: GET: API_PREFIX + projects
#: Gets projects accessible to calling user.
#: If parameter all is sent, all projects are shown - if the requesting user is omnipotent.
#: Input: {
#:   'all':<any value>
#: }
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
    """
Get project list.
---
tags:
  - Projects
parameters:
  - in: body
    name: All
    description: If this flag is present, and the user is omnipotent, then all projects are returned.
    schema:
      type: object
      properties:
        all:
          type: string
          description: |
              If this flag is present, and the user is omnipotent, then all projects are returned.
              Otherwise only the projects to which the calling user has view access are returned.
responses:
  200:
    description: Project list.
    schema:
      properties:
        data:
          description: List of projects
          type: array
          items:
              properties:
                url:
                  type: string
                  description: Project URL
                projectName:
                  type: string
                  description: Project name     
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlGetProjects')
    all = params.get('all') is not None
    if all and not g.user.omnipotent():
        return errorAccess('No permission to get all projects')

    if not all:
        (plist, errmsg) = fpsys.getUserProjects(g.userName)
        if errmsg:
            return errorBadRequest(errmsg)
        retProjects = [{'projectName':p.getProjectName(),
                        'url':url_for('webRest.urlGetProject', projId=p.getProjectId())
                        } for p in plist]
    else:
        try:
            plist = fpsys.Project.getAllProjects()
        except FPSysException as e:
            return errorServer("Unexpected error getting projects: {}".format(e))
        retProjects = [{'projectName':p.getName(),
                        'url':url_for('webRest.urlGetProject', projId=p.getId(), _external=True)
                        } for p in plist]
    return apiResponse(True, HTTP_OK, data=retProjects)

def responseProjectObject(proj):
    projId = proj.getId()
    return {
        'projectName':proj.getName(),
        'urlTrials' : url_for('webRest.urlCreateTrial', projId=projId, _external=True),
        'urlUsers' : url_for('webRest.urlAddProjectUser', projId=projId, _external=True),
        'urlTraits' : url_for('webRest.urlGetTraits', projId=projId, _external=True)
    }
@webRest.route(API_PREFIX + 'projects/<int:projId>', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetProject(mproj, params, projId):
#^-----------------------------------
#: GET: API_PREFIX + projects/<projId>
#: Get project - which must be accessible to calling user.
#: Input: none
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [
#:     {
#:       'projectName':<Project Name>,
#:       'urlTrials': <url for trials within project>
#:       'urlUsers': <url for users within project>
#:     }
#:   ]
#$
    """
Get project.
Requesting user needs project view permissions.
---
tags:
  - Projects
responses:
  200:
    description: Project found.
    schema:
      type: object
      properties:
        data:
          schema:
            id: ProjectDetails
            properties:
              projectName:
                type: string
                description: Project name
              urlTrials:
                type: string
                description: URL for accessing project trials
              urlUsers :
                type: string
                description: URL for accessing project users
              urlTraits :
                type: string
                description: URL for accessing project traits
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('in urlGetProject')
    ret = responseProjectObject(mproj)
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
#: Access: Requesting user needs create omnipotent permissions.
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
#:   data: <project object - same as for urlGetProject>
#$
    """
Create a project.
Requesting user must have omnipotence.
---
tags:
  - Projects
parameters:
  - in: body
    name: Project Creation
    description: Project creation data
    required: true
    schema:
      type: object
      properties:
        projectName:
          type: string
          description: Project name
        contactName:
          type: string
          description: Name of contact person for project
        contactEmail:
          type: string
          description: Email address of contact person for project
        adminLogin:
          type: string
          description: Login id of administrator for project
responses:
  201:
    description: Project Created.
    schema:
      properties:
        data:
          $ref: "#/definitions/ProjectDetails"
        success:
          type: string
          description: Informative phrase
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('in urlCreateProject')
    # Check permissions:
    if not g.user.hasPermission(fpsys.User.PERMISSION_OMNIPOTENCE):
        return errorAccess("No permission for project creation")
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
            mkdbg('adminUser not found')
            return errorBadRequest("Unknown admin user ({}) does not exist".format(adminLogin))

        # Create the project:
        proj = models.Project.makeNewProject(projectName, ownDatabase, contactName, contactEmail, adminLogin)

        # Add the adminUser to the project:
        errmsg = fpsys.addUserToProject(adminUser.getId(), projectName, 1)  #MFK define and use constant
        if errmsg is not None:
            return errorBadRequest('project {} created, but could not add user {} ({})'.format(projectName,
                adminLogin, errmsg))
    except Exception, e:
        return errorBadRequest('Problem creating project: ' + str(e))

    return apiResponse(True, HTTP_CREATED, msg='Project {} created'.format(projectName),
                url=url_for('webRest.urlGetProject', projId=proj.getId(), _external=True),
                data=responseProjectObject(proj))

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

@webRest.route(API_PREFIX + 'projects/<int:projId>', methods=['PUT'])
@multi_auth.login_required
@project_func()
def urlUpdateProject(mproj, params, projId):
#^-----------------------------------
#: PUT: API_PREFIX + projects/<ident>
#: Access: Requesting user needs omnipotence, or to have admin access to the project.
#: Input: {
#:   'projectName': <Project name>,
#:   'contactName': <Name of contact person>,
#:   'contactEmail': <email of contact person>,
#: }
#: Success Response:
#:   Status code: HTTP_OK
#$
    """
Update project properties.
Requesting user needs to have admin access to the project, or omnipotence.
---
tags:
  - Projects
parameters:
  - in: body
    name: Project update
    description: Project details
    required: true
    schema:
      type: object
      properties:
        projectName:
          type: string
          description: Project name
        contactName:
          type: string
          description: Name of contact person for project
        contactEmail:
          type: string
          description: Email address of contact person for project
responses:
  200:
    description: Project updated.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    if not g.canAdmin:
        return errorAccess()
    try:
        # Check permissions:
        pxo = getCheckProjectsParams(params)
    except Exception, e:
        return errorBadRequest('Problem project update: ' + str(e))

    # now update stuff:
    # Need to update name in both fpsys and project database.
    # Other details in project database.

    if pxo['projectName'] is not None:
        g.sysProj.setName(pxo['projectName'])
        errmsg = g.sysProj.saveName()
        if errmsg is not None:
            return errorServer(errmsg)
        mproj.setName(pxo['projectName'])
    if pxo['contactName'] is not None:
        mproj.setContactName(pxo['contactName'])
    if pxo['contactEmail'] is not None:
        mproj.setContactEmail(pxo['contactEmail'])

    mproj.save()  # check worked..
    return apiResponse(True, HTTP_OK)

@webRest.route(API_PREFIX + 'projects/<int:projId>', methods=['DELETE'])
@multi_auth.login_required
@project_func()
def urlDeleteProject(mproj, params, projId):
    """
Delete project.
Requesting user needs create project permissions.
---
tags:
  - Projects
responses:
  200:
    description: Project Deleted.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    # check permissions
    if not g.user.omnipotent():
        return errorAccess("no permission to delete project")
    errmsg = fpsys.Project.delete(projId)
    if errmsg is not None:
        return errorBadRequest(errmsg)  # need to distinguish server error, user not found..
    return apiResponse(True, HTTP_OK)


### Project Users: #######################################################################

@webRest.route(API_PREFIX + 'projects/<int:projId>/users', methods=['POST'])
@multi_auth.login_required
@project_func()
def urlAddProjectUser(mproj, params, projId):
#----------------------------------------------------------------------------------------------
#^
#: POST: urlUsers from project
#: Requesting user needs omnipotence permissions or admin access to project.
#: NB can be used to update user permissions for the project.
#: Input: {
#:   "ident":<ident>,
#:   "admin":<boolean>
#: }
#: Success Response:
#:   Status code: HTTP_CREATED
#$
    """
Add user to project.
Requesting user must have admin access to project.
Can be used to add multiple users, if parameter "users" is present,
or a single user, if "ident" and "admin" are present. Or both.
---
tags:
  - Projects
parameters:
  - in: body
    name: Project Creation
    description: Project creation data
    required: true
    schema:
      id: ProjectUser
      type: object
      properties:
        ident:
          type: string
          description: Login id of user
        admin:
          type: boolean
          description: Does user have admin access to project.
        users:
          type: array
          description: List of users to add to project.
          items:
            type: object
            properties:
              ident:
                type: string
                description: Login id of user
              admin:
                type: boolean
                description: Does user have admin access to project.
responses:
  201:
    description: User added.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlAddProjectUser({},{})'.format(params, projId))
    # check permissions
    if not g.canAdmin:
        return errorAccess()

    def processSingleUser(ident, admin):
    # Return error return if bad, else None
        # check user exists:
        user = fpsys.User.getByLogin(ident)
        if user is None:
            return errorBadRequest("Unknown user ({}) does not exist".format(ident))
    
        # Add the adminUser to the project:
        mkdbg('calling addOrUpdateUserProjectById({},{},{})'.format(user.getId(), projId, 1 if admin else 0))
        errmsg = fpsys.addOrUpdateUserProjectById(user.getId(), projId, 1 if admin else 0)
        if errmsg is not None:
            return errorBadRequest(errmsg)
        return None
    
    try:
        # Process array of users:
        users = params.get('users')
        if users is not None:
            if not isinstance(users, list):
                return errorBadRequest("users parameter must be a list")
            for user in users:
                ident = user.get('ident')
                admin = user.get('admin')
                ret = processSingleUser(ident, admin)
                if ret is not None:
                    return ret
        
        # Process single user
        ident = params.get('ident')
        if ident is not None:
            admin = params.get('admin')       
            ret = processSingleUser(ident, admin)
            if ret is not None:
                return ret
    except Exception as e:
        mkdbg('EXCEPTION in urlAddProjectUser: {}'.format(str(e)))
        return errorBadRequest('Invalid input')

    return apiResponse(True, HTTP_CREATED)

@webRest.route(API_PREFIX + 'projects/<int:projId>/users', methods=['GET'])
@multi_auth.login_required
@project_func('projId')
def urlGetProjectUsers(mProj, params, projId):
#----------------------------------------------------------------------------------------------
#^
#: GET: urlUsers from project
#: Access: Requesting user needs omnipotence permissions or admin access to project.
#: NB can be used to update user permissions for the project.
#: Input: {
#: }
#: Success Response:
#:   Status code: HTTP_OK
#:   data: array of {'ident':<ident>, 'admin':boolean}
#$
    """
Get list of project users.
Requesting user must have admin access to project.
---
tags:
  - Projects
responses:
  200:
    description: Trial Created.
    schema:
      type: object
      properties:
        data:
            type: array
            items:
              type: object
              properties:
                url:
                  type: string
                  description: URL for user in project
                name:
                  type: string
                  description: Name of user
                ident:
                  type: string
                  description: Login id of user
                admin':
                  type: boolean
                  description: Does user have admin access to project
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlGetProjectUsers({})'.format(projId))
    # check permissions
    if not g.canAdmin:
        return errorAccess()

    try:
        users = g.sysProj.getUsers()
    except FPSysException as e:
        return errorServer('urlGetProjectUsers: ' + e)
    retList = [{'url':url_for('webRest.urlDeleteProjectUser', projId=projId, userId=userId),
                'ident':ident,
                'admin':perms==1,
                'name':name
                } for (ident,perms,name,userId) in users]
    mkdbg('user list {}'.format(retList))
    return apiResponse(True, HTTP_OK, data=retList)

@webRest.route(API_PREFIX + 'projects/<int:projId>/users/<int:userId>', methods=['DELETE'])
@multi_auth.login_required
@project_func('projId')
def urlDeleteProjectUser(mProj, params, userId, projId):
#def urlDeleteProjectUser(userId, projId):
#----------------------------------------------------------------------------------------------
#^
#: DELETE: urlProjectUser from getProjectUsers
#: Access: Requesting user needs omnipotence permissions or admin access to project.
#: NB can be used to update user permissions for the project.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#$
    """
Remove user from project.
Requesting user must have admin access to project.
---
tags:
  - Projects
responses:
  200:
    description: Remove project user.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlDeleteProjectUser({})'.format(projId))

    # check permissions
    if not g.canAdmin:
        return errorAccess()
    try:
        g.sysProj.removeUser(userId)
    except FPSysException as e:
        return errorServer('urlDeleteProjectUser: ' + str(e))
    return apiResponse(True, HTTP_OK, msg='User removed from project')


#### Traits: ##########################################################################

@webRest.route(API_PREFIX + 'projects/<int:projId>/traits', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetTraits(mproj, params, projId):
#---------------------------------------------------------------------------------
#^
#: GET: urlTraits from project
#: Access: Omnipotence or project admin access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [ {
#:     name : <name>
#:     description : <description>
#:     datatype : <'integer' | 'decimal' | 'text' | 'categorical' | 'date' | 'photo'>
#:     url : <trait URL>
#:   ]
#$
    """
Get project trait list.
---
tags:
  - Traits
responses:
  200:
    description: Project list.
    schema:
      properties:
        data:
          type: array
          items:
            schema:
              id: Trait
              properties:
                url:
                 type: string
                 description: Trait URL
                name:
                 type: string
                 description: Trait name
                description:
                 type: string
                 description: Trait description
                datatype:
                 type: string
                 description: Must be one of integer, decimal, text, categorical, date, photo
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlGetTraits({})'.format(projId))
    # check permissions
    if not g.canAdmin:
        return errorAccess()
    try:
        straits = mproj.getTraits()
        retList = [{
                    'name':trt.getName(),
                    'description':trt.getDescription(), 
                    'datatype':trt.getDatatypeName(),
                    'url':url_for('urlGetTrait', projId=projId, traitId=trt.getId(),
                                  _external=True)
                    } for trt in straits]
    except Exception as e:
        return errorBadRequest('Problem getting traits: ' + str(e))
    return apiResponse(True, HTTP_OK, data=retList)

@webRest.route(API_PREFIX + 'projects/<int:projId>/traits', methods=['POST'])
@multi_auth.login_required
@project_func()
def urlCreateTrait(mproj, params, projId):
#^-----------------------------------
#: POST: urlTraits from project
#: Access: Requesting user needs create omnipotent permissions.
#: Input: {
#:   'name': <name>,
#:   'description': <description>,
#:   'datatype': <name of datatype>,
#:   'typeData': [..{caption:<category name, value:<category value>}..]
#: }
#: Success Response:
#:   Status code: HTTP_CREATED
#:   url: <url of created trait>
#:   data: none
#$
    """
Create a trait.
Requesting user needs project admin permissions.
---
tags:
  - Traits
parameters:
  - in: body
    name: Project Trait Creation
    description: Trait creation data
    required: true
    schema:
      required:
        - properties
      type: object
      properties:
        name:
          type: string
          description: Trait name
        description:
          type: string
          description: Description of trait.
        datatype:
         type: string
         description: Must be one of integer, decimal, text, categorical, date, photo
#          $ref: '#/definitions/ScoreDatatype'
        typeData:
          type: object
responses:
  201:
    description: Trait Created.
    schema:
      properties:
        success:
          type: string
          description: Informative phrase
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('in urlCreateTrait')
    # check permissions
    if not g.canAdmin:
        return errorAccess()
    try:
        # todo parameter checks, perhaps, checks are done in makeNewProject
        name = params.get('name')
        description = params.get('description')
        datatype = params.get('datatype')
        typeData = params.get('typeData')
        if typeData is not None and type(typeData) != dict:
            return errorBadRequest('invalid typeData')      
        trt = mproj.newTrait(name, description, datatype, typeData)
    except Exception, e:
        return errorBadRequest('Problem creating trait: ' + str(e))

    return apiResponse(True, HTTP_CREATED, msg='Trait {} created'.format(name),
                url=url_for('webRest.urlGetTrait', projId=projId,
                            traitId=trt.getId(), _external=True))
    
@webRest.route(API_PREFIX + 'projects/<int:projId>/traits/<int:traitId>', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetTrait(mproj, params, projId, traitId):
#---------------------------------------------------------------------------------
#^
#: GET: trait url from getTraits
#: Access: Omnipotence or project view access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [ {
#:     name : <name>
#:     description : <description>
#:     datatype : <'integer' | 'decimal' | 'text' | 'categorical' | 'date' | 'photo'>
#:   ]
#$
    """
Get project trait.
---
tags:
  - Traits
responses:
  200:
    description: Trait details.
    schema:
      properties:
        data:
          $ref: '#/definitions/Trait'
#           type: object
#           properties:
#             url:
#              type: string
#              description: Trait URL
#             name:
#              type: string
#              description: Trait name
#             description:
#              type: string
#              description: Trait description
#             datatype:
#              $ref: '#/definitions/ScoreDatatype'
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlGetTrait({})'.format(projId))
    try:
        trt = mproj.getTrait(traitId)
        retObj = {
                    'name':trt.getName(),
                    'description':trt.getDescription(), 
                    'datatype':trt.getDatatypeName(),
                    'url':url_for('urlGetTrait', projId=projId, traitId=trt.getId(),
                                  _external=True)
                    }
    except Exception as e:
        return errorBadRequest('Problem getting trait: ' + str(e))
    return apiResponse(True, HTTP_OK, data=retObj)

@webRest.route(API_PREFIX + 'projects/<int:projId>/traits/<int:traitId>', methods=['DELETE'])
@multi_auth.login_required
@project_func()
def urlDeleteTrait(mproj, params, projId, traitId):
#---------------------------------------------------------------------------------
#^
#: DELETE: urlTraits from project
#: Access: Omnipotence or project view access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: none
#$
    """
Delete trait.
Requesting user needs project view permissions.
---
tags:
  - Traits
responses:
  200:
    description: Trait Deleted.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlDeleteTrait({})'.format(projId))
    return notImplemented()
    try:
        mproj.deleteTrait(traitId)
    except Exception as e:
        return errorBadRequest('Problem deleting trait: ' + str(e))
    return apiResponse(True, HTTP_OK)

## Trials: ############################################################################

def processAttributes(trial, attributes):
# Adds attributes to trial.
# NB passes models exception through.
    for att in attributes:
        # Create attribute
        try:
            natt = trial.createAttribute(att)
            g.dbsess.add(natt)
        except models.DalError:
            raise
    return None

def processNodes(trial, nodes):
# Adds nodes to trial.
# NB passes models exception through.
    for node in nodes:
        try:
            mnode = trial.createNode(node)
        except models.DalError:
            raise
    return None

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials', methods=['POST'])
@multi_auth.login_required
@project_func()
def urlCreateTrial(mproj, params, projId):
#^-----------------------------------
#: POST: <trialUrl from getProject>
#: Access: Requesting user needs project admin permissions.
#: Input: {
#:   properties : {
#:     name : name project - must be appropriate.
#:     year : text
#:     site : text
#:     acronym : text
#:     nodeCreation : 'true' or 'false'
#:     index1name : text
#:     index2name : text
#:   }
#:   attributes : array of {
#:     name : <attribute name>,
#:     datatype : OPTIONAL 'text' | 'decimal' | 'integer'
#:   }
#:   nodes : array of {
#:     attributeName : attributeValue
#:   }
#: }
#: NB, all input parameters are optional except for trialName.
#: Success Response:
#:   Status code: HTTP_CREATED
#:   url: <url of created trial>
#$
    """
Create a trial.
Requesting user needs project admin permissions.
---
tags:
  - Trials
definitions:
  - schema:
              type: object
              id: TrialProperties
              required:
                - name
              description: Trial properties
              properties:
                name:
                  type: string
                  description: Name for trial
                year:
                  type: integer
                  description: Trial year
                site:
                  type: integer
                  description: Trial site
                acronym:
                  type: integer
                  description: Trial acronym
                nodeCreation:
                  type: string
                  description: Indicates whether user node creation allowed for trial
                index1name:
                  type: string
                  description: Name of first index for trial
                index2name:
                  type: string
                  description: Name of second index for trial
parameters:
  - in: body
    name: Trial Creation
    description: Trial creation data
    required: true
    schema:
      required:
        - properties
      properties:
        properties:
            $ref: "#/definitions/TrialProperties"
#               type: object
#               id: TrialProperties
#               required:
#                 - name
#               description: Trial properties
#               properties:
#                 name:
#                   type: string
#                   description: Name for trial
#                 year:
#                   type: integer
#                   description: Trial year
#                 site:
#                   type: integer
#                   description: Trial site
#                 acronym:
#                   type: integer
#                   description: Trial acronym
#                 nodeCreation:
#                   type: string
#                   description: Indicates whether user node creation allowed for trial
#                 index1name:
#                   type: string
#                   description: Name of first index for trial
#                 index2name:
#                   type: string
#                   description: Name of second index for trial
        attributes:
          type: array
          items:
            description: Attribute details
            type: object
            properties:
                name:
                  type: string
                  description: Attribute name
                datatype:
#                  id: datatype
                  type: string
                  description: Must be 'text', 'decimal', or 'integer'
        nodes:
          type: array
          items:
            description: Node details
            type: object
            properties:
                attributeName:
                  type: string
                  description: Attribute Value
responses:
  201:
    description: Trial Created.
    schema:
      properties:
        success:
          type: string
          description: Informative phrase
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    # Check permissions:
    # Calling user must be omnipotent or have admin access to project.
    # We should have trial creation permissions, but this should be project specific
    # preferably with inheritance.
    mkdbg('urlCreateTrial({})'.format(projId))
    if not g.canAdmin:
        return errorAccess()

    properties = params.get('properties')
    if properties is None:
        return errorBadRequest('missing properties parameter')
    trialName = properties.get('name')
    trialYear = properties.get('year')
    trialSite = properties.get('site')
    trialAcronym = properties.get('acronym')    
    index1 = properties.get('index1name')
    index2 = properties.get('index2name')
    
    attributes = params.get('attributes')
    nodes = params.get('nodes')

    # check trial name provided and valid format:
    if trialName is None or not util.isValidIdentifier(trialName):
        return errorBadRequest("Invalid trial name")

    try:
        trial = mproj.newTrial(trialName, trialSite, trialYear, trialAcronym)  #MFK this func doing commits.
        nodeCreation = properties.get('nodeCreation')
        if nodeCreation is not None:
            if nodeCreation not in ('true', 'false'):
                raise Exception('nodeCreation must be "true" or "false"') 
            trial.setTrialPropertyBoolean('nodeCreation', nodeCreation=='true')
        trial.setNavIndexNames(index1, index2)

        # process attributes:
        if attributes is not None:
            processAttributes(trial, attributes)

        # process nodes:
        if nodes is not None:
            processNodes(trial, nodes)

        # commit
        g.dbsess.commit()
    except Exception as e:
        g.dbsess.rollback()
        return errorBadRequest("Error creating trial: {}".format(e.__str__()))

    return apiResponse(True, HTTP_CREATED, msg='Trial {} created'.format(trialName),
            url=url_for('webRest.urlGetTrial', _external=True, projId=projId, trialId=trial.getId()))

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>', methods=['PUT'])
@multi_auth.login_required
@project_func()
def urlUpdateTrial(mproj, params, projId, trialId):
    """
Update a trial.
---
tags:
  - Trials
parameters:
  - in: body
    name: Trial Creation
    description: Trial creation data
    required: true
    schema:
      type: object
      properties:
        nodeCreation:
          type: string
          description: Indicates whether user node creation allowed for trial
        index1name:
          type: string
          description: Name of first index for trial
        index2name:
          type: string
          description: Name of second index for trial
responses:
  200:
    description: Trial Updated.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlUpdateTrial {}'.format(params))
    if not g.canAdmin:
        return errorAccess()
    try:
        nodeCreation = params.get('nodeCreation')
        ind1 = params.get('index1name')
        ind2 = params.get('index2name')
        trial = models.getTrial(g.dbsess, trialId)
        if nodeCreation is not None:
            if nodeCreation not in ('true', 'false'):
                raise Exception('nodeCreation must be "true" or "false"') 
            trial.setTrialPropertyBoolean('nodeCreation', nodeCreation=='true')
        trial.setNavIndexNames(ind1, ind2)
        # commit
        g.dbsess.commit()
    except Exception as e:
        g.dbsess.rollback()
        return errorBadRequest("Error creating trial: {}".format(e.__str__()))
       
    return apiResponse(True, HTTP_OK, msg='trial updated')

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetTrials(userid, params, projId):
#^-----------------------------------
#: GET: <trialUrl from project>
#: Access: Requesting user needs omnipotence or project view permissions.
#: Input: {
#: }
#: Success Response:
#:   Status code: HTTP_OK
#:   data: <array of trial urls>
#$
    """
Get trial list.
Requesting user needs project view permissions.
---
tags:
  - Trials
responses:
  200:
    description: Got trials.
    schema:
      properties:
        data:
            type: array
            items:
              type: string
              description: Trial URL
#           schema:
#               properties:
#                 schema:
#                   $ref: "#/definitions/TrialProperties"
#               urlAttributes:
#                 type: string
#                 description: URL for accessing trial attributes
#               urlNodes :
#                 type: string
#                 description: URL for accessing trial nodes

  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    # Check access:
    if not g.user.omnipotent() and g.userProject is None:
        return errorAccess()
    # Return array of trial URLs:
    trialUrlList = [
        url_for('webRest.urlGetTrial', _external=True, projId=projId, trialId=trial.getId()) for
            trial in g.userProject.getModelProject().getTrials()]
    return apiResponse(True, HTTP_OK, data=trialUrlList)


@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>', methods=['GET'])
@multi_auth.login_required
@wrap_api_func
def urlGetTrial(userid, params, projId, trialId):
    """
Get trial.
Requesting user needs project view permissions.
---
tags:
  - Trials
responses:
  200:
    description: Trial found.
    schema:
      type: object
      properties:
        data:
          type: object
          properties:
              properties:
                  $ref: "#/definitions/TrialProperties"
              urlAttributes:
                type: string
                description: URL for accessing trial attributes
              urlNodes :
                type: string
                description: URL for accessing trial nodes
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    # check user has access to project
    trial = models.getTrial(g.userProject.db(), trialId)
    returnJson = { # perhaps we should have trial.getJson()
        'properties' : {
            "name":trial.getName(),
            "year":trial.getYear(),
            "site":trial.getSite(),
            "acronym":trial.getAcronym(),
            "nodeCreation":trial.getTrialProperty('nodeCreation'),
            "index1name":trial.navIndexName(0),
            "index2name":trial.navIndexName(1)
        },
        "urlAttributes":url_for('webRest.urlGetAttributes', _external=True,
                                projId=projId, trialId=trialId),
        "urlNodes":url_for('webRest.urlGetNodes', _external=True,
                                projId=projId, trialId=trialId)
    }
    return apiResponse(True, HTTP_OK, data=returnJson)

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>', methods=['DELETE'])
@multi_auth.login_required
@wrap_api_func
def urlDeleteTrial(userid, params, projId, trialId):
    """
Delete trial.
Requesting user needs project admin permissions.
---
tags:
  - Trials
responses:
  200:
    description: Trial Deleted.
  401:
    $ref: "#/responses/Unauthorized"
"""
    # Need project admin access to delete
    if not g.userProject.hasAdminRights():
        return errorAccess('No administration access')
    models.Trial.delete(g.userProject.db(), trialId)
    return jsonSuccessReturn("Trial Deleted", HTTP_OK)

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/traits/<int:traitId>', methods=['PUT'])
@multi_auth.login_required
@project_func(trialIdParamName='trialId')
def urlTrialProjectTrait(mproj, params, projId, trialId, traitId):
# Use this URL for adding trait to trial, or deleting? But Where do we get it from?
# NB - we probably should allow the passing in of barcode attribute (trialTrait field)
# and a type specific object.    
# parameters:
#   - in: body
#     name: Trial Creation
#     description: Trial creation data
#     required: true
#     schema:
#       type: object
#       properties:
#         trialUrl:
#           type: string
#           description: Url of trait to add to trial
    """
Add trial trait.
Add project trait to trial.
---
tags:
  - Trials
  - Traits
responses:
  200:
    description: Trait added to trial.
    schema:
      type: object
      properties:
        success:
          type: string
          description: Informative phrase
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    trial = g.trial
    trait = mproj.getTrait(traitId) # does this check trait is in project?
    if trait is None:
        return errorBadRequest('Trait not found in project')
    trial.addTrait(trait)
    g.dbsess.commit()
    return apiResponse(True, HTTP_OK, msg="Trait added to trial")

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/availableTraits', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetAvailableTrialProjectTraits(mproj, params, projId, trialId):
    pass


### Nodes: ###############################################################################

#-----------------------------------------------------------------------------------------
# nodes endpoint: urlNodes attribute from api Trial object
#   GET - get all nodes
#   POST - create new nodes

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/nodes', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetNodes(mproj, params, projId, trialId):
    """
Get node list.
User must have project view access, or omnipotence.
This URL is urlNodes from the trial object.
---
tags:
  - Nodes
responses:
  200:
    description: Node list.
    schema:
      properties:
        data:
          type: array
          items:
              properties:
                url:
                 type: string
                 description: Node URL
                fpId:
                 type: string
                 description: Attribute name
                index1:
                 type: string
                 description: Node value for index 1
                index2:
                 type: string
                 description: Node value for index 2
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
#---------------------------------------------------------------------------------
#^
#: GET: urlNodes from trial
#: Access: Omnipotence or project view access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [ {
#:     url : <url for node>
#:     fpId : <fp id>
#:     index1 : <index 1 value>
#:     index2 : <index 2 value>
#:   ]
#$
    mkdbg('in urlGetNodes')
    # NB, check that user has access to project is done in project_func.
    try:
        trial = mproj.getTrialById(trialId)
        nodes = trial.getNodes()
        data = [{
            'url':url_for('webRest.urlGetNode', _external=True, projId=projId,
                          trialId=trialId, nodeId=node.getId()),
            'fpId':node.getId(),
            'index1':node.getRow(),
            'index2':node.getCol()
            } for node in nodes]
    except Exception as e:
        return errorBadRequest(str(e))
    return apiResponse(True, HTTP_OK, data=data)

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/nodes', methods=['POST'])
@multi_auth.login_required
@project_func()
def urlCreateNode(mproj, params, projId, trialId):
#-----------------------------------------------------------------------------------------
# NB, could have complex object, including attributes, or could have everything atomic,
# and have separate access point to create attributes and add values to them.
# Or we could have both, eventually. Separately is better I think. Reduces risk of
# unintentionally create new attributes by mistyping names, and allows defining the type
# of an attribute prior to loading values.
#^-----------------------------------
#: POST: urlNodes from trial
#: Access: Omnipotence or project view access. If nodeCreation is not enabled for the
#:   trial, then project admin access is required.
#: Input JSON object:
#: { node : <node object> }
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
    """
Create a trial node.
---
tags:
  - Nodes
parameters:
  - in: body
    name: body
    description: Node object
    required: true
    schema:
      required:
        - node
      properties:
        node:
          schema:
            id: Node
            properties:
              index1:
                type: integer
                description: Value of index 1 for the node.
              index2:
                type: integer
                description: Value of index 2 for the node.
              description:
                type: string
                description: Optional node information.
              barcode:
                type: string
                description: Default barcode for navigation
              latitude:
                type: number
                description: Latitude of node location.
              longitude:
                type: number
                description: Longitude of node location.
              attributes:
                type: array
                description: Array of attribute name:attribute value objects
                items:
                  type: object
                
responses:
  201:
    description: Node Created.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('urlCreateNode : {}'.format(params))
    try:
        # Check permissions, nodeCreation needs to be on if not admin.
        trial = mproj.getTrialById(trialId)
        if not g.canAdmin and not trial.getTrialPropertyBoolean('nodeCreation'):
            return errorAccess('nodeCreation not enabled for non admin user')
        
        node = params.get('node')
        if node is None: return errorBadRequest('missing node parameter')
        #processNodes(trial, (node,))
        mnode = trial.createNode(node)
        g.dbsess.commit()
    except Exception as e:
        g.dbsess.rollback()
        return errorBadRequest("Error creating trial: {}".format(e.__str__()))
    return apiResponse(True, HTTP_CREATED, msg='Node created',
            url=url_for('webRest.urlGetNode', _external=True, projId=projId, trialId=trialId, nodeId=mnode.getId()))

#-----------------------------------------------------------------------------------------
# nodes/nodeId endpoint
#   GET
#   DELETE - delete particular node
#   PUT - update node
#
# Need to get node notes somehow

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/nodes/<int:nodeId>', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetNode(mproj, params, projId, trialId, nodeId):
#---------------------------------------------------------------------------------
#^
#: GET: node url from getNodes
#: Access: Omnipotence or project view access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: {
#:     fpId : <fp id>
#:     index1 : <index 1 value>
#:     index2 : <index 2 value>
#:   }
#$
    """
Get node.
User must have project view access, or omnipotence.
Node URLs can be obtaing from the getNodes operation.
---
tags:
  - Nodes
responses:
  200:
    description: Node.
    schema:
      properties:
        data:
              properties:
                fpId:
                 type: string
                 description: Attribute name
                index1:
                 type: string
                 description: Node value for index 1
                index2:
                 type: string
                 description: Node value for index 2
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('in urlGetNodes')
    # NB, check that user has access to project is done in project_func.
    try:
        trial = mproj.getTrialById(trialId)
        node = trial.getNode(nodeId)
        if node is None:
            return errorBadRequest('Node not found')
        data = {
            'fpId':node.getId(),
            'index1':node.getRow(),
            'index2':node.getCol()
            }
    except Exception as e:
        return errorBadRequest(str(e))
    return apiResponse(True, HTTP_OK, data=data)

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/nodes/<int:nodeId>', methods=['PUT'])
@multi_auth.login_required
@project_func()
def urlUpdateNode(mproj, params, projId, trialId, nodeId):
#---------------------------------------------------------------------------------
#^
#: PUT: node url from getNodes
#: Access: Omnipotence or admin.
#: Input: As for urlCreateNode
#: Success Response:
#:   Status code: HTTP_OK
#:   data: none
#$
    """
Update a trial node.
---
tags:
  - Nodes
parameters:
  - in: body
    name: body
    description: Node object
    required: true
    schema:
      required:
        - node
      properties:
        node:
          $ref: '#/definitions/Node'
                
responses:
  200:
    description: Node Updated.
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
    mkdbg('in urlGetNodes : {}'.format(params))
    if not g.canAdmin:
        return errorAccess('admin privileges required')
    try:
        # Check permissions, nodeCreation needs to be on if not admin.
        trial = mproj.getTrialById(trialId)        
        jnode = params.get('node')
        if jnode is None: return errorBadRequest('missing node parameter')
        mnode = trial.updateNode(jnode)
        g.dbsess.commit()
    except Exception as e:
        g.dbsess.rollback()
        return errorBadRequest("Error updating node: {}".format(e.__str__()))
    return apiResponse(True, HTTP_CREATED, msg='Node created',
            url=url_for('webRest.urlGetNode', _external=True, projId=projId, trialId=trialId, nodeId=mnode.getId()))

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/nodes/<int:nodeId>', methods=['DELETE'])
@multi_auth.login_required
@project_func()
def urlDeleteNode(mproj, params, projId, trialId, nodeId):
    """
Delete node.
Requesting user needs project admin permissions.
---
tags:
  - Nodes
responses:
  200:
    description: Node Deleted.
  401:
    $ref: "#/responses/Unauthorized"
"""
#---------------------------------------------------------------------------------
#^
#: DELETE: node url from getNodes
#: Access: Omnipotence or project admin access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: none
#$
    mkdbg('in urlDeleteNode')
    # NB, check that user has access to project is done in project_func.
    if not g.canAdmin:
        return errorAccess()
    try:
        trial = mproj.getTrialById(trialId)
        trial.deleteNode(nodeId)
        g.dbsess.commit()
    except Exception as e:
        return errorBadRequest(str(e))
    return apiResponse(True, HTTP_OK)

### Attributes: ##########################################################################

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/attributes', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlGetAttributes(mproj, params, projId, trialId):
    """
Get attribute list.
User must have project view access, or omnipotence.
This URL is urlAttributes from the trial object.
---
tags:
  - Attributes
responses:
  200:
    description: Attribute list.
    schema:
      properties:
        data:
          type: array
          items:
              properties:
                url:
                 type: string
                 description: Attribute URL
                name:
                 type: string
                 description: Attribute name
                datatype:
                 $ref: "#/definitions/datatype"
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
#---------------------------------------------------------------------------------
#^
#: GET: urlAttributes from trial
#: Access: Omnipotence or project view access.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [ {
#:     url : <url for attribute>
#:     name : <attribute Name>
#:     datatype : <'text' | 'integer' | 'decimal'>
#:   ]
#$
    mkdbg('in urlGetAttributes')
    # NB, check that user has access to project is done in project_func.
    try:
        trial = mproj.getTrialById(trialId)
        natts = trial.getAttributes()
        data = [{
            'url':url_for('webRest.urlAttributeData', _external=True, projId=projId,
                          trialId=trialId, attId=nat.getId()),
            'name':nat.getName(),
            'datatype':nat.getDatatypeText()
            } for nat in natts]
    except Exception as e:
        return errorBadRequest(str(e))
    return apiResponse(True, HTTP_OK, data=data)

@webRest.route(API_PREFIX + 'projects/<int:projId>/trials/<int:trialId>/attributes/<int:attId>', methods=['GET'])
@multi_auth.login_required
@project_func()
def urlAttributeData(mproj, params, projId, trialId, attId):
    """
Get attribute values.
User must have project view access.
The returned data property is an array of two element arrays, each
of which represents a single value of the attribute for a node.
The first element of the array is the node id, and the second
element is the value of the attribute for that node.
---
tags:
  - Attributes
responses:
  200:
    description: Attribute value list.
    schema:
      properties:
        data:
          type: array
          items:
            type: array
            items:
              - type: integer
              - type: string
  400:
    $ref: "#/responses/BadRequest"
  401:
    $ref: "#/responses/Unauthorized"
"""
#---------------------------------------------------------------------------------
#^
#: GET: API_PREFIX + /projects/<int:projId>/trials/<int:trialId>/attributes/<int:attId>
# Returns array of nodeId:attValue pairs
# These are sorted by node_id.
#: Access:Requesting user needs access to project.
#: NB can be used to update user permissions for the project.
#: Input: None
#: Success Response:
#:   Status code: HTTP_OK
#:   data: [
#:      [nodeId, attValue], ...
#:   ]
#$
#
# This is used in the admin web pages. And was designed before the main REST API,
# so may need some rethinking, eg the url.
#
    mkdbg('in urlAttributeData')
    # NB, check that user has access to project is done in wrap_api_func.
    natt = models.getAttribute(g.dbsess, attId)
    if natt is None:
        return errorBadRequest("Invalid attribute")
    vals = natt.getAttributeValues()
    data = []
    for av in vals:
        data.append([av.getNode().getId(), av.getValueAsString()])
    return apiResponse(True, HTTP_OK, data=data)


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

# add user
curl $AUTH -X POST -H "Content-Type: application/json" \
    -d '{"ident":"fpadmin", "admin":true}' $FP/projects/

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
