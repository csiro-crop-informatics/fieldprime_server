# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
# see http://blog.miguelgrinberg.com/post/restful-authentication-with-flask, or more
# recent and better, find the github page for flask_httpauth
#
# Todo - long term time out, or numUses value for token. To limit damage from stolen token.
#

from flask import Blueprint, current_app, request, Response, jsonify, g, abort
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from functools import wraps
import simplejson as json
from passlib.apps import custom_app_context as pwd_context
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
# auth = HTTPBasicAuth()
# auth = HTTPTokenAuth(scheme='token')

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('fptoken')
multi_auth = MultiAuth(basic_auth, token_auth)

def mkdbg(msg):
    #pass
    print msg

### Constants: ###########################################################################

API_PREFIX = '/fpv1/'

### Response functions: ##################################################################

def jsonErrorReturn(errmsg, statusCode):
    return Response(json.dumps({'error':errmsg}), status=statusCode, mimetype='application/json')

def jsonReturn(jo, statusCode):
    return Response(json.dumps(jo), status=statusCode, mimetype='application/json')

def jsonSuccessReturn(msg='success', statusCode=HTTP_OK):
    return jsonReturn({'success':msg}, statusCode)

def fprGetError(jsonResponse):
# Returns the error message from the response, IF there was an error, else None.
# This function intended to abstract the way we encode errors in the response,
# all users of the rest api should use this to get errors.
    if "error" in jsonResponse:
        return jsonResponse["error"]
    return None

def fprHasError(jsonResponse):
    return "error" in jsonResponse

@webRest.errorhandler(401)
def custom_401(error):
    print 'in custom_401'
    return Response('<Why access is denied string goes here...>', 401)
                    #, {'WWWAuthenticate':'Basic realm="Login Required"'})

### Authorization stuff: #################################################################

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
def verify_password(username_or_token, password):
# Password check.
# This is invoked by the basic_auth.login_required decorator.
# If verification is successful, g.user is set.
#
    # first try to authenticate by token
    mkdbg('verify_password: u:{} p:{}'.format(username_or_token, password))
    user = verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        check = fpsys.userPasswordCheck(username_or_token, password)
        if not check:
            mkdbg('verify_password: fpsys.userPasswordCheck failed')
            return False
#             g.user = 'xxxx'
#             return True
        else: user = username_or_token
    g.user = user
    g.newToken = generate_auth_token(user)
    return True

@token_auth.verify_token
def verify_token(notoken):
# Note not using parameter. Presumably this would be retrieved
# from www-authenticate header, and if it is there we should use it.
# But in the absence, we look in cookie, and then perhaps in json?
#
    mkdbg(notoken)
    token = request.cookies.get(NAME_COOKIE_TOKEN)
    if token is None: return False
    mkdbg('verify_token token: {}'.format(token))
    user = verify_auth_token(token)
    if not user:
        mkdbg('verify_token: not user')
        return False
    # Reset token
    g.newToken = generate_auth_token(user)
    mkdbg('verify_token newToken: {}'.format(g.newToken))
    g.user = user
    return True


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

##########################################################################################
### Access Points: #######################################################################
##########################################################################################

### Authentication: #################################################################

@webRest.route(API_PREFIX + 'token', methods=['GET'])
@basic_auth.login_required
def get_auth_token():
#-------------------------------------------------------------------------------------------------
# Returns, in a JSON object, a token for user.
# The returned token may be used as a basic authentication username
# for subsequent calls to the api (for up to 600 seconds).
# This is in place of repeatedly sending the real username and password.
# When using the token as the username, the password is not used, so any
# value can be given.
#
    token = generate_auth_token(g.user)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

# @webRest.route(API_PREFIX + 'otherToken/<otherUserId>', methods=['GET'])
# @basic_auth.login_required
# def get_other_auth_token(otherUserId):
# #-------------------------------------------------------------------------------------------------
# # Returns, in a JSON object, a token for user.
# # The returned token may be used as a basic authentication username
# # for subsequent calls to the api (for up to 600 seconds).
# # This is in place of repeatedly sending the real username and password.
# # When using the token as the username, the password is not used, so any
# # value can be given.
# #
#     # Check authenticated user has power to create tokens for others.
#     token = generate_auth_token(g.user, 600)
#     return jsonify({'token': token.decode('ascii'), 'duration': 600})

