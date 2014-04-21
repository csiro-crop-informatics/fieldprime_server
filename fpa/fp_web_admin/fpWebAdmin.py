# fpApi.py
# Michael Kirk 2013
#
#

import os, sys, time
import MySQLdb as mdb
from flask import Flask, request, Response, redirect, url_for, render_template, g, make_response
from flask import json, jsonify
from werkzeug import secure_filename
from jinja2 import Environment, FileSystemLoader
from functools import wraps

if __name__ == '__main__':
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

import dbUtil
import fpTrait
import fp_common.models as models
import fpTrial
import fpUtil
from fp_common.const import *
from dbUtil import GetTrial, GetTrials, GetSysTraits
from fpUtil import HtmlFieldset, HtmlForm, HtmlButtonLink, HtmlButtonLink2

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

LOGIN_TIMEOUT = 300          # Idle time before requiring web user to login again


#############################################################################################
###  FUNCTIONS: #############################################################################

def dec_check_session(returnNoneSess=False):
#-------------------------------------------------------------------------------------------------
# Decorator to check if in valid session. If not, send the login page.
# Generates function that has session as first parameter.
#
    def param_dec(func):
        @wraps(func)
        def inner(*args, **kwargs):
            COOKIE_NAME = 'sid'
            sid = request.cookies.get(COOKIE_NAME)                                         # Get the session id from cookie (if there)
            sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, app.config['SESS_FILE_DIR']) # Create or get session object
            g.rootUrl = url_for('main') # Set global var g, accessible by templates, to the url for this func
            if not sess.Valid():
                if returnNoneSess:
                    return func(None, *args, **kwargs)
                return render_template('sessError.html', title='Field Prime Login',
                                       msg='Your session has timed out - please login again.')
            g.userName = sess.GetUser()
            return func(sess, *args, **kwargs)
        return inner
    return param_dec


def dbUserName(username):
#-----------------------------------------------------------------------
# Map username to the database username.
    return 'fp_' + username

def dbName(username):
#-----------------------------------------------------------------------
# Map username to the database name.
    return 'fp_' + username

def CheckPassword(user, password):
#-----------------------------------------------------------------------
# Validate user/password, returning boolean indicating success
#
    try:
        con = mdb.connect('localhost', dbUserName(user), password, dbName(user));
        return True
    except mdb.Error, e:
        return False


def FrontPage(sess, msg=''):
#-----------------------------------------------------------------------
# Return HTML Response for main user page after login
#
    sess.resetLastUseTime()    # This should perhaps be in dataPage, assuming it will only run immediately
                               # after login has been checked (i.e. can't click on link on page that's been
                               # been sitting around for a long time and have it prevent the timeout).
    return dataPage(sess, content=msg, title="User: " + sess.GetUser())


def TrialTraitTableHtml(trial):
#----------------------------------------------------------------------------------------------------
# Returns HTML for table showing all the traits for trial.
    if len(trial.traits) < 1:
        return "No traits configured"
    out = "<table border='1'>"
    out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(
        "Caption", "Description", "Type", "Details")
    for trt in trial.traits:
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(
            trt.caption, trt.description, TRAIT_TYPE_NAMES[trt.type])
        # Add "Detail" button for trait types with extra configuration:
        if trt.type == T_INTEGER or trt.type == T_DECIMAL:
            url = url_for('traitValidation', trialId=trial.id, traitId=trt.id,  _external=True)
            validateButton = HtmlButtonLink2("Details", url)
            out += "<td>" + validateButton  + "</td>"
    out += "</table>"
    return out


