# fpApi.py
# Michael Kirk 2013
# 
#

import os, sys, time
import MySQLdb as mdb
from flask import Flask, request, Response, url_for, render_template, g, make_response
from flask import json, jsonify
from functools import wraps
from werkzeug import secure_filename
from jinja2 import Environment, FileSystemLoader

if __name__ == '__main__':
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir) 

import dbUtil
import fpTrait
import fp_common.models as models
import fpTrial
from dbUtil import GetTrial, GetTrials, GetSysTraits
from fpUtil import HtmlFieldset, HtmlForm, HtmlButtonLink

import websess

app = Flask(__name__)
try:
    app.config.from_object('fp_web_admin.fpAppConfig')
except ImportError:
    print 'no fpAppConfig found'
    pass

# If env var FPAPI_SETTINGS is set then load configuration from the file it specifies:
app.config.from_envvar('FP_WEB_ADMIN_SETTINGS', silent=True)

# Load the Data Access Layer Module (must be named in the config)
import importlib
dal = importlib.import_module(app.config['DATA_ACCESS_MODULE'])


gdbg = True  # Switch for logging to file


##################################################################################################







def LogDebug(hdr, text):
#-------------------------------------------------------------------------------------------------
# Writes stuff to file system (for debug)
    f = open('/tmp/fieldPrimeDebug','a')
    print >>f, "--- " + hdr + ": ---"
    print >>f, text
    print >>f, "------------------"
    f.close


#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
# Old stuff:



#############################################################################################
#############################################################################################

HOMEPAGE = "/test"

@app.route('/')
def hello_world():
    return 'Hello Sailor!'


LOGIN_TIMEOUT = 300

def CheckPassword(user, password):
#-----------------------------------------------------------------------
# Validate user/password, returning boolean indicating success
#
    try:
        usrname = 'fp_' + user
        usrdb = usrname
        con = mdb.connect('localhost', usrname, password, usrdb);
        cur = con.cursor()
        cur.execute("SELECT VERSION()")
        ver = cur.fetchone()
        return True
    except mdb.Error, e:
        return False


def FrontPage(sess):
#-----------------------------------------------------------------------
# Return HTML Response for main user page after login
#
    x = sess.timeSinceUse()
    sess.resetLastUseTime()
    suser = sess.GetUser()

    r = "hallo <a href={0}?op=user>{1}</a> last seen {2} <br>".format(HOMEPAGE, suser, time.asctime(time.gmtime(sess.getLastUseTime())))
    r += "Time since last seen: {0} <br>".format(x)
    r += "Time till login expires: {{LOGIN_TIMEOUT }} <br><p>".format(LOGIN_TIMEOUT - x)

    # Administer passwords button:
    r += "<p>" + HtmlButtonLink("Administer Passwords", "{0}?op=user".format(HOMEPAGE))

    # Traits:
    trials = GetTrials(sess)
    trialListHtml = "No trials yet" if len(trials) < 1 else ""
    for t in trials:
        trialListHtml += "<li><a href={0}?op=showTrial&tid={1}>{2}</a></li>".format(HOMEPAGE, t.id, t.name)

    r += HtmlFieldset(HtmlForm(trialListHtml) +  HtmlButtonLink("Create New Trial", HOMEPAGE + "?op=newTrial"), "Current Trials")

    # System Traits:
    sysTraits = GetSysTraits(sess)
    #from fp_common.fpTrait import TraitListHtmlTable
    sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else fpTrait.TraitListHtmlTable(sysTraits)
    r += HtmlFieldset(HtmlForm(sysTraitListHtml) \
                          + HtmlButtonLink("Create New System Trait", HOMEPAGE + "?op=newTrait&tid=sys"),
                      "System Traits")

    return make_response(render_template('genericPage.html', content=r, title="User: " + sess.GetUser()))