# @webRest.route(API_PREFIX + 'grant/<login>/<permission>', methods=['GET'])
# @basic_auth.login_required
# def authUser(login, permission):
#     pass


### TraitInstance Attribute: #################################################################
# Note authentication problem: from the web page in the browser, we won't have login token.
# Can we use the cookie? see wr_check_session.
#

def _checkTiAttributeStuff(sess, tiId):
# Check permissions for ti attribute ops. If OK, returns the ti,
# else returns error Response.
    # Check user has rights for this operation:
    if not sess.adminRights():
        return jsonErrorReturn('Requires project admin rights', HTTP_UNAUTHORIZED)
    # Check ti is in project:
    ti = models.getTraitInstance(sess.db(), tiId)
    if ti is None:
        return jsonErrorReturn('invalid trait instance', HTTP_BAD_REQUEST)
    if ti.getTrial().getProject().getId() != sess.getProject().getId():
        return jsonErrorReturn('invalid trait instance for project', HTTP_BAD_REQUEST)
    return ti

@webRest.route(API_PREFIX + 'ti/<int:tiId>/attribute', methods=['POST'])
#@basic_auth.login_required
@wr_check_session
def createTiAttribute(sess, tiId):
# Create attribute for the TI specified in the URL.
# The attribute name must be present as a url parameter "name".
#
    ti = _checkTiAttributeStuff(sess, tiId)
    if not isinstance(ti, models.TraitInstance):
        return ti

    # Get name proposed for attribute:
    name = request.json.get('name')
    if not name:
        return jsonErrorReturn('invalid name', HTTP_BAD_REQUEST)

    # check
    nodat = ti.getAttribute()
    if nodat is None:
        # Create it:
        att = ti.createAttribute(name)
        if att is None:
            return jsonErrorReturn('Cannot create attribute, may be invalid name', HTTP_BAD_REQUEST)
    else:
        # Reset the name:
        nodat.setName(name)  # error return

    return jsonSuccessReturn("Attribute Created")

@webRest.route(API_PREFIX + 'ti/<int:tiId>/attribute', methods=['DELETE'])
@wr_check_session
def deleteTiAttribute(sess, tiId):
    ti = _checkTiAttributeStuff(sess, tiId)
    if not isinstance(ti, models.TraitInstance):
        return ti
    errmsg = ti.deleteAttribute()
    if errmsg is None:
        return jsonSuccessReturn("Attribute Deleted")
    else:
        return jsonErrorReturn(errmsg, HTTP_SERVER_ERROR)

### Projects: ---------------------------------------------------------------------------------------

@webRest.route(API_PREFIX + 'test', methods=['GET'])
#@wr_check_session
def urlTest():
    return 'test return\n'

### Users: ####################################################################################