def TrialHtml(sess, trialId):
#-----------------------------------------------------------------------
# Returns the HTML for a top level page to display/manage a given trial.
#
    trial = dbUtil.GetTrial(sess, trialId)
    if trial is None: return None

    # Trial name and details:
    trialDetails = ''
    if trial.site: trialDetails += trial.site
    if trial.year:
        if trialDetails: trialDetails += ', ' + trial.year
        else: trialDetails += trial.year
    if trial.acronym:
        if trialDetails: trialDetails += ', ' + trial.acronym
        else: trialDetails += trial.acronym
    trialNameAndDetails = trial.name
    if trialDetails: trialNameAndDetails += ' (' + trialDetails + ')'
    r = "<p><h3>Trial {0}</h3>".format(trialNameAndDetails)

    # Attributes:
    attList = dbUtil.GetTrialAttributes(sess, trialId)
    def atts():
        if len(attList) < 1:
            return "No attributes found"
        out = "<ul>"
        for att in attList:
            out += "<li><a href={0}>{1}</a></li>".format(url_for("attributeDisplay", trialId=trialId, attId=att.id), att.name)
        out += "</ul>"
        out += '<p>' + fpUtil.HtmlButtonLink2("Upload attributes", url_for("attributeUpload", trialId=trialId))
        return out
    r += HtmlForm(HtmlFieldset(atts, "Attributes:"))

    # Traits:
    createTraitButton = '<p>' + fpUtil.HtmlButtonLink2("Create New Trait", url_for("newTrait", trialId=trialId))
    addSysTraitForm = '<FORM method="POST" action="{0}">'.format(url_for('addSysTrait2Trial', trialId=trialId))
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
    r += HtmlFieldset(HtmlForm(TrialTraitTableHtml(trial)) + createTraitButton + addSysTraitForm, "Traits:")

    # Trait Instances:
    tiList = dbUtil.GetTraitInstancesForTrial(sess, trialId)
    def tis():
        if len(tiList) < 1:
            return "No trait score sets yet"
        #out = "<ul>"
        out = ""
        #startIndex = 0
        #index = 0
        lastSeqNum = -1
        lastTraitId = -1
        lastToken = 'x'
        oneSet = []

        # func for use in loop below:
        def processGroup(oneSet):
            out = ""
            if len(oneSet) == 1:
                out += "<b>{1}:{2}&nbsp;&nbsp;</b><a href={0}>Single sample</a><p>".format(
                    url_for('traitInstance', traitInstanceId=oneSet[0].id), oneSet[0].trait.caption, oneSet[0].seqNum)
            else:
                out += "<b>{0}:{1}</b>".format(oneSet[0].trait.caption, oneSet[0].seqNum)
                out += '<ul>'
                for oti in oneSet:
                    out += "<li><a href={0}>&nbsp;Sample{1}</a></li>".format(
                        url_for('traitInstance', traitInstanceId=oti.id), oti.sampleNum)
                out += '</ul>'
            return out

        for ti in tiList:
            #++index
            traitId = ti.trait_id
            seqNum = ti.seqNum
            token = ti.token
            if lastSeqNum > -1 and (seqNum != lastSeqNum  or traitId != lastTraitId or token != lastToken):
                out += processGroup(oneSet)
                oneSet = []
            lastSeqNum = seqNum
            lastTraitId = traitId
            lastToken = token
            oneSet.append(ti)
        if lastSeqNum > -1:
            out += processGroup(oneSet)

        return out + "</ul>"
    r += HtmlForm(HtmlFieldset(tis, "Trait Score Sets:"))

    #============================================================================
    # Download data section:
    #

    # Javascript function to generate the href for the download links.
    # The generated link includes trialId and the user selected output options.
    # MFK, note we have problem with download link in that if the session has timed
    # out, the html for the login page will be downloaded instead of the actual data.
    # Could do a redirect? but have to pass all the params..
    #
    jscript = """
<script>
// func to set the href of the passed link to a URL for the trial data as plaintext tsv
function downloadURL() {{
    var tdms = document.getElementById('tdms');
    var out = '{0}?';
    // Add parameters indicating what to include in the download
    for (var i=0; i<tdms.length; i++)
        if (tdms[i].selected)
          out += '&' + tdms[i].value + '=1';
    return out;
}}
</script>
""".format(url_for("TrialDataTSV", trialId=trialId))

    dl = ""
    dl += jscript
    # Multi select output columns:
    dl += "Select columns to view/download:<br>"
    dl += "<select multiple id='tdms'>";
    dl += "<option value='timestamp' selected='selected'>Timestamps</option>";
    dl += "<option value='user' selected='selected'>User Idents</option>";
    dl += "<option value='gps' selected='selected'>GPS info</option>";
    dl += "<option value='notes' selected='selected'>Notes</option>";
    dl += "<option value='attributes' selected='selected'>Attributes</option>";
    dl += "</select>";
    dl += "<br><a href='dummy' onclick='this.href=downloadURL()'>"
    dl +=     "View tab separated score data (or right click and Save Link As to download)</a>"
    dl += "<br><a href='dummy' download='{0}.tsv' onclick='this.href=downloadURL()'>".format(trial.name)
    dl +=     "Download tab separated score data (browser permitting, Chrome and Firefox OK, IE not yet)</a>"
    dl += "<br>Note data is TAB separated"
    r += HtmlFieldset(dl, "Score Data:")

    return r


def dataNavigationContent(sess):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
    nc = "<h1>User {0}</h1>".format(sess.GetUser())
    nc += '<a href="{0}">Profile/Passwords</a>'.format(url_for('userDetails', userName=g.userName))
    nc += '<hr clear="all">'

    trials = GetTrials(sess)
    trialListHtml = "No trials yet" if len(trials) < 1 else ""
    for t in trials:
        trialListHtml += "<li><a href={0}>{1}</a></li>".format(url_for("showTrial", trialId=t.id), t.name)
    nc += "<h2>Trials:</h2>"
    nc += trialListHtml + HtmlButtonLink("Create New Trial", url_for("newTrial"))
    nc += '<hr>'
    nc += HtmlButtonLink("Download app", url_for("downloadApp"))
    nc += '<hr>'
    nc += '<a href="{0}">System Traits</a>'.format(url_for('systemTraits', userName=g.userName))
    return nc


