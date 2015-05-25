# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
#

from flask import Blueprint, current_app, request, Response, jsonify
from functools import wraps
import simplejson as json

import fp_common.models as models
import websess
from const import *
import fpUtil
import fp_common.util as util

webRest = Blueprint('webRest', __name__)


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
# in the file system), and the id of this session is sent back to the browser in a cookie,
# which should be sent back with each subsequent request.
#
# Every access via the various app.routes above, should go through decorator dec_check_session
# which will check there is a valid session current. If not, eg due to timeout, then it redirects
# to the login screen.
#
# Notes:
# Ideally, perhaps, after a redirect to the login screen, and successful login, we should go directly
# to where the user was originally trying to get to..
#
# Perhaps all of the app.routes should start with a /trial/<trialId>, even when this is not strictly
# necessary, eg for urlScoreSetTraitInstance, which doesn't need it since the TI id is unique within db.
# Or perhaps it should be /user/userName/[trial/trialId]/
#
# Might want to change displayed url for some things eg the op to change password ends up displaying
# the FrontPage, but shows the URL for the op.
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
    if systemPasswordCheck(username, password):
        project = username
        access = websess.PROJECT_ACCESS_ALL
        dbname = models.dbName4Project(project)
        loginType = LOGIN_TYPE_SYSTEM
    elif ***REMOVED***PasswordCheck(username, password):  # Not a main project account, try as ***REMOVED*** user.
        # For ***REMOVED*** check, we should perhaps first check in a system database
        # as to whether the user is known to us. If not, no point checking ***REMOVED*** credentials.
        #
        # OK, valid ***REMOVED*** user. Find project they have access to:
        loginType = LOGIN_TYPE_***REMOVED***
        projList, errMsg = fpsys.getProjects(username)
        if errMsg is not None:
            error = 'Failed system login'
        elif not projList:
            error = 'No projects found for user {0}'.format(username)
        else:
            project = access = dbname = None
    else:
        util.fpLog(app, 'Login failed attempt for user {0}'.format(username))
        error = 'Invalid Password'

    if not error:
        # Good to go, show the user front page, after adding cookie:
        util.fpLog(app, 'Login from user {0}'.format(username))
        sess.resetLastUseTime()
        sess.setUser(username)
        sess.setProject(project, dbname, access)
        sess.setLoginType(loginType)
        g.userName = username
        g.projectName = project
        resp = make_response(FrontPage(sess))
        resp.set_cookie(COOKIE_NAME, sess.sid())      # Set the cookie
        return resp


    # Error return
    return render_template('sessError.html', msg=error, title='FieldPrime Login')