def new_user_post_auth(userid, params):
#----------------------------------------------------------------------------------------------
# Create a new user for requesting user with specified id.
# It is assumed that this user has been authenticated.
# params must have a get method which allows the retrieval
# of the various inputs we need. This function is like this
# so that it can be used whether the request came from either
# a form submission or a post of json content.
#
# Could merge this back into urlCreateUser now as disambiguation
# of input source happens there.
#
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER):
        return jsonErrorReturn("no user create permission", HTTP_UNAUTHORIZED)
    
    # check all details provided (should be infra)
    login = params.get('login')
    loginType = params.get('loginType')
    if login is None or loginType is None:
        return jsonErrorReturn("login and loginType required", HTTP_BAD_REQUEST)

    # check if user already exists
    if fpsys.User.getByLogin(login) is not None:
        return jsonErrorReturn("User with that login already exists", HTTP_BAD_REQUEST)

    # create them
    if int(loginType) == LOGIN_TYPE_LOCAL:
        password = params.get('password')
        fullname = params.get('fullname')
        email = params.get('userEmail')
        # Validation - should be by infrastructure..
        if password is None or fullname is None:
            return jsonErrorReturn("password and fullname required for local user", HTTP_BAD_REQUEST)        
        if not util.isValidName(fullname):
            return jsonErrorReturn('Invalid user name', HTTP_BAD_REQUEST)
        if not util.isValidPassword(password):
            return jsonErrorReturn('Invalid password', HTTP_BAD_REQUEST)
        print 'email:{}'.format(email)
        if not util.isValidEmail(email):
            return jsonErrorReturn("Invalid email address", HTTP_BAD_REQUEST)
        errmsg = fpsys.addLocalUser(login, fullname, password, email)
    elif loginType == LOGIN_TYPE_***REMOVED***:
        errmsg = fpsys.add***REMOVED***User(login)
    else:
        errmsg = 'Invalid loginType'
    if errmsg is not None:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    return jsonSuccessReturn('User {} created'.format(login), HTTP_CREATED)

#@webRest.route(API_PREFIX + 'users', methods=['POST'])
@token_auth.login_required
def OLD_urlCreateUser():
#----------------------------------------------------------------------------------------------
# Create new user, from details provided in json.
# Authenticated user must have create user perms.
# NB Currently can only create local user. Need to be able to create ***REMOVED***,
# could have login_type parameter.
# Expects json input with the following information:
# . login
# . loginType
# . password
# . fullname
#

#     if g.user == 'xxxx': # hack to solve browser authentication prob..
#         print 'here goeth'
#         return Response('<Why access is denied string goes here...>', 401)
    if request.json is None and request.form is not None:
        params = request.form
    elif request.json is not None and request.form is None:
        params = request.json
    else:
        jsonErrorReturn('Missing parameters', HTTP_BAD_REQUEST)
    ret = new_user_post_auth(g.user, params)
    ret.set_cookie(NAME_COOKIE_TOKEN, g.newToken)
    return ret

def wrap_api_func(func):
#-------------------------------------------------------------------------------------------------
# func should return a response.
# request is assumed to be available
# func should have first params: userid, params.
#
    @wraps(func)
    def inner(*args, **kwargs):
        if request.json is None and request.form is not None:
            params = request.form
        elif request.json is not None: # and request.form is None:   Note if both json and form, we use json only
            params = request.json
        else:
            return jsonErrorReturn('Missing parameters', HTTP_BAD_REQUEST)
        ret = func(g.user, params, *args, **kwargs)
        ret.set_cookie(NAME_COOKIE_TOKEN, g.newToken)
        return ret
    return inner

@webRest.route(API_PREFIX + 'users', methods=['POST'])
@token_auth.login_required
@wrap_api_func
#def NEW_new_user_post_auth(userid, params):
def urlCreateUser(userid, params):
#----------------------------------------------------------------------------------------------
# Create a new user for requesting user with specified id.
# It is assumed that this user has been authenticated.
# params must have a get method which allows the retrieval
# of the various inputs we need. This function is like this
# so that it can be used whether the request came from either
# a form submission or a post of json content.
#
# Could merge this back into urlCreateUser now as disambiguation
# of input source happens there.
#
    # check permissions
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_CREATE_USER):
        return jsonErrorReturn("no user create permission", HTTP_UNAUTHORIZED)
    
    # check all details provided (should be infra)
    login = params.get('login')
    loginType = params.get('loginType')
    if login is None or loginType is None:
        return jsonErrorReturn("login and loginType required", HTTP_BAD_REQUEST)

    # check if user already exists
    if fpsys.User.getByLogin(login) is not None:
        return jsonErrorReturn("User with that login already exists", HTTP_BAD_REQUEST)

    # create them
    if int(loginType) == LOGIN_TYPE_LOCAL:
        password = params.get('password')
        fullname = params.get('fullname')
        email = params.get('userEmail')
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
    return jsonSuccessReturn('User {} created'.format(login), HTTP_CREATED)

### Projects: ############################################################################