def dataPage(sess, title, content):
#----------------------------------------------------------------------------
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
#
    nc = dataNavigationContent(sess)
    return render_template('dataPage.html', navContent=nc, content=content, title=title)

def dataTemplatePage(sess, template, **kwargs):
#----------------------------------------------------------------------------
# Return page for user data with given template, kwargs are passed through
# to the template. The point of this function is to add the navigation content.
#
    nc = dataNavigationContent(sess) # Generate content for navigation bar:
    return render_template(template, navContent=nc, **kwargs)


def trialPage(sess, trialId):
#----------------------------------------------------------------------------
# Return response that is the main page for specified file, or error message.
#
    trialh = TrialHtml(sess, trialId)
    if trialh is None:
        trialh = "No such trial"
    return dataPage(sess, content=trialh, title='Trial Data')


@app.route('/trial/<trialId>', methods=["GET"])
@dec_check_session()
def showTrial(sess, trialId):
#===========================================================================
# Page to display/modify a single trial.
#
    return trialPage(sess, trialId)


def AddSysTrialTrait(sess, trialId, traitId):
#-----------------------------------------------------------------------
# Return error string, None for success
#
    if traitId == "0":
        return "Select a system trait to add"
    try:
        usrname = dbUserName(sess.GetUser())
        usrdb = dbName(sess.GetUser())
        con = mdb.connect('localhost', usrname, sess.GetPassword(), usrdb)
        cur = con.cursor()
        cur.execute("insert into trialTrait (trial_id, trait_id) values (%s, %s)", (trialId, traitId))
        cur.close()
        con.commit()
    except mdb.Error, e:
        return  usrdb + " " + qry
    return None


# Could put all trait type specific stuff in trait extension classes.
# Aiming for this file to not contain any type specific code.
# class pTrait(models.Trait):
#     def ProcessForm(form):
#         pass

def allowed_file(filename):  # MFK cloned code warning
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def NewTraitCategorical(sess, request, newTrait):
    capKeys = [key for key in request.form.keys() if key.startswith("caption_")]
    for key in capKeys:
        caption = request.form.get(key)
        value = request.form.get(key.replace("caption_", "value_"))
        imageURL = None
        imageURLFile = request.files[key.replace("caption_", "imgfile_")]
        if imageURLFile:
            sentFilename = secure_filename(imageURLFile.filename)
            if allowed_file(sentFilename):
                subpath = os.path.join(app.config['CATEGORY_IMAGE_FOLDER'], sess.GetUser(), str(newTrait.id))
                if not os.path.exists(subpath):
                    os.makedirs(subpath)
                imageURLFile.save(subpath +  "/" + sentFilename)
                imageURL = app.config['CATEGORY_IMAGE_URL_BASE'] + sess.GetUser() + "/" + str(newTrait.id) + "/" + sentFilename
            else:
                pass  # should issue a warning perhaps?

        # Add new trait category:
        ncat = models.TraitCategory()
        ncat.value = value
        ncat.caption = caption
        ncat.trait_id = newTrait.id
        ncat.imageURL = imageURL
        sess.DB().add(ncat)

def CreateNewTrait(sess,  trialId, request):
#-----------------------------------------------------------------------
# Create trait in db, from data from html form.
# trialId is id of trial if a local trait, else it is 'sys'.
# Returns error message if there's a problem, else None.
#
    caption = request.form.get("caption")
    description = request.form.get("description")
    type = request.form.get("type")

    # This should be trait type specific (but min, max fields are in trait table):
    min = request.form.get("min")
    max = request.form.get("max")

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
        trial = dbUtil.GetTrialFromDBsess(sess, trialId)
        for x in trial.traits:
            if x.caption == caption:
                return 'Error: A local trait with this caption already exists'
        ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        ntrt.sysType = SYSTYPE_TRIAL
    else:  # If system trait, check there's no other system trait with same caption:
        sysTraits = dbUtil.GetSysTraits(sess)
        for x in sysTraits:
            if x.caption == caption:
                return 'Error: A system trait with this caption already exists'
        ntrt.sysType = SYSTYPE_SYSTEM

    ntrt.type = type
    if min:
        ntrt.min = min
    if max:
        ntrt.max = max

    dbsess.add(ntrt)
    dbsess.commit()

    # Trait type specific processing:
    if int(ntrt.type) == dal.TRAIT_TYPE_TYPE_IDS['Categorical']:
        NewTraitCategorical(sess, request, ntrt)
    elif int(ntrt.type) == dal.TRAIT_TYPE_TYPE_IDS['Integer']:
        pass

    dbsess.add(ntrt)
    dbsess.commit()
    return None