def TrialHtml(sess, trialId):
#-----------------------------------------------------------------------
    trial = dbUtil.GetTrial(sess, trialId)

    # Trial name and attributes:
    r = "<p><h3>Trial : {0}</h3>".format(trial.name)
    r += "<ul>"
    if trial.site: r += "<li>Site:" + trial.site + "</li>" 
    if trial.year: r += "<li>Year:" + trial.year + "</li>" 
    if trial.site: r += "<li>Acronym:" + trial.acronym + "</li>" 
    r += "</ul>"

    # Attributes:
    attList = dbUtil.GetTrialAttributes(sess, trialId)
    def atts():
        if len(attList) < 1:
            return "No attributes found"
        out = "<ul>"
        for att in attList:
            out += "<li><a href={0}?op=attribute&aid={1}>{2}</a></li>".format(HOMEPAGE, att.id, att.name)
        return out + "</ul>"
    r += HtmlForm(HtmlFieldset(atts, "Attributes:"))

    # Traits:
    def content():
        if len(trial.traits) < 1:
            return "No traits configured"
        out = "<table border='1'>"
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format("Caption", "Description", "Type", "Min", "Max")
        for trt in trial.traits:
            out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(
                trt.caption, trt.description, models.TRAIT_TYPE_NAMES[trt.type], trt.min, trt.max)
        out += "</table>"
        return out

    createTraitButton =  """<p><button style="color: red" onClick="window.location = """
    createTraitButton += """'{0}?op=newTrait&tid={1}'">Create New Trait</button>""".format(HOMEPAGE, trialId)

    addSysTraitForm = '<FORM method="POST" action="{0}?op=addSysTrait2Trial&tid={1}">'.format(HOMEPAGE, trialId)
    addSysTraitForm += '<input type="submit" value="Submit">'
    addSysTraitForm += '<select name="traitID"><option value="0">Select System Trait to add</option>'
    sysTraits = dbUtil.GetSysTraits(sess)
    for st in sysTraits:
        for trt in trial.traits:   # Only add traits not already in trial
            if trt.id == st.id:
                break
        else:
            addSysTraitForm += '<option value="{0}">{1}</option>'.format(st.id, st.caption)
    addSysTraitForm += '</select></form>'

    r += HtmlFieldset(HtmlForm(content) + createTraitButton + addSysTraitForm, "Traits:")

    # Trait Instances:
    tiList = dbUtil.GetTraitInstancesForTrial(sess, trialId)
    def tis():
        if len(tiList) < 1:
            return "No trait instances found"
        out = "<ul>"
        for ti in tiList:
            out += "<li><a href={0}?op=traitInstance&tiid={1}>{3}:{2}:{4}</a></li>".format(HOMEPAGE, ti.id, ti.trait.caption, ti.trial.name,ti.trial_id)
        return out + "</ul>"
    r += HtmlForm(HtmlFieldset(tis, "Trait Instances:"))

    # Download data link:
    r += "<a href={0}?op=trialData&tid={1}>Download Score Data as CSV (right click and Save Link As)</a>".format(HOMEPAGE, trialId)
    return r

def AddSysTraitTrial(sess, trialId, traitId):
#-----------------------------------------------------------------------
# Return error string, None for success
#
    if traitId == "0":
        return "Select a system trait to add"
    try:
        usrname = 'fp_' + sess.GetUser()
        usrdb = usrname
        qry = "insert into trialTrait (trial_id, trait_id) values ({0}, {1})".format(trialId, traitId)
        con = mdb.connect('localhost', usrname, sess.GetPassword(), usrdb)
        cur = con.cursor()
        cur.execute(qry)
        con.commit()
    except mdb.Error, e:
        return  usrdb + " " + qry
    return None

def AdminForm(sess, op = '', msg = ''):
#-----------------------------------------------------------------------
# Returns Response which is the user admin form. MK - could use template?
#
    adminMsg = msg if op == 'newpw' else ''
    appMsg =  msg if op == 'setAppPassword' else ''
    #adminMsg = op
    #appMsg = msg
    changeAdminPassForm = """
<FORM method="POST" action="{0}?op=newpw">
<p> The <i>Admin Password</i> is the password used to login to this web server to
manage the trials. I.e. the one you must have used at some stage to get to this page.
<p> Enter your login name: <input type="text" name="login">
<p> Enter your current password: <input type=password name="password">
<p>Enter your new password: <input type=password name="newpassword1">
<p>Confirm your new password: <input type=password name="newpassword2">
<p> <input type="submit" value="Change Admin Password">
</FORM>
</form>
{1}
""".format(HOMEPAGE, adminMsg)
    changeAppPassForm = """
<FORM method="POST" action="{0}?op=setAppPassword">
<p> The <i>Scoring Devices Password</i> is the password that needs to be configured on the scoring devices
to allow them to download trial information, and upload trial scores. If this is not configured,
or if it is blank, then the scoring devices will be able to download and upload without configuring
a password on the device.
<p> Note this is not the same as the admin password, (used to login to this web server to
manage the trials). The app password is less secure than the admin password (it could be retrieved
from the scoring device with some effort), so this should not be set to the same value as the
admin password.
<p> Enter your <i>Admin</i> login name: <input type="text" name="login">
<p> Enter your current <i>Admin</i> password: <input type=password name="password">
<p>Enter new <i>Scoring Device</i> password: <input type=password name="newpassword1">
<p>Confirm new <i>Scoring Device</i> password: <input type=password name="newpassword2">
<p> <input type="submit" value="Change App Password">
</FORM>
</form>
{1}
""".format(HOMEPAGE, appMsg)
    r =  HtmlFieldset(changeAdminPassForm, "Reset Admin password") + \
                    HtmlFieldset(changeAppPassForm, "Reset Scoring Devices Password")
    return render_template('genericPage.html', content=r, title='Field Prime Login')