#@webRest.route(API_PREFIX + 'projects', methods=['GET'])
@basic_auth.login_required
def getProjects():
    (plist, errmsg) = fpsys.getUserProjects(g.user)
    if errmsg:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    print len(plist)
    nplist = [p.name() for p in plist]
    return jsonReturn(nplist, HTTP_OK)  # return urls - do we need set Content-Type: application/json?

@webRest.route(API_PREFIX + 'projects/<int:id>', methods=['GET'])
@basic_auth.login_required
def getProject(id):
    util.flog("in getProject")
    (plist, errmsg) = fpsys.getUserProjects(g.user)
    if errmsg:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    print len(plist)
    nplist = [p.name() for p in plist]
    return jsonReturn(nplist, HTTP_BAD_REQUEST)  # return urls - do we need set Content-Type: application/json?

@webRest.route(API_PREFIX + 'projects', methods=['POST'])
@token_auth.login_required
@wrap_api_func
def urlCreateProject(userid, params):
# Expects URL parameters:
#   ownDatabase : 'true' or 'false', indicating whether separate database should be
#                 created. Currently ignored and assumed true.
#   projectName : name project - must be appropriate.
#   contactName : Name of contact person
#   contactEmail : email of contact person
#
# Note, perhaps we should use json input, in which case we would have:
# projectName = request.json.get('projectName')...
# top level dir called 'projects'? 'users'
#     parentUrl = request.json.get('parent')
#     parentProj = models.Project.getByUrl(parentUrl);
#

# todo parameter checks

    # Check permissions:
    if not fpsys.User.sHasPermission(userid, fpsys.User.PERMISSION_OMNIPOTENCE):
        return jsonErrorReturn("No permission for project creation", HTTP_UNAUTHORIZED)

    try: # not sure we need try anymore..
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
            return jsonErrorReturn('Problem in REST create project', HTTP_BAD_REQUEST)
        print 'urlCreateProject xxxx'

        # Check admin user exists, get id:
            # check if user already exists
        adminUser = fpsys.User.getByLogin(adminLogin)
        if adminUser is None:
            return jsonErrorReturn("Unknown admin user ({}) does not exist".format(adminLogin), HTTP_BAD_REQUEST)

        # Create the project:
        proj = models.Project.makeNewProject(projectName, ownDatabase, contactName, contactEmail, adminLogin)
#        if not isinstance(proj, models.Project): # return project json representation? Or URL?
        if isinstance(proj, basestring):
            return jsonErrorReturn(proj, HTTP_BAD_REQUEST)
#         else:
#             return jsonSuccessReturn("project created", HTTP_CREATED)
        print 'urlCreateProject nnnnn'

        # Add the adminUser to the project:
        print 'admin: {} pname {}'.format(adminUser.id(), projectName)
        errmsg = fpsys.addUserToProject(adminUser.id(), projectName, 1)  #MFK define and use constant
        if errmsg is not None:
            return jsonErrorReturn('project {} created, but could not add user {} ({})'.format(projectName,
                adminLogin, errmsg))

        # Return representation of the project, or a link to it?
        return jsonSuccessReturn('Project {} created'.format(projectName), HTTP_CREATED)
    except Exception, e:
        return jsonErrorReturn('Problem in REST create project: ' + str(e), HTTP_BAD_REQUEST)