@app.route('/downloadApp/', methods=['GET'])
@dec_check_session()
def downloadApp(sess):
#-----------------------------------------------------------------------
# Display page for app download.
# Provide a link for each .apk file in the static/apk folder
#
    from fnmatch import fnmatch
    apkDir = app.root_path + '/static/apk'
    apkListHtml = 'To download the app, right click on a link and select "Save Link As":'
    l = os.listdir(apkDir)
    for fname in l:
        if fnmatch(fname, '*.apk'):
            apkListHtml += '<p><a href="{0}">{1}</a>'.format(url_for('static', filename = 'apk/'+fname), fname)
    return dataPage(sess, content=apkListHtml, title='Download App')


@app.route('/trial/<trialId>/data/', methods=['GET'])
@dec_check_session()
def TrialDataTSV(sess, trialId):
#-----------------------------------------------------------------------
# Returns trial data as plain text tsv form - i.e. for download.
# The data is arranged in trial unit rows, and trait instance value and attribute
# columns.
#
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    SEP = '\t'
    # Get Trait Instances:
    tiList = dbUtil.GetTraitInstancesForTrial(sess, trialId)

    # Work out number of columns for each trait instance:
    numColsPerValue = 1
    if showTime:
        numColsPerValue += 1
    if showUser:
        numColsPerValue += 1
    if showGps:
        numColsPerValue += 2
    if showNotes:
        numColsPerValue += 1         # MFK NOTE this will need to be removed when we deprecate datum notes

    # Headers:
    r = "Row" + SEP + "Column"
    if showAttributes:
        trl = dbUtil.GetTrial(sess, trialId)
        for tua in trl.tuAttributes:
            r += SEP + tua.name
    for ti in tiList:
        tiName = "{0}_{1}.{2}.{3}".format(ti.trait.caption, ti.dayCreated, ti.seqNum, ti.sampleNum)
        r += "{1}{0}".format(tiName, SEP)
        if showTime:
            r += "{1}{0}_timestamp".format(tiName, SEP)
        if showUser:
            r += "{1}{0}_user".format(tiName, SEP)
        if showGps:
            r += "{1}{0}_latitude{1}{0}_longitude".format(tiName, SEP)
        if showNotes:
            r += SEP + "{0}.notes".format(tiName)
    if showNotes:
        r += SEP + "Notes"  # Putting notes at end in case some commas slip thru and mess up csv structure
    r += '\n'

    # Data:
    tuList = dbUtil.GetTrialUnits(sess, trialId)
    for tu in tuList:
        # Row and Col:
        r += "{0}{2}{1}".format(tu.row, tu.col, SEP)

        # Attribute Columns:
        if showAttributes:
            for tua in trl.tuAttributes:
                r += SEP
                av = dbUtil.getAttributeValue(sess, tu.id, tua.id)
                if av is not None:
                    r += av.value

        # Scores:
        for ti in tiList:
            type = ti.trait.type
            datums = dbUtil.GetDatum(sess, tu.id, ti.id)
            if len(datums) == 0:  # Handle case where no datum:
                r += SEP * numColsPerValue
            else:  # Data present
                # There probably shouldn't be multiple, but if there is, we use the most recent.
                # Could remove this when/if sure that it's one or zero datums.
                lastDatum = datums[0]
                for d in datums:
                    if d.timestamp > lastDatum.timestamp: lastDatum = d
                d = lastDatum

                # Write the value:
                r += "{0}{1}".format(SEP, d.getValue())
                # Write any other datum fields specified:
                if showTime:
                    r += "{0}{1}".format(SEP, d.timestamp)
                if showUser:
                    r += "{0}{1}".format(SEP, d.userid)
                if showGps:
                    r += "{0}{1}{0}{2}".format(SEP, d.gps_lat, d.gps_long)
                if showNotes:
                    r += SEP
                    if d.notes != None and len(d.notes) > 0: r += d.notes  ######### MFK move old notes, discontinue support!

        # Notes, as list separated by pipe symbols:
        if showNotes:
            r += SEP + '"'
            tuNotes = dbUtil.GetTrialUnitNotes(sess, tu.id)
            for note in tuNotes:
                r += '{0}|'.format(note.note)
            r += '"'

        # End the line:
        r += "\n"

    return Response(r, content_type='text/plain')

@app.route('/newTrial/', methods=["GET", "POST"])
@dec_check_session()
def newTrial(sess):
#===========================================================================
# Page for trial creation.
#
    if request.method == 'GET':
        return dataTemplatePage(sess, 'newTrial.html', title='Create Trial')
    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.uploadTrialFile(sess, uploadFile, request.form.get('name'), request.form.get('site'),
                                      request.form.get('year'), request.form.get('acronym'))
        if res is not None and 'error' in res:
            return dataTemplatePage(sess, 'newTrial.html', title='Create Trial', msg = res['error'])
        else:
            return FrontPage(sess)

