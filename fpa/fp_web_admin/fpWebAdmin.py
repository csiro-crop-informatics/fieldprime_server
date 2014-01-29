# fpApi.py
# Michael Kirk 2013
# 
#

import os, sys, time
import MySQLdb as mdb
from flask import Flask, request, Response, url_for, render_template, g, make_response
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

LOGIN_TIMEOUT = 300            # Idle time before requiring web user to login again


#############################################################################################
###  FUNCTIONS: #############################################################################

def dec_check_session():
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
                return render_template('login.html', title='Field Prime Login')
            g.userName = sess.GetUser()
            return func(sess, *args, **kwargs)
        return inner
    return param_dec


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
    sess.resetLastUseTime()

    # Administer passwords button:
    r = "<p>" + HtmlButtonLink("Administer Passwords", url_for('userDetails', userName=g.userName))

    # Download app button:
    r += "<p>" + HtmlButtonLink("Download app", url_for("downloadApp"))

    # Traits:
    trials = GetTrials(sess)
    trialListHtml = "No trials yet" if len(trials) < 1 else ""
    for t in trials:
        trialListHtml += "<li><a href={0}>{1}</a></li>".format(url_for("showTrial", trialId=t.id), t.name)

    r += HtmlFieldset(HtmlForm(trialListHtml)
                      + HtmlButtonLink("Create New Trial", url_for("newTrial")), "Current Trials")

    # System Traits:
    sysTraits = GetSysTraits(sess)
    #from fp_common.fpTrait import TraitListHtmlTable
    sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else fpTrait.TraitListHtmlTable(sysTraits)
    r += HtmlFieldset(
        HtmlForm(sysTraitListHtml) + HtmlButtonLink("Create New System Trait", url_for("newTrait", trialId='sys')),
        "System Traits")

    return make_response(render_template('genericPage.html', content=r, title="User: " + sess.GetUser()))


def TrialTraitTableHtml(trial):
#----------------------------------------------------------------------------------------------------
    if len(trial.traits) < 1:
        return "No traits configured"
    out = "<table border='1'>"
    out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(
        "Caption", "Description", "Type", "Validation")
    for trt in trial.traits:
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(
            trt.caption, trt.description, TRAIT_TYPE_NAMES[trt.type])
        if trt.type == 0:
            valOp = '<select name="validationOp">'
            valOp += '<option value="0">Greater Than</option>'
            valOp += '<option value="0">Less Than</option>'
            valOp += '</select>'

            url = url_for('traitValidation', trialId=trial.id, traitId=trt.id,  _external=True)
            validateButton = HtmlButtonLink2("Validation", url) 
            out += "<td>" + validateButton  + "</td>"
    out += "</table>"
    return out


def TrialHtml(sess, trialId):
#-----------------------------------------------------------------------
# Top level page to display/manage a given trial.
#
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
            out += "<li><a href={0}>{1}</a></li>".format(url_for("attributeDisplay", trialId=trialId, attId=att.id), att.name)
            #out += "<li><a href={0}>{1}</a></li>".format("fred", att.name)
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
            return "No trait instances found"
        #out = "<ul>"
        out = ""
        #startIndex = 0
        #index = 0
        lastSeqNum = -1
        lastTraitId = -1
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
            if lastSeqNum > -1 and (seqNum != lastSeqNum  or traitId != lastTraitId):
                out += processGroup(oneSet)
                oneSet = []
            lastSeqNum = seqNum
            lastTraitId = traitId
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
    jscript = """
<script>
function tdSelect() {{
    var tdms = document.getElementById('tdms');
    var out = '{0}?';
    for (var i=0; i<tdms.length; i++)
        if (tdms[i].selected)
          out += '&' + tdms[i].value + '=1';
    return out;
}}
</script>
""".format(url_for("TrialDataHtml", trialId=trialId))
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
    dl += "<br><a href='dummy' onclick='this.href=tdSelect()'>View tab separated score data (or right click and Save Link As to download)</a>".format(trial.name)
    dl += "<br><a href='dummy' download='{0}.tsv' onclick='this.href=tdSelect()'>Download tab separated score data (browser permitting)</a>".format(trial.name)
    dl += "<br>Note data is TAB separated"
    r += HtmlFieldset(dl, "Score Data:")

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


