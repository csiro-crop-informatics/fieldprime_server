# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
# see http://blog.miguelgrinberg.com/post/restful-authentication-with-flask

from flask import Blueprint, current_app, request, Response, jsonify, g, abort
from flask.ext.httpauth import HTTPBasicAuth
from functools import wraps
import simplejson as json
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import re

import fp_common.models as models
import fp_common.users as users
import fp_common.fpsys as fpsys
import websess
from fp_common.const import LOGIN_TIMEOUT, LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***, LOGIN_TYPE_LOCAL
import fpUtil
import fp_common.util as util


### Initialization: ####################################
webRest = Blueprint('webRest', __name__)
auth = HTTPBasicAuth()

### Constants: #########################################

API_PREFIX = '/fpv1/'

# Http status codes:
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500


def jsonErrorReturn(errmsg, statusCode):
    return Response(json.dumps({'error':errmsg}), status=statusCode, mimetype='application/json')

def jsonReturn(jo, statusCode):
    return Response(json.dumps(jo), status=statusCode, mimetype='application/json')


### Authorization stuff: ########################################################

def generate_auth_token(username, expiration=600):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': username})

def verify_auth_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None    # valid token, but expired
    except BadSignature:
        return None    # invalid token
    user = data['id']
    return user

@auth.verify_password
def verify_password(username_or_token, password):
# Password check.
# This is invoked by the auth.login_required decorator.
#    
    # first try to authenticate by token
    user = verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        check = fpsys.userPasswordCheck(username_or_token, password)
        if not check: return False
        else: user = username_or_token
    g.user = user
    return True

### Access Points: ########################################################

@webRest.route(API_PREFIX + 'token', methods=['GET'])
@auth.login_required
def get_auth_token():
#-------------------------------------------------------------------------------------------------
# Returns, in a JSON object, a token for user.
# The returned token may be used as a basic authentication username
# for subsequent calls to the api (for up to 600 seconds).
# This is in place of repeatedly sending the real username and password.
# When using the token as the username, the password is not used, so any
# value can be given.
#
    token = generate_auth_token(g.user, 600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@webRest.route(API_PREFIX + 'users', methods=['POST'])
@auth.login_required
def new_user():
#-------------------------------------------------------------------------------------------------
# Create new user.
# Authenticated user must have create user perms.
# NB Currently can only create local user. Need to be able to create ***REMOVED***,
# could have login_type parameter.
#
    # check permissions
    if not fpsys.User.sHasPermission(g.user, fpsys.User.PERMISSION_CREATE_USER):
        return jsonErrorReturn("no user create permission", HTTP_UNAUTHORIZED)
    # check all details provided
    login = request.json.get('login')
    loginType = request.json.get('loginType')
    if login is None or loginType is None:
        return jsonErrorReturn("login and loginType required", HTTP_BAD_REQUEST)

    # check if user already exists
    if fpsys.User.getByLogin(login) is not None:
        return jsonErrorReturn("User with that login already exists", HTTP_BAD_REQUEST)

    # create them
    if loginType == LOGIN_TYPE_LOCAL:
        password = request.json.get('password')
        fullname = request.json.get('fullname')
        if password is None or fullname is None:
            return jsonErrorReturn("password and fullname required for local user", HTTP_BAD_REQUEST)
        errmsg = fpsys.addLocalUser(login, fullname, password)
    elif loginType == LOGIN_TYPE_***REMOVED***:
        errmsg = fpsys.add***REMOVED***User(login)
    else:
        errmsg = 'Invalid loginType'
    if errmsg is not None:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    return jsonReturn({'username': login}, HTTP_CREATED)

@webRest.route(API_PREFIX + 'projects', methods=['GET'])
@auth.login_required
def getProjects():
    (plist, errmsg) = fpsys.getProjects(g.user)
    if errmsg:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    print len(plist)
    nplist = [p.name() for p in plist]
    return jsonReturn(nplist, HTTP_OK)  # return urls - do we need set Content-Type: application/json?

###########################################################

@webRest.route(API_PREFIX + 'grant/<login>/<permission>', methods=['GET'])
@auth.login_required
def authUser(login, permission):
    pass


@webRest.route(API_PREFIX + 'projects/<int:id>', methods=['GET'])
@auth.login_required
def getProject(id):
    util.flog("in getProject")
    (plist, errmsg) = fpsys.getProjects(g.user)
    if errmsg:
        return jsonErrorReturn(errmsg, HTTP_BAD_REQUEST)
    print len(plist)
    nplist = [p.name() for p in plist]
    return jsonReturn(nplist, HTTP_BAD_REQUEST)  # return urls - do we need set Content-Type: application/json?



@webRest.route(API_PREFIX + 'XXXprojects/<path:path>', methods=['POST'])
@auth.login_required
def createProject(path):
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

@webRest.route(API_PREFIX + 'projects', methods=['POST'])
@auth.login_required
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

@webRest.route(API_PREFIX + 'XXXprojects', methods=['POST'])
@auth.login_required
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
### Old stuff, but note some of it may be in use: ######################################


def wr_check_session(func):
#-------------------------------------------------------------------------------------------------
# Decorator to check if in valid session. If not, send the login page.
# Generates function that has session as first parameter.
# If returnNoneSess is true, then the function is returned even if session is
# invalid, but with None as the session parameter - this can be used for pages
# that don't require a user to be logged in.
# NB Derived from fpWebAdmin:dec_check_session.
    @wraps(func)
    def inner(*args, **kwargs):
        COOKIE_NAME = 'sid'
        sid = request.cookies.get(COOKIE_NAME) # Get the session id from cookie (if there)
        sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, current_app.config['SESS_FILE_DIR']) # Create or get session object
        if not sess.valid():  # Check if session is still valid
            return {'error':'not logged in'}, 401
        return func(sess, *args, **kwargs)
    return inner

@webRest.route('/project/<projectName>/trial/<trialId>/slice/<tiId>', methods=['GET'])
@wr_check_session
def urlDataSlice(sess, projectName, trialId, tiId):
    dic = {'a':1}
    return Response(json.dumps(dic), mimetype='application/json')

@webRest.route('/project/<projectName>/attribute/<attId>', methods=['GET'])
@wr_check_session
def urlAttributeData(sess, projectName, attId):
#---------------------------------------------------------------------------------
# Return nodeId:attValue pairs
# These are sorted by node_id.
    natt = models.getAttribute(sess.db(), attId)
    vals = natt.getAttributeValues()
    data = []
    for av in vals:
        data.append([av.node_id, av.value])
    return Response(json.dumps(data), mimetype='application/json')


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