@app.route('/trial/<trialId>/newTrait/', methods=["GET", "POST"])
@dec_check_session()
def newTrait(sess, trialId):
#===========================================================================
# Page for trait creation.
#
    if request.method == 'GET':
        # NB, could be a new sys trait, or trait for a trial. Indicated by trialId which will be
        # either 'sys' or the trial id respectively.
        return dataTemplatePage(sess, 'newTrait.html', trialId=trialId, traitTypes=TRAIT_TYPE_TYPE_IDS, title='New Trait')

    if request.method == 'POST':
        errMsg = CreateNewTrait(sess, trialId, request)
        if errMsg:
            return dataPage(sess, content=errMsg, title='Error')
        if trialId == 'sys':
            return FrontPage(sess, 'System trait created')
        return trialPage(sess, trialId)

@app.route('/trial/<trialId>/trait/<traitId>', methods=['GET', 'POST'])
@dec_check_session()
def traitValidation(sess, trialId, traitId):
#===========================================================================
# Page to display/modify validation parameters for a trait.
# Currently only relevant for integer traits.
#
    trial = dbUtil.GetTrial(sess, trialId)
    trt = dbUtil.GetTrait(sess, traitId)
    title = 'Trial: ' + trial.name + ', Trait: ' + trt.caption
    comparatorCodes = [
        ["gt", "Greater Than", 1],
        ["ge", "Greater Than or Equal to", 2],
        ["lt", "Less Than", 3],
        ["le", "Less Than or Equal to", 4]
    ]

    if request.method == 'GET':  #xxx
        if trt.type == T_INTEGER:
            #
            # Generate form on the fly. Could use template but there's lots of variables.
            #
            tti = models.GetTrialTraitIntegerDetails(sess.DB(), traitId, trialId)
            # xxx need to get decimal version if decimal. Maybe make tti type have getMin/getMax func and use for both types
            minText = ""
            if tti and tti.min is not None:
                minText = "value='{0}'".format(tti.min)
            maxText = ""
            if tti and tti.max is not None:
                maxText = "value='{0}'".format(tti.max)
            minMaxBounds = "<p>Minimum: <input type='text' name='min' {0}>".format(minText)
            minMaxBounds += "<p>Maximum: <input type='text' name='max' {0}><br>".format(maxText);

            # Parse condition string, if present, to retrieve comparator and attribute.
            # Format of the string is: ^. <2_char_comparator_code> att:<attribute_id>$
            # The only supported comparison at present is comparing the score to a
            # single attribute.
            # NB, this format needs to be in sync with the version on the app. I.e. what
            # we save here, must be understood on the app.
            atId = -1
            op = ""
            if tti and tti.cond is not None:
                tokens = tti.cond.split()  # [["gt", "Greater than", 0?], ["ge"...]]?
                if len(tokens) != 3:
                    return "bad condition: " + tti.cond
                op = tokens[1]
                atClump = tokens[2]
                atId = int(atClump[4:])

            # Show available comparison operators:
            valOp = '<select name="validationOp">'
            valOp += '<option value="0">&lt;Choose Comparator&gt;</option>'
            for c in comparatorCodes:
                valOp += '<option value="{0}" {2}>{1}</option>'.format(
                    c[2], c[1], 'selected="selected"' if op == c[0] else "")
            valOp += '</select>'

            # Attribute list:
            attListHtml = '<select name="attributeList">'
            attListHtml += '<option value="0">&lt;Choose Attribute&gt;</option>'
            atts = dbUtil.GetTrialAttributes(sess, trialId)
            for att in atts:
                if att.datatype == T_INTEGER:  # xxx restrict to integer attributes
                    attListHtml += '<option value="{0}" {2}>{1}</option>'.format(
                        att.id, att.name, "selected='selected'" if att.id == atId else "")
            attListHtml += '</select>'

            conts = 'Trial: ' + trial.name
            conts += '<br>Trait: ' + trt.caption
            conts += '<br>Type: ' + TRAIT_TYPE_NAMES[trt.type]
            conts += minMaxBounds
            conts += '<p>Integer traits can be validated by comparison with an attribute:'
            conts += '<br>Trait value should be ' + valOp + attListHtml
            conts += '<p><input type="button" style="color:red" value="Cancel" onclick="history.back()"><input type="submit" style="color:red" value="Submit">'

            return dataPage(sess, content=HtmlForm(conts, post=True), title='Trait Validation')
        elif trt.type == T_INTEGER or trt.type == T_DECIMAL:  #mfk clone of above, remove above when numeric works for integer.
            #
            # Generate form on the fly. Could use template but there's lots of variables.
            # Make this a separate function to generate html form, so can be used from
            # trait creation page.
            #
            ttn = models.GetTrialTraitNumericDetails(sess.DB(), traitId, trialId)

            # Min and Max:
            # need to get decimal version if decimal. Maybe make ttn type have getMin/getMax func and use for both types
            minText = ""
            if ttn and ttn.min is not None:
                minText = "value='{0}'".format(ttn.getMin())
            maxText = ""
            if ttn and ttn.max is not None:
                maxText = "value='{0}'".format(ttn.getMax())
            minMaxBounds = "<p>Minimum: <input type='text' name='min' {0}>".format(minText)
            minMaxBounds += "<p>Maximum: <input type='text' name='max' {0}><br>".format(maxText);

            # Parse condition string, if present, to retrieve comparator and attribute.
            # Format of the string is: ^. <2_char_comparator_code> att:<attribute_id>$
            # The only supported comparison at present is comparing the score to a
            # single attribute.
            # NB, this format needs to be in sync with the version on the app. I.e. what
            # we save here, must be understood on the app.
            atId = -1
            op = ""
            if ttn and ttn.cond is not None:
                tokens = ttn.cond.split()  # [["gt", "Greater than", 0?], ["ge"...]]?
                if len(tokens) != 3:
                    return "bad condition: " + ttn.cond
                op = tokens[1]
                atClump = tokens[2]
                atId = int(atClump[4:])

            # Show available comparison operators:
            valOp = '<select name="validationOp" id="tdCompOp">'
            valOp += '<option value="0">&lt;Choose Comparator&gt;</option>'
            for c in comparatorCodes:
                valOp += '<option value="{0}" {2}>{1}</option>'.format(
                    c[2], c[1], 'selected="selected"' if op == c[0] else "")
            valOp += '</select>'

            # Attribute list:
            attListHtml = '<select name="attributeList" id="tdAttribute">'
            attListHtml += '<option value="0">&lt;Choose Attribute&gt;</option>'
            atts = dbUtil.GetTrialAttributes(sess, trialId)
            for att in atts:
                if att.datatype == T_DECIMAL:  # xxx restrict to decimal attributes
                    attListHtml += '<option value="{0}" {2}>{1}</option>'.format(
                        att.id, att.name, "selected='selected'" if att.id == atId else "")
            attListHtml += '</select>'

            # javascript to check that if one of comp and att chosen both are:
            script = """
                <script>
                function validateTraitDetails() {
                    //alert("hallo");
                    //return false;

                    var att = document.getElementById("tdAttribute").value;
                    var comp = document.getElementById("tdCompOp").value;

                    var attPresent = (att === null || att === "");
                    //alert(attPresent ? "att yes" : "att no");
                    //return false;

                    var compPresent = (comp === null || comp === "");
                    if (attPresent && !compPresent) {
                        alert("Attribute selected with no comparitor specified, please fix.");
                        return false;
                    }
                    if (!attPresent && compPresent) {
                        alert("Comparitor selected with no attibute specified, please fix.");
                        return false;
                    }
                    return true;
                }
                </script>
            """

            conts = 'Trial: ' + trial.name
            conts += '<br>Trait: ' + trt.caption
            conts += '<br>Type: ' + TRAIT_TYPE_NAMES[trt.type]
            conts += minMaxBounds
            conts += '<p>Integer traits can be validated by comparison with an attribute:'
            conts += '<br>Trait value should be ' + valOp + attListHtml
            # MFK why the history.back?
            #conts += '<p><input type="button" style="color:red" value="Cancel" onclick="history.back()"><input type="submit" style="color:red" value="Submit">'
            conts += '<p><input type="button" style="color:red" value="Cancel"><input type="submit" style="color:red" value="Submit">'

            return dataPage(sess, content=script + HtmlForm(conts, post=True, onsubmit='return validateTraitDetails()'), title='Trait Validation')

        return dataPage(sess, content='No validation for this trait type', title=title)
    if request.method == 'POST':
        if trt.type == T_INTEGER:
            op = request.form.get('validationOp')
            # if op == "0":
            #     return "please choose a comparator" mfk now javascript? No but we need js check that if one of comp and att chosen both are.
            at = request.form.get('attributeList')
            # if int(at) == 0:
            #     return "please choose an attribute"
            vmin = request.form.get('min')
            if len(vmin) == 0:
                vmin = None
            vmax = request.form.get('max')
            if len(vmax) == 0:
                vmax = None
            # Get existing trialTraitInteger, if any.
            tti = models.GetTrialTraitIntegerDetails(sess.DB(), traitId, trialId)
            newTTI = tti is None
            if newTTI:
                tti = models.TrialTraitInteger()
            tti.trial_id = trialId
            tti.trait_id = traitId
            tti.min = vmin
            tti.max = vmax
            if int(op) > 0 and int(at) > 0:
                tti.cond = ". " + comparatorCodes[int(op)-1][0] + ' att:' + at
            if newTTI:
                sess.DB().add(tti)
            sess.DB().commit()
            return trialPage(sess, trialId)
        if trt.type == T_INTEGER or trt.type == T_DECIMAL: # clone of above remove above when integer works with numeric
            op = request.form.get('validationOp')
            # if op == "0":
            #     return "please choose a comparator" mfk now javascript? No but we need js check that if one of comp and att chosen both are.
            at = request.form.get('attributeList')
            vmin = request.form.get('min')
            if len(vmin) == 0:
                vmin = None
            vmax = request.form.get('max')
            if len(vmax) == 0:
                vmax = None
            # Get existing trialTraitInteger, if any.
            ttn = models.GetTrialTraitNumericDetails(sess.DB(), traitId, trialId)
            newTTN = ttn is None
            if newTTN:
                ttn = models.TrialTraitNumeric()
            ttn.trial_id = trialId
            ttn.trait_id = traitId
            ttn.min = vmin
            ttn.max = vmax
            if int(op) > 0 and int(at) > 0:
                ttn.cond = ". " + comparatorCodes[int(op)-1][0] + ' att:' + at
            if newTTN:
                sess.DB().add(ttn)
            sess.DB().commit()
            return trialPage(sess, trialId)

