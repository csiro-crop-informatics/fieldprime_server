# fpRestApi.py
# Michael Kirk 2015
#
# Functions to respond to REST type calls, i.e. urls for
# getting or setting data in json format.
#

from flask import Blueprint, current_app, request, Response
from functools import wraps
import simplejson as json

import fp_common.models as models
import websess
from const import *

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

@webRest.route('/project/<projectName>/trait/<traitId>', methods=['DELETE'])
@wr_check_session()
def urlTraitDelete(sess, projectName, ident):
    if not sess.adminRights() or projectName != sess.getProjectName():
        return badJuju(sess, 'No admin rights')
    errmsg = fpsys.deleteUser(sess.getProjectName(), ident)
    if errmsg is not None:
        return jsonify({"error":errmsg})
    else:
        return jsonify({"status":"good"})
