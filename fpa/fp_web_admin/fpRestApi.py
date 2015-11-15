# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
# see http://blog.miguelgrinberg.com/post/restful-authentication-with-flask

from flask import Blueprint, current_app, request, Response, jsonify
from functools import wraps
import simplejson as json

import fp_common.models as models
import fp_common.users as users
import fp_common.fpsys as fpsys
import websess
from fp_common.const import LOGIN_TIMEOUT, LOGIN_TYPE_SYSTEM, LOGIN_TYPE_***REMOVED***
import fpUtil
import fp_common.util as util

webRest = Blueprint('webRest', __name__)


########################################################################################
########################################################################################
from flask import g
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# initialization

#current_app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'

# extensions
auth = HTTPBasicAuth()



def hash_password(self, password):
    self.password_hash = pwd_context.encrypt(password)

# def verify_user_password(username, password):
#     return pwd_context.verify(password, self.password_hash)

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

@webRest.route(/fp/newUser/<login>/fullname/<fullname>/password/<password)
def newUser(login, fullname, password):
    # check user strings for bad stuff
    pwhash = hashPassword(password)
    try:
        con = fpsys.getFpsysDbConnection()
        qry = "insert user values (login, name, password, login_type) values (%s,%s,%s,%s)"
        cur = con.cursor()
        cur.execute(qry, (login, fullname, pwhash, LOGIN_TYPE_LOCAL))
        return None if resRow is None else resRow[0]
    except mdb.Error, e:
        return None

    pass
    #need password and such

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        check = users.userPasswordCheck(username_or_token, password)
        if check is None: return False
        else: user = username_or_token
    g.user = user
    print 'user: %s' % user
    return True

@webRest.route('/api/token')
@auth.login_required
def get_auth_token():
    token = generate_auth_token(g.user, 600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@webRest.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user})

def jsonErrorReturn(errmsg):
    return jsonify({'error':errmsg})

def jsonReturn(jo):
    return Response(json.dumps(jo), mimetype='application/json')

@webRest.route('/fp/project')
@auth.login_required
def getProjects():
    util.flog("in getProjects")
    (plist, errmsg) = fpsys.getProjects(g.user)
    if errmsg:
        return jsonErrorReturn(errmsg)
    print len(plist)
    nplist = [p.name() for p in plist]
    return jsonReturn(nplist)  # return urls - do we need set Content-Type: application/json?

########################################################################################


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

# not used yet
def userPasswordCheck(username, password):
    if users.systemPasswordCheck(username, password):
        return LOGIN_TYPE_SYSTEM
    elif users.***REMOVED***PasswordCheck(username, password):  # Not a main project account, try as ***REMOVED*** user.
        # For ***REMOVED*** check, we should perhaps first check in a system database
        # as to whether the user is known to us. If not, no point checking ***REMOVED*** credentials.
        #
        # OK, valid ***REMOVED*** user. Find project they have access to:
        return LOGIN_TYPE_***REMOVED***
    else:
        return None




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
    if users.systemPasswordCheck(username, password):
        project = username
        access = websess.PROJECT_ACCESS_ALL
        dbname = models.dbName4Project(project)
        loginType = LOGIN_TYPE_SYSTEM
    elif users.***REMOVED***PasswordCheck(username, password):  # Not a main project account, try as ***REMOVED*** user.
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
    sess.setUser(username)
    sess.setProject(project, dbname, access)
    sess.setLoginType(loginType)
    return jsonify({'token':sess.sid()})