def ProcessAdminForm(sess, op, form):
#-----------------------------------------------------------------------
# Handle login form submission
# Returns Response for display.
#
    suser = form.get("login")
    password = form.get("password")
    newpassword1 = form.get("newpassword1")
    newpassword2 = form.get("newpassword2")
    if not (suser and password and newpassword1 and newpassword2):
        return AdminForm(sess, op, "<p>Please fill out all fields</p>")
    if newpassword1 != newpassword2:
        return AdminForm(sess, op, "<p>Versions of new password do not match.</p>")
    if not CheckPassword(suser, password):
        return LoginForm("Password is incorrect")

    # OK, all good, change their password:
    try:
        usrname = 'fp_' + suser
        usrdb = usrname
        con = mdb.connect('localhost', usrname, password, usrdb)
        cur = con.cursor()
        if op == 'newpw':
            cur.execute("set password for {0}@localhost = password(\'{1}\')".format(usrname, newpassword1))
            sess.SetUserDetails(suser, newpassword1)
        elif op == 'setAppPassword':
            cur.execute("REPLACE system set name = 'appPassword', value = '{0}'".format(newpassword1))
            con.commit()
        con.close()

        return FrontPage(sess)
    except mdb.Error, e:
        return LoginForm("Password incorrect")  


def LoginForm(msg):
#-----------------------------------------------------------------------
# login form 
    return render_template('login.html', msg = msg, title='Field Prime Login')


def CreateNewTrait(sess,  trialId, caption, description, type, min, max):
#-----------------------------------------------------------------------
# Create trait in db, trial Id is id of trial if a local trait, else it is 'sys'.
# Returns error message if there's a problem, else None.
#
    sysTrait = True if trialId == "sys" else False
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.
    dbsess = sess.DB()
    ntrt = models.Trait()
    ntrt.caption = caption
    ntrt.description = description

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    if not sysTrait: # If local, check there's no other trait local to the trial with the same caption:
        trial = GetTrialFromDBsess(sess, trialId)
        for x in trial.traits:
            if x.caption == caption:
                return 'Error: A local trait with this caption already exists'
        ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        ntrt.sysType = models.SYSTYPE_TRIAL
    else:  # If system trait, check there's no other system trait with same caption:
        sysTraits = dbUtil.GetSysTraits(sess)
        for x in sysTraits:
            if x.caption == caption:
                return 'Error: A system trait with this caption already exists'
        ntrt.sysType = models.SYSTYPE_SYSTEM

    ntrt.type = type
    if min:
        ntrt.min = min
    if max:
        ntrt.max = max
    dbsess.add(ntrt)
    dbsess.commit()
    return None


def TraitInstanceHtml(sess, tiId):
#-----------------------------------------------------------------------
# Returns html for data for specified trait instance.
#
    data = sess.DB().query(models.Datum).filter(models.Datum.traitInstance_id == tiId).all()
    r = "Row Column Timestamp numValue textValue<br>"
    for d in data:
        r += "{0} {1} {2} {3} {4}<br>".format(d.trialUnit.row, d.trialUnit.col, d.timestamp, d.numValue, d.txtValue)
    return r


def TrialDataHtml(sess, trialId):
#-----------------------------------------------------------------------
# Returns trial data as plain text csv form - i.e. for download.
# The data is arranged in trial unit rows, and trait instance value and attribute
# columns.
#
    r = "Content-type: text/plain\n"

    # Get Trait Instances:
    tiList = dbUtil.GetTraitInstancesForTrial(sess, trialId)

    # Headers:
    r += "Row,Column"
    for ti in tiList:
        tiName = "{0}_{1}.{2}.{3}".format(ti.trait.caption, ti.dayCreated, ti.seqNum, ti.sampleNum)
        r += ",{0},{0}_timestamp,{0}_user,{0}_latitude,{0}_longitude,{0}.notes".format(tiName)
    r += "\n"

    # Data:
    tuList = dbUtil.GetTrialUnits(sess, trialId)
    for tu in tuList:
        r += "{0},{1}".format(tu.row, tu.col)
        for ti in tiList:
            type = ti.trait.type
            datums = dbUtil.GetDatum(sess, tu.id, ti.id)
            if len(datums) == 0:
                r += ",,,,,,"
            #elif len(datums) == 1:
            #    d = datums[0]
            #    if type == 0: value = d.numValue
            #    if type == 1: value = d.numValue
            #    if type == 2: value = d.txtValue
            #    if type == 3: value = d.numValue
            #    if type == 4: value = d.numValue
            #    r += ",{0},{1},{2},{3},{4}".format(value, d.timestamp, d.userid, d.gps_lat, d.gps_long)
            #else:
            #    r += "Error - too many datums"
            else:  # While there might be multiple, we get last:
                # Use the latest:
                lastDatum = datums[0]
                for d in datums:
                    if d.timestamp > lastDatum.timestamp: lastDatum = d
                d = lastDatum
                # This next switch is no good, have to support trait type polymorphism somehow..
                if type == 0: value = d.numValue
                if type == 1: value = d.numValue
                if type == 2: value = d.txtValue
                if type == 3: value = d.numValue
                if type == 4: value = d.numValue
                if type == 5: value = d.txtValue
                r += ",{0},{1},{2},{3},{4},".format(value, d.timestamp, d.userid, d.gps_lat, d.gps_long)
                if d.notes != None and len(d.notes) > 0: r += d.notes
        r += "\n"
    return r