@app.route('/trial/<trialId>/uploadAttributes/', methods=['GET', 'POST'])
@dec_check_session()
def attributeUpload(sess, trialId):
    if request.method == 'GET':
        return dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes')

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.updateTrialFile(sess, uploadFile, trialId)
        if res is not None and 'error' in res:
            return dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes', msg = res['error'])
        else:
            return trialPage(sess, trialId) #FrontPage(sess)

@app.route('/trial/<trialId>/attribute/<attId>/', methods=['GET'])
@dec_check_session()
def attributeDisplay(sess, trialId, attId):
    tua = dbUtil.GetAttribute(sess, attId)
    r = "Attribute {0}".format(tua.name)
    r += "<br>Datatype : " + TRAIT_TYPE_NAMES[tua.datatype]
    r += "<p><table border='1'>"
    r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format("Row", "Column", "Value")
    aVals = dbUtil.GetAttributeValues(sess, attId)
    for av in aVals:
        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(av.trialUnit.row, av.trialUnit.col, av.value)
    r += "</table>"
    return dataPage(sess, content=r, title='Attribute')


@app.route('/user/<userName>/details/', methods=['GET', 'POST'])
@dec_check_session()
def userDetails(sess, userName):
    title = "Profile"
    if request.method == 'GET':
        cname = dbUtil.getSystemValue(sess, 'contactName') or ''
        cemail = dbUtil.getSystemValue(sess, 'contactEmail') or ''
        return dataTemplatePage(sess, 'profile.html', contactName=cname, contactEmail=cemail, title=title)
    if request.method == 'POST':
        op = request.args.get('op')
        form = request.form
        if op == 'contact':
            contactName = form.get('contactName')
            contactEmail = form.get('contactEmail')
            if not (contactName and contactEmail):
                return dataTemplatePage(sess, 'profile.html', op=op, errMsg="Please fill out all fields", title=title)
            else:
                dbUtil.setSystemValue(sess, 'contactName', contactName)
                dbUtil.setSystemValue(sess, 'contactEmail', contactEmail)
                return dataTemplatePage(sess, 'profile.html', op=op, contactName=contactName, contactEmail=contactEmail,
                                        errMsg="Contact details saved", title=title)

        suser = form.get("login")
        password = form.get("password")
        newpassword1 = form.get("newpassword1")
        newpassword2 = form.get("newpassword2")
        if not (suser and password and newpassword1 and newpassword2):
            return dataTemplatePage(sess, 'profile.html', op=op, errMsg="Please fill out all fields", title=title)
        if newpassword1 != newpassword2:
            return dataTemplatePage(sess, 'profile.html', op=op, errMsg="Versions of new password do not match.", title=title)
        if not CheckPassword(suser, password):
            sess.close()
            return render_template('sessError.html', msg="Password is incorrect", title='FieldPrime Login')

        # OK, all good, change their password:
        try:
            usrname = dbUserName(suser)
            usrdb = dbName(suser)
            con = mdb.connect('localhost', usrname, password, usrdb)
            cur = con.cursor()
            msg = ''
            if op == 'newpw':
                cur.execute("set password for %s@localhost = password(%s)", (usrname, newpassword1))
                sess.SetUserDetails(suser, newpassword1)
                msg = 'Admin password reset successfully'
            elif op == 'setAppPassword':
                cur.execute("REPLACE system set name = 'appPassword', value = %s", newpassword1)
                con.commit()
                msg = 'Scoring password reset successfully'
            con.close()
            return FrontPage(sess, msg)
        except mdb.Error, e:
            sess.close()
            return render_template('sessError.html', msg="Unexpected error trying to change password", title='FieldPrime Login')