def LoginForm(msg):
#-----------------------------------------------------------------------
# login form 
    return render_template('login.html', msg = msg, title='Field Prime Login')


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
#
    return render_template('downloadApp.html', title='Download')


@app.route('/trial/<trialId>/data/', methods=['GET'])
@dec_check_session()
def TrialDataHtml(sess, trialId):
#-----------------------------------------------------------------------
# Returns trial data as plain text csv form - i.e. for download.
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
                av = dbUtil.GetAttributeValue(sess, tu.id, tua.id)
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
                # This next switch is no good, have to support trait type polymorphism somehow..
                if type == T_INTEGER: value = d.numValue
                if type == T_DECIMAL: value = d.numValue
                if type == T_STRING: value = d.txtValue
                if type == T_CATEGORICAL:
                    value = d.numValue
                    # Need to look up the text for the value:
                    if value is not None:
                        value = dbUtil.GetTraitCategory(sess,ti.trait.id , value).caption
                        # MFK what if image trait? perhaps need ID? note caption cannot be null so ok?
                if type == T_DATE: value = d.numValue
                if type == T_PHOTO: value = d.txtValue
                # Convert None to "NA"
                if value is None:
                    value = "NA"
                #if type == T_LOCATION: value = d.txtValue
                # Write the value:
                r += "{0}{1}".format(SEP, value)
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
        return render_template('newTrial.html', title='Create Trial')
    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.UploadTrialFile(sess, uploadFile, request.form.get('name'), request.form.get('site'), 
                                      request.form.get('year'), request.form.get('acronym'))
        if res is not None and 'error' in res:
            return render_template('newTrial.html', title='Create Trial', msg = res['error'])
        else:
            return FrontPage(sess)

@app.route('/trial/<trialId>/newTrait/', methods=["GET", "POST"])
@dec_check_session()
def newTrait(sess, trialId):
#===========================================================================
# Page for trial creation.
#
    if request.method == 'GET':
        # NB, could be a new sys trait, or trait for a trial. Indicated by tid which will be
        # either 'sys' or the trial id respectively.
        return render_template('newTrait.html', trialId = trialId,
                               traitTypes = TRAIT_TYPE_TYPE_IDS, title='New Trait')
    if request.method == 'POST':
        errMsg = CreateNewTrait(sess, trialId, request)
        if errMsg:
            return render_template('genericPage.html', content=errMsg, title='Error')
        if trialId == 'sys':
            return FrontPage(sess)
        return render_template('genericPage.html', content=TrialHtml(sess, trialId), title='Trial Data')


@app.route('/trial/<trialId>', methods=["GET"])
@dec_check_session()
def showTrial(sess, trialId):
#===========================================================================
# Page to display/modify a single trial.
#
    return render_template('genericPage.html', content=TrialHtml(sess, trialId), title='Trial Data')


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

    if request.method == 'GET':
        if trt.type == 0:
            tti = models.GetTrialTraitIntegerDetails(sess.DB(), traitId, trialId)
            minText = ""
            if tti and tti.min is not None:
                minText = "value='{0}'".format(tti.min)
            maxText = ""
            if tti and tti.max is not None:
                maxText = "value='{0}'".format(tti.max)
            bounds = "<p>Minimum: <input type='text' name='min' {0}>".format(minText)
            bounds += "<p>Maximum: <input type='text' name='max' {0}><br>".format(maxText);

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
                if att.datatype == T_INTEGER:  # restrict to integer attributes
                    attListHtml += '<option value="{0}" {2}>{1}</option>'.format(
                        att.id, att.name, "selected='selected'" if att.id == atId else "")
            attListHtml += '</select>'

            conts = 'Trial: ' + trial.name
            conts += '<br>Trait: ' + trt.caption
            conts += '<br>Type: ' + TRAIT_TYPE_NAMES[trt.type]
            conts += bounds
            conts += '<p>Integer traits can be validated by comparison with an attribute:'
            conts += '<br>Trait value should be ' + valOp + attListHtml
            conts += '<p><input type="button" style="color:red" value="Cancel" onclick="history.back()"><input type="submit" style="color:red" value="Submit">'

            return render_template('genericPage.html', content=HtmlForm(conts, post=True), title='Trait Validation')
        return render_template('genericPage.html', content='No validation for this trait type', title=title)
    if request.method == 'POST':
        op = request.form.get('validationOp')
        # if op == "0":
        #     return "please choose a comparator"
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
        return render_template('genericPage.html', content=TrialHtml(sess, trialId), title='Trial Data')