#@webRest.route(API_PREFIX + 'projects', methods=['POST'])
@basic_auth.login_required
def OLD_urlCreateProject():
# Expects URL parameters:
#   ownDatabase : 'true' or 'false', indicating whether separate database should be
#                 created. Currently ignored and assumed true.
#   projectName : name project - must be appropriate.
#   contactName : Name of contact person
#   contactEmail : email of contact person
#
# Note, perhaps we should use json input, in which case we would have:
# projectName = request.json.get('projectName')...
# top level dir called 'projects'? 'users'
#     parentUrl = request.json.get('parent')
#     parentProj = models.Project.getByUrl(parentUrl);
#
# Not the use of sess in here - this is problematic as proper rest calls won't have a session.
# We are using to get user ident, which hopefully is available from token or basic auth
#sess.getUserIdent()
    # Check permissions:
    if not fpsys.User.sHasPermission(g.user, fpsys.User.PERMISSION_OMNIPOTENCE):
        return jsonErrorReturn("No permission for project creation", HTTP_UNAUTHORIZED)

    try:
        frm = request.form
        projectName = frm['projectName']
        contactName = frm['contactName']
        contactEmail = frm['contactEmail']
        ownDatabase = frm['ownDatabase']
        adminLogin = frm['adminLogin']
        if ownDatabase == 'true':
            ownDatabase = True
        elif ownDatabase == 'false':
            ownDatabase = False
        else:
            return jsonErrorReturn('Problem in REST create project', HTTP_BAD_REQUEST)
        print 'urlCreateProject'

        # Check admin user exists, get id:
            # check if user already exists
        adminUser = fpsys.User.getByLogin(adminLogin)
        if adminUser is None:
            return jsonErrorReturn("Unknown admin user ({}) does not exist".format(adminLogin), HTTP_BAD_REQUEST)

        # Create the project:
        proj = models.Project.makeNewProject(projectName, ownDatabase, contactName, contactEmail, adminLogin)
#        if not isinstance(proj, models.Project): # return project json representation? Or URL?
        if isinstance(proj, basestring):
            return jsonErrorReturn(proj, HTTP_BAD_REQUEST)
        else:
            return jsonSuccessReturn("project created", HTTP_CREATED)
        print 'urlCreateProject'

        # Add the adminUser to the project:
        errmsg = fpsys.addUserToProject(adminUser.getId(), projectName, 1)  #MFK define and use constant
        if errmsg is not None:
            return jsonErrorReturn('project {} created, but could not add user {} ({})'.format(projectName,
                adminLogin, errmsg))

        # Return representation of the project, or a link to it?
        return jsonSuccessReturn('Project {} created'.format(projectName), HTTP_CREATED)
    except Exception, e:
        return jsonErrorReturn('Problem in REST create project: ' + str(e), HTTP_BAD_REQUEST)


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


def checkIdent(candidate):
    re.match('\w\w*')

#@webRest.route(API_PREFIX + 'projects', methods=['POST'])
@basic_auth.login_required
def new_createProject():
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

     
'''
    
@webRest.route(API_PREFIX + 'projects/<int:projId>/trials', methods=['POST'])
@multi_auth.login_required
@wrap_api_func
def urlCreateTrial(userid, params, projId):
# Paramaters can be form or json.    
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
    
    return jsonSuccessReturn('Trial {} created'.format(trialName), HTTP_CREATED)


### Attributes: ##########################################################################

@webRest.route('/project/<projectName>/attribute/<attId>', methods=['GET'])
@wr_check_session
def urlAttributeData(sess, projectName, attId):
#---------------------------------------------------------------------------------
# Return nodeId:attValue pairs
# These are sorted by node_id.
# This is used in the admin web pages.
#
    natt = models.getAttribute(sess.db(), attId)
    vals = natt.getAttributeValues()
    data = []
    for av in vals:
        data.append([av.getNode().getId(), av.getValueAsString()])
    return Response(json.dumps(data), mimetype='application/json')


########################################################################################
TEST_STUFF = '''
FP=http://0.0.0.0:5001/fpv1

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

# Create ***REMOVED*** user:
curl -u mk:m -i -X POST -H "Content-Type: application/json" \
     -d '{"login":"***REMOVED***","loginType":2}' $FP/users

# Create Local user:
curl -u mk:m -i -X POST -H "Content-Type: application/json" \
     -d '{"login":"al","password":"a","fullname":"Al Ocal","loginType":3}' $FP/users

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

@webRest.route('/project/<projectName>/trial/<trialId>/slice/<tiId>', methods=['GET'])
@wr_check_session
def urlDataSlice(sess, projectName, trialId, tiId):
    dic = {'a':1}
    return Response(json.dumps(dic), mimetype='application/json')


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