@app.route('/user/<userName>/systemTraits/', methods=['GET', 'POST'])
@dec_check_session()
def systemTraits(sess, userName):
#---------------------------------------------------------------------------
#
#
    if request.method == 'GET':
        # System Traits:
        sysTraits = GetSysTraits(sess)
        sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else fpTrait.TraitListHtmlTable(sysTraits)
        r = HtmlFieldset(
            HtmlForm(sysTraitListHtml) + HtmlButtonLink("Create New System Trait", url_for("newTrait", trialId='sys')),
            "System Traits")
        return dataPage(sess, title='System Traits', content=r)


@app.route('/trial/<trialId>/addSysTrait2Trial/', methods=['POST'])
@dec_check_session()
def addSysTrait2Trial(sess, trialId):
    errMsg = AddSysTrialTrait(sess, trialId, request.form['traitID'])
    if errMsg:
        return dataPage(sess, content=errMsg, title='Error')
    # If all is well, display the trial page:
    return trialPage(sess, trialId)

@app.route('/scoreSet/<traitInstanceId>/', methods=['GET'])
@dec_check_session()
def traitInstance(sess, traitInstanceId):
#-----------------------------------------------------------------------
# Display the data for specified trait instance.
# MFK this should probably display RepSets, not individual TIs
#
    ti = dbUtil.getTraitInstance(sess, traitInstanceId)
    typ = ti.trait.type
    name = ti.trait.caption + '_' + str(ti.seqNum) + ' sample ' + str(ti.sampleNum) # MFK add name() to TraitInstance
    data = sess.DB().query(models.Datum).filter(models.Datum.traitInstance_id == traitInstanceId).all()
    r = "Score Set: {0}".format(name)
    #r += "<br>Datatype : " + TRAIT_TYPE_NAMES[tua.datatype]

    r += "<p><table border='1'>"
    r += "<tr><td>Row</td><td>Column</td><td>Timestamp</td><td>Value</td></tr>"
    for d in data:
        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(
            d.trialUnit.row, d.trialUnit.col, d.timestamp, d.getValue())
    r += "</table>"
    return dataPage(sess, content=r, title='Score Set Data')