@app.route('/trial/<trialId>/uploadAttributes/', methods=['GET', 'POST'])
@dec_check_session()
def attributeUpload(sess, trialId):
    if request.method == 'GET':
        return render_template('uploadAttributes.html', content=TrialHtml(sess, trialId), title='Load Attributes')
    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.UpdateTrialFile(sess, uploadFile, trialId)
        if res is not None and 'error' in res:
            return render_template('uploadAttributes.html', title='Load Attributes', msg = res['error'])
        else:
            return FrontPage(sess)

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
    return render_template('genericPage.html', content=r, title='Attribute')


@app.route('/user/<userName>/details/', methods=['GET', 'POST'])
@dec_check_session()
def userDetails(sess, userName):
    if request.method == 'GET':
        return AdminForm(sess)
    if request.method == 'POST':
        op = request.args.get('op')
        return ProcessAdminForm(sess, op, request.form)


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
<font color="red">{1}</font>
""".format(url_for('userDetails', userName=g.userName), adminMsg)
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
<font color="red">{1}</font>
""".format(url_for('userDetails', userName=g.userName), appMsg)
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

@app.route('/trial/<trialId>/addSysTrait2Trial/', methods=['POST'])
@dec_check_session()
def addSysTrait2Trial(sess, trialId):
    errMsg = AddSysTraitTrial(sess, trialId, request.form['traitID'])
    if errMsg:
        return render_template('genericPage.html', content=errMsg, title='Error')
    # If all is well, display the trial page:
    return render_template('genericPage.html', content=TrialHtml(sess, trialId), title='Trial Data')


@app.route('/scoreSet/<traitInstanceId>/', methods=['GET'])
@dec_check_session()
def traitInstance(sess, traitInstanceId):
#-----------------------------------------------------------------------
# Display the data for specified trait instance. t_integer
# MFK this should probably display RepSets, not individual TIs
#
    data = sess.DB().query(models.Datum).filter(models.Datum.traitInstance_id == traitInstanceId).all()

    r = "Score Set {0}".format("name?")
    #r += "<br>Datatype : " + TRAIT_TYPE_NAMES[tua.datatype]

    r += "<p><table border='1'>"
    r += "<tr><td>Row</td><td>Column</td><td>Timestamp</td><td>numValue</td><td>textValue</td></tr>"
    for d in data:
        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}<br></tr>".format(
            d.trialUnit.row, d.trialUnit.col, d.timestamp, d.numValue, d.getValue())
    r += "</table>"
    return render_template('genericPage.html', content=r, title='Score Set Data')

 

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
            # Good to go, show the user front page:
            sess.resetLastUseTime()
            sess.SetUserDetails(username, password)
            g.userName = username
            resp = FrontPage(sess)
            resp.set_cookie(COOKIE_NAME, sess.sid())
            return resp

    return LoginForm(error)


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
    app.config['SESS_FILE_DIR'] = '/home/***REMOVED***/fpserver/fpa/fp_web_admin/tmp2'
    app.run(debug=True, host='0.0.0.0')