@app.route(HOMEPAGE, methods=["GET", "POST"])
def main():
#-----------------------------------------------------------------------
    COOKIE_NAME = 'sid'
    sid = request.cookies.get(COOKIE_NAME)                # Get the session id from cookie (if there)
    sess = websess.Session(False, sid, LOGIN_TIMEOUT)     # Create session object (may be existing session)
    g.homepage = HOMEPAGE                                 # Set global variable accessible by templates
    op = request.args.get('op', '')
    if not op:
        error = ""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username:
                error = 'No username'
            elif not password:
                error = 'No password'
            elif not CheckPassword(username, password):
                error = 'Invalid password'
            else:
                # Good to go, show the user front page:
                sess.resetLastUseTime()
                sess.SetUserDetails(username, password)
                resp = FrontPage(sess)
                resp.set_cookie(COOKIE_NAME, sess.sid())
                return resp

        #return render_template('login.html', msg = error, title='Field Prime Login')
        return LoginForm(error)

    #----------------------------------------------------------
    # Case operation is specified:
    #

    # Check session still valid:
    if not sess.Valid():
        # Present login form:
        # Ideally have a redirect after login to current op, if there is one, but would need all form parameters
        # to be passed thru to the login form (op and any others needed for op, such as tid), and then passed
        # back by the login form to the login form submit handler. Alternatively perhaps, could bundle the
        # parameters into the session shelf.
        return render_template('login.html', title='Field Prime Login')

    if op == 'showTrial':
        tid = request.args.get('tid')
        return render_template('genericPage.html', content=TrialHtml(sess, tid), title='Trial Data')

    elif op == 'addSysTrait2Trial':
        tid = request.args.get('tid')
        errMsg = AddSysTraitTrial(sess, tid, request.form['traitID'])
        if errMsg:
            return render_template('genericPage.html', content=errMsg, title='Error')
        # If all is well, display the trial page:
        return render_template('genericPage.html', content=TrialHtml(sess, tid), title='Trial Data')

    elif op == 'user':
        return AdminForm(sess)
    elif op == 'newpw' or op == 'setAppPassword':
        return ProcessAdminForm(sess, op, request.form)

    elif op == 'newTrial':
        return fpTrial.NewTrial(sess)

    elif op == 'createTrial':
        uploadFile = request.files['file']
        res = fpTrial.CreateTrial(sess, uploadFile, request.form)
        if res:
            return res
        return FrontPage(sess)

    elif op == 'newTrait':
        # NB, could be a new sys trait, or trait for a trial. Indicated by tid which will be
        # either 'sys' or the trial id respectively.
        return render_template('newTrait.html', trialId = request.args.get("tid"),
                               traitTypes = models.TRAIT_TYPE_TYPE_IDS, title='New Trait')
    elif op == 'createTrait':
        trialId = request.args.get("tid")
        caption = request.form.get("caption")
        description = request.form.get("description")
        type = request.form.get("type")
        min = request.form.get("min")
        max = request.form.get("max")
        errMsg = CreateNewTrait(sess, trialId, caption, description, type, min, max)
        if errMsg:
            return render_template('genericPage.html', content=errMsg, title='Error')

        if trialId == 'sys':
            return FrontPage(sess)
        return render_template('genericPage.html', content=TrialHtml(sess, trialId), title='Trial Data')

    elif op == 'traitInstance':
        return render_template('genericPage.html',
                               content=TraitInstanceHtml(sess, request.args.get("tid")),
                               title='Trait Instance Data')

    elif op == 'trialData':
        return TrialDataHtml(sess, request.args.get("tid"))

    else:
        return render_template('genericPage.html', content="No such operation ({0})".format(op), title='Error')


# For local testing:
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