# def TraitInstanceHtml(sess, tiId):
# #-----------------------------------------------------------------------
# # Returns html for data for specified trait instance.
# #
#     data = sess.DB().query(models.Datum).filter(models.Datum.traitInstance_id == tiId).all()
#     r = "Row Column Timestamp numValue textValue<br>"
#     for d in data:
#         r += "{0} {1} {2} {3} {4}<br>".format(d.trialUnit.row, d.trialUnit.col, d.timestamp, d.numValue, d.txtValue)
#     return r


@app.route('/user/<userName>/', methods=['GET'])
@dec_check_session()
def userHome(sess, userName):
    return FrontPage(sess)

@app.route('/logout', methods=["GET"])
@dec_check_session()
def logout(sess):
    sess.close()
    return redirect(url_for('main'))

@app.route('/info/<pagename>', methods=["GET"])
@dec_check_session(True)
def infoPage(sess, pagename):
    g.rootUrl = url_for('main')
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)

@app.route('/', methods=["GET", "POST"])
def main():
#-----------------------------------------------------------------------
# Entry point for FieldPrime web admin.
# As a GET it presents a login screen.
# As a POST it process the login data.
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
# necessary, eg for traitInstance, which doesn't need it since the TI id is unique within db.
# Or perhaps it should be /user/userName/[trial/trialId]/
#
# Might want to change displayed url for some things eg the op to change password ends up displaying
# the FrontPage, but shows the URL for the op.
#
    COOKIE_NAME = 'sid'
    sid = request.cookies.get(COOKIE_NAME)                # Get the session id from cookie (if there)
    sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, app.config['SESS_FILE_DIR'])     # Create session object (may be existing session)
    g.rootUrl = url_for(sys._getframe().f_code.co_name)   # Set global variable accessible by templates (to the url for this func)
    g.userName = 'unknown'
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
            # Good to go, show the user front page, after adding cookie:
            sess.resetLastUseTime()
            sess.SetUserDetails(username, password)
            g.userName = username
            resp = make_response(FrontPage(sess))
            resp.set_cookie(COOKIE_NAME, sess.sid())      # Set the cookie
            return resp
        return render_template('sessError.html', msg=error, title='FieldPrime Login')

    # Request method is 'GET':
    return infoPage('fieldprime')


##############################################################################################################


def LogDebug(hdr, text):
#-------------------------------------------------------------------------------------------------
# Writes stuff to file system (for debug) - not routinely used..
    f = open('/tmp/fieldPrimeDebug','a')
    print >>f, "--- " + hdr + ": ---"
    print >>f, text
    print >>f, "------------------"
    f.close


# For local testing:
if __name__ == '__main__':
    from os.path import expanduser
    app.config['SESS_FILE_DIR'] = expanduser("~") + '/proj/fpserver/fpa/fp_web_admin/tmp2'
    app.run(debug=True, host='0.0.0.0', port=5001)

