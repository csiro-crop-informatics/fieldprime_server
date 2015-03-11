#
# Functions to respond to REST calls.
# These return json
#
#
#
#
#
#
#
#
#
#
#
#
#




from flask import Blueprint

import fp_common.models as models

webRest = Blueprint('webRest', __name__)


def wr_check_session(returnNoneSess=False):
#-------------------------------------------------------------------------------------------------
# Decorator to check if in valid session. If not, send the login page.
# Generates function that has session as first parameter.
# If returnNoneSess is true, then the function is returned even if session is
# invalid, but with None as the session parameter - this can be used for pages
# that don't require a user to be logged in.
# NB Derived from fpWebAdmin:dec_check_session.
    def param_dec(func):
        @wraps(func)
        def inner(*args, **kwargs):
            COOKIE_NAME = 'sid'
            sid = request.cookies.get(COOKIE_NAME) # Get the session id from cookie (if there)
            sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, app.config['SESS_FILE_DIR']) # Create or get session object
            if not sess.valid():  # Check if session is still valid
                if returnNoneSess:
                    return func(None, *args, **kwargs)
                return render_template('sessError.html', title='Field Prime Login',
                                       msg='Your session has timed out - please login again.')
            return func(sess, *args, **kwargs)
        return inner
    return param_dec



@webRest.route('/fishcakes', methods=["GET"])
def fishcakes():
    return 'fishcakes are going to be big!'



@webRest.route('/project/<projectName>/trial/<trialId>/slice/<tiId>', methods=['GET'])
def urlDataSlice(projectName, trialId, tiId):
    return Response(json.dumps(dic), mimetype='application/json')




