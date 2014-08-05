# fpWebAdmin.py
# Michael Kirk 2013
#
#

import os, sys, re
import zipfile, ntpath
import MySQLdb as mdb
from flask import Flask, request, Response, redirect, url_for, render_template, g, make_response
from flask import json, jsonify
from werkzeug import secure_filename
from jinja2 import Environment, FileSystemLoader
from functools import wraps
from time import strftime

# If we are running locally for testing, we need this magic for some imports to work:
if __name__ == '__main__':
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

import dbUtil
import fpTrait
import fp_common.models as models
import fp_common.util as util
import fpTrial
import fpUtil
import trialAtt
from fp_common.const import *
from dbUtil import GetTrial, GetTrials, GetSysTraits
from fpUtil import HtmlFieldset, HtmlForm, HtmlButtonLink, HtmlButtonLink2
import fp_common.util as util

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

LOGIN_TIMEOUT = 1500          # Idle time before requiring web user to login again


#############################################################################################
###  FUNCTIONS: #############################################################################

def getMYSQLDBConnection(sess):
#-------------------------------------------------------------------------------
# Return mysqldb connection for user associated with session
#
    try:
        usrname = dbUserName(sess.GetUser())
        usrdb = dbName(sess.GetUser())
        con = mdb.connect('localhost', usrname, sess.GetPassword(), usrdb)
        return con
    except mdb.Error, e:
        return None


def dec_check_session(returnNoneSess=False):
#-------------------------------------------------------------------------------------------------
# Decorator to check if in valid session. If not, send the login page.
# Generates function that has session as first parameter.
# If returnNoneSess is true, then the function is returned even if session is
# invalid, but with None as the session parameter - this can be used for pages
# that don't require a user to be logged in.
#
    def param_dec(func):
        @wraps(func)
        def inner(*args, **kwargs):
            COOKIE_NAME = 'sid'
            sid = request.cookies.get(COOKIE_NAME) # Get the session id from cookie (if there)
            sess = websess.WebSess(False, sid, LOGIN_TIMEOUT, app.config['SESS_FILE_DIR']) # Create or get session object
            g.rootUrl = url_for('urlMain') # Set global var g, accessible by templates, to the url for this func
            if not sess.Valid():  # Check if session is still valid
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
# Return HTML Response for urlMain user page after login
#
    sess.resetLastUseTime()    # This should perhaps be in dataPage, assuming it will only run immediately
                               # after login has been checked (i.e. can't click on link on page that's been
                               # been sitting around for a long time and have it prevent the timeout).
    return dataPage(sess, content=msg, title="User: " + sess.GetUser())


#####################################################################################################
# Trial page functions:
#

def htmlTrialTraitTable(trial):
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
        if trt.type in [T_INTEGER, T_DECIMAL, T_CATEGORICAL]:
            url = url_for('urlTraitValidation', trialId=trial.id, traitId=trt.id,  _external=True)
            validateButton = HtmlButtonLink2("Details", url)
            out += "<td>" + validateButton  + "</td>"
    out += "</table>"
    return out


def htmlTrialScoreSets(sess, trialId):
#----------------------------------------------------------------------------------------------------
# Returns HTML for list of trial score sets.
    trl = dbUtil.GetTrial(sess, trialId)
    scoreSets = trl.getScoreSets()
    if len(scoreSets) < 1:
        return "No trait score sets yet"
    htm = ('\n<table style="border:1px solid #ccc;border-collapse: collapse;">' +
            '<thead><tr><th>Trait</th><th>Date Created</th><th>Device Id</th>' +
            '<th>seqNum</th><th>Score Data</th></tr></thead>\n')
    for ss in scoreSets:
        tis = ss.getInstances()
        htm += "  <tbody style='border:1px solid #000;border-collapse: separate;border-spacing: 4px;'>\n"
        if False and len(ss) == 1:
            htm += "<b>{1}:{2}&nbsp;&nbsp;</b><a href={0}>Single sample</a><p>".format(
                url_for('urlScoreSetTraitInstance', traitInstanceId=tis[0].id), tis[0].trait.caption, ss.seqNum)
        else:
            first = True
            tdPattern = "<td style='border-left:1px solid grey;'>{0}</td>"
            for oti in tis:
                htm += "<tr>"
                htm += tdPattern.format(oti.trait.caption if first else "")
                htm += tdPattern.format(util.formatJapDate(oti.dayCreated) if first else "")
                htm += tdPattern.format(oti.getDeviceId() if first else "")
                htm += tdPattern.format(oti.seqNum if first else "")
                htm += tdPattern.format("<a href={0}>&nbsp;Sample{1} : {2} scores</a></td>".format(
                        url_for('urlScoreSetTraitInstance', traitInstanceId=oti.id), oti.sampleNum, oti.numData()))
                #htm += tdPattern.format(oti.numData())
                htm += "</tr>\n"
                first = False
        htm += '  </tbody>\n'
    htm +=  "\n</table>\n"
    return htm

def htmlNodeAttributes(sess, trialId):
#----------------------------------------------------------------------------------------------------
# Returns HTML for trial attributes.
# MFK - improve this, showing type and number of values, also delete button? modify?
    attList = dbUtil.GetTrialAttributes(sess, trialId)
    out = ''
    if len(attList) < 1:
        out += "No attributes found"
    else:
        out = "<table border='1'>"
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(
            "Name", "Datatype", "Values")
        for att in attList:
            valuesButton = HtmlButtonLink2("values", url_for("urlAttributeDisplay", trialId=trialId, attId=att.id))
            out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(
                   att.name, TRAIT_TYPE_NAMES[att.datatype], valuesButton)
        out += "</table>"

    # Add BROWSE button:
    out += '<p>'
    out += fpUtil.HtmlButtonLink2("Browse Attributes", url_for("urlBrowseTrial", trialId=trialId))

    # Add button to upload new/modified attributes:
    out += fpUtil.HtmlButtonLink2("Upload attributes", url_for("urlAttributeUpload", trialId=trialId))

    return out

def trialNameDetails(sess, trial):
#--------------------------------------------------------------------
# Return HTML for trial name, details and top level config:
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

    # Add DELETE button:
    r += '<p>'
    r += fpUtil.HtmlButtonLink2("Delete this trial", url_for("urlDeleteTrial", trialId=trial.id))
    r += '<p>'
    return r


def TrialHtml(sess, trialId):
#-----------------------------------------------------------------------
# Returns the HTML for a top level page to display/manage a given trial.
#
    trial = dbUtil.GetTrial(sess, trialId)
    if trial is None: return None

    r = trialNameDetails(sess, trial)

    # Attributes: ------------------------------------------
    r += HtmlFieldset(htmlNodeAttributes(sess, trialId), "Node Attributes:")

    # Traits: ------------------------------------------
    createTraitButton = '<p>' + fpUtil.HtmlButtonLink2("Create New Trait", url_for("urlNewTrait", trialId=trialId))
    addSysTraitForm = '<FORM method="POST" action="{0}">'.format(url_for('urlAddSysTrait2Trial', trialId=trialId))
    addSysTraitForm += '<input type="submit" value="Add System Trait">'  #MFK need javascript to check selection made before submitting
    addSysTraitForm += '<select name="traitID"><option value="0">Select System Trait to add</option>'
    sysTraits = dbUtil.GetSysTraits(sess)
    for st in sysTraits:
        for trt in trial.traits:   # Only add traits not already in trial
            if trt.id == st.id:
                break
        else:
            addSysTraitForm += '<option value="{0}">{1}</option>'.format(st.id, st.caption)
    addSysTraitForm += '</select></form>'
    r += HtmlFieldset(HtmlForm(htmlTrialTraitTable(trial)) + createTraitButton + addSysTraitForm, "Traits:")

    # Score sets: ------------------------------------------
    r += HtmlFieldset(htmlTrialScoreSets(sess, trialId), "Score Sets:")

    # Score Data: ------------------------------------------

    # Javascript function to generate the href for the download links.
    # The generated link includes trialId and the user selected output options.
    # MFK, note we have problem with download link in that if the session has timed
    # out, the html for the login page will be downloaded instead of the actual data.
    # Could do a redirect? but have to pass all the params..
    #
    jscript = """
    <script>
    function downloadURL(tables) {{
        var tdms = document.getElementById('tdms');
        var out = tables ? '{1}?' : '{0}?';
        // Add parameters indicating what to include in the download
        for (var i=0; i<tdms.length; i++)
            if (tdms[i].selected)
              out += '&' + tdms[i].value + '=1';
        return out;
    }}
    </script>
    """.format(url_for("urlTrialDataTSV", trialId=trialId), url_for("urlTrialDataBrowse", trialId=trialId))

#     jq1 = """
#     <link rel=stylesheet type=text/css href="{0}">
#     <script src="{1}"></script>
#     """.format(url_for('static', filename='jquery.multiselect.css'), url_for('static', filename='jquery.multiselect.js'))
#
#     jq = """
#     <script>
#     $(document).ready(
#         function() {
#             $("#tdms").multiselectMenu();
#         });
#     </script>
#     """
#     jscript += jq1 + jq
    #MFK perhaps instead of a multi select list we should have checkboxes. Contents of list are not dynamically
    # determined and checkboxes look nicer and are easier to use.

    dl = ""
    dl += jscript
    # Multi select output columns:
    dl += "Select columns to view/download:<br>"
    dl += "<select multiple='multiple' id='tdms'>";
    dl += "<option value='timestamp' selected='selected'>Timestamps</option>";
    dl += "<option value='user' selected='selected'>User Idents</option>"
    dl += "<option value='gps' selected='selected'>GPS info</option>"
    dl += "<option value='notes' selected='selected'>Notes</option>"
    dl += "<option value='attributes' selected='selected'>Attributes</option>"
    dl += "</select>"
    dl += "<br><a href='dummy' download='{0}.tsv' onclick='this.href=downloadURL(false)'>".format(trial.name)
    dl +=     "<button>Download Trial Data</button></a>"
    dl +=     " (browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)"
    dl += "<br><a href='dummy' onclick='this.href=downloadURL(false)' onContextMenu='this.href=downloadURL()'>"
    dl +=     "View tab separated score data</a>"
    dl += "<br>Note data is TAB separated"
    dl += "<br><a href='dummy' onclick='this.href=downloadURL(true)'>".format(trial.name)
    dl +=     "<button>Browse Trial Data</button></a>"
    r += HtmlFieldset(dl, "Score Data:")

    return r

def trialPage(sess, trialId):
#----------------------------------------------------------------------------
# Return response that is the urlMain page for specified file, or error message.
#
    trialh = TrialHtml(sess, trialId)
    if trialh is None:
        trialh = "No such trial"
    return dataPage(sess, content=trialh, title='Trial Data')



def dataNavigationContent(sess):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
    nc = "<h1>User {0}</h1>".format(sess.GetUser())
    nc += '<a href="{0}">Profile/Passwords</a>'.format(url_for('urlUserDetails', userName=g.userName))
    nc += '<hr clear="all">'

    trials = GetTrials(sess)
    trialListHtml = "No trials yet" if len(trials) < 1 else ""
    for t in trials:
        trialListHtml += "<li><a href={0}>{1}</a></li>".format(url_for("urlTrial", trialId=t.id), t.name)
    nc += "<h2>Trials:</h2>"
    nc += trialListHtml + HtmlButtonLink("Create New Trial", url_for("newTrial"))
    nc += '<hr>'
    nc += HtmlButtonLink("Download app", url_for("downloadApp"))
    nc += '<hr>'
    nc += '<a href="{0}">System Traits</a>'.format(url_for('urlSystemTraits', userName=g.userName))
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

def dataErrorPage(sess, errMsg):
#----------------------------------------------------------------------------
# Show error message in user data page.
    return dataPage(sess, content=errMsg, title='Error')

@app.route('/trial/<trialId>', methods=["GET"])
@dec_check_session()
def urlTrial(sess, trialId):
#===========================================================================
# Page to display/modify a single trial.
#
    return trialPage(sess, trialId)

def AddSysTrialTrait(sess, trialId, traitId):
#-----------------------------------------------------------------------
# Return error string, None for success
# MFK perhaps this would be better done with sqlalchemy?
#
    if traitId == "0":
        return "Select a system trait to add"
    try:
        con = getMYSQLDBConnection(sess)
        if con is None:
            return "Error accessing database"
        cur = con.cursor()
        cur.execute("insert into trialTrait (trial_id, trait_id) values (%s, %s)", (trialId, traitId))
        cur.close()
        con.commit()
    except mdb.Error, e:
        return "Error accessing database"
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

def NewTraitCategorical(sess, request, newTraitID):
    capKeys = [key for key in request.form.keys() if key.startswith("caption_")]
    for key in capKeys:
        caption = request.form.get(key)
        value = request.form.get(key.replace("caption_", "value_"))
        imageURL = None
        imageURLFile = request.files[key.replace("caption_", "imgfile_")]
        if imageURLFile:
            sentFilename = secure_filename(imageURLFile.filename)
            if allowed_file(sentFilename):
                subpath = os.path.join(app.config['CATEGORY_IMAGE_FOLDER'], sess.GetUser(), str(newTraitID))
                if not os.path.exists(subpath):
                    os.makedirs(subpath)
                imageURLFile.save(subpath +  "/" + sentFilename)
                imageURL = app.config['CATEGORY_IMAGE_URL_BASE'] + sess.GetUser() + "/" + str(newTraitID) + "/" + sentFilename
            else:
                pass  # should issue a warning perhaps?

        # Add new trait category:
        ncat = models.TraitCategory()
        ncat.value = value
        ncat.caption = caption
        ncat.trait_id = newTraitID
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
        NewTraitCategorical(sess, request, ntrt.id)
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


@app.route('/newTrial/', methods=["GET", "POST"])
@dec_check_session()
def newTrial(sess):
#===========================================================================
# Page for trial creation.
#

    # Trial attribute stuff. We want table driven presentation of allowed trial attributes.
    extras = ''
    for tae in trialAtt.gTrialAttributes:
        extras += tae.htmlElement()
    if request.method == 'GET':
        return dataTemplatePage(sess, 'newTrial.html', title='Create Trial', extraElements=extras)
    if request.method == 'POST':
        uploadFile = request.files['file']
        trl = fpTrial.uploadTrialFile(sess, uploadFile, request.form.get('name'), request.form.get('site'),
                                      request.form.get('year'), request.form.get('acronym'))
        # Handle error (trl will be string error message):
        if type(trl) is str:
            return dataTemplatePage(sess, 'newTrial.html', title='Create Trial', msg = trl, extraElements=extras)
        #
        # All good. Trial created. Set extra trial attributes.
        # MFK in general we will need insert or update (merge)
        #
        for tae in trialAtt.gTrialAttributes:
            sess.DB().add(models.TrialAtt(trl.id, tae.dbName, request.form.get(tae.ename)))
        sess.DB().commit()
        return FrontPage(sess)

def getAttributeColumns(sess, trialId, attList):
#-----------------------------------------------------------------------
# Returns a list of columns one for each attribute in attList - each column
# being an array of attribute values with one entry for each node in the trial.
# The columns are in the same order as attList, and the column entries are
# ordered by row/col. Missing values are given as the empty string.
    con = getMYSQLDBConnection(sess)
    qry = """
        select a.value from trialUnit n left join attributeValue a
        on n.id = a.trialUnit_id and a.trialUnitAttribute_id = %s
        where n.trial_id = %s
        order by row, col"""
    attValList = []
    for att in attList:
        valList = []
        cur = con.cursor()
        cur.execute(qry, (att.id, trialId))
        for row in cur.fetchall():  # can we just store cur.fetchall()? Yes we could, but perhaps better this way
            valList.append("" if row[0] is None else row[0])
        attValList.append(valList)
        cur.close()
    return attValList

def htmlDataTableMagic(tableId):
#----------------------------------------------------------------------------
# Html required to have a datatable table work, pass in the dom id
    r = '<link rel="stylesheet" type="text/css" href="//cdn.datatables.net/1.10.0/css/jquery.dataTables.css">'
    r += '<script type="text/javascript" language="javascript" src="//cdn.datatables.net/1.10.0/js/jquery.dataTables.js"></script>'
    r += '<script src={0}></script>'.format(url_for('static', filename='jquery.jeditable.css'))
    r += """<script>
    $(document).ready(function() {{
        $("#{0}").dataTable( {{
            "fnInitComplete": function(oSettings, json) {{$("#{0}").show();}}
          }});
    }});
    </script>
    """.format(tableId)
    return r


@app.route('/browseTrial/<trialId>/', methods=["GET", "POST"])
@dec_check_session()
def urlBrowseTrial(sess, trialId):
#===========================================================================
# Page for display of trial data.
#
    attList = dbUtil.GetTrialAttributes(sess, trialId)
    nodeList = dbUtil.getNodes(sess, trialId)

    # Get all the attribute values:
    attValList = getAttributeColumns(sess, trialId, attList)

    # generate html table of the trial data:
    r = htmlDataTableMagic('trialData')
    r += '<p><table id="trialData" class="display" cellspacing="0" width="100%" style="display: none">'
    hdrs = '<th>Row</th><th>Column</th>'
    for att in attList:
        hdrs += '<th>{0}</th>'.format(att.name)
    r += '<thead><tr>{0}</tr></thead>'.format(hdrs)
    r += '<tfoot><tr>{0}</tr></tfoot>'.format(hdrs)
    r += '<tbody>'
    for nodeIndex, n in enumerate(nodeList):
        r += '<tr>'
        r += '<td>{0}</td><td>{1}</td>'.format(n.row, n.col)
        for attIndex, att in enumerate(attList):
            r += '<td>{0}</td>'.format(attValList[attIndex][nodeIndex])
        r += '</tr>'
    r += '</tbody></table>'

    return dataPage(sess, content=r, title='Browse')


def getDataColumns(sess, trialId, tiList):
#-----------------------------------------------------------------------
# SQL query - this is a bit complicated:
# Get a row for each node in a given trial, showing the most recent value for the node
# for a given trait instance. Note we can distinguish NA from not present as
# those rows that have a non null value for any of the d1 fields that are alway
# non null - eg timestamp. The values we need are the datum value (type appropriate)
# and the score metadata. There must be a result for every node, and these must be
# in row/col order.
# NB we could pass in which metadata parameters are required, rather than getting them all.
# Output is list of column, each a list of value data (value, timestamp, userid, lat, long)
# The columns are in the same order as tiList. Timestamp is given in readable form.
#
    con = getMYSQLDBConnection(sess)
    qry = """
    select d1.{0}, d1.timestamp, d1.userid, d1.gps_lat, d1.gps_long
    from trialUnit t
      left join datum d1 on t.id = d1.trialUnit_id and d1.traitInstance_id = %s
      left join datum d2 on d1.trialUnit_id = d2.trialUnit_id and d1.traitInstance_id = d2.traitInstance_id and d2.timestamp > d1.timestamp
    where t.trial_id = %s and ((d2.timestamp is null and d1.traitInstance_id = %s) or d1.timestamp is null)
    order by row, col
    """
    print qry
    outList = []
    for ti in tiList:
        # If trait type is categorical then the values will be numbers which should be
        # converted into names (via the traitCategory table), retrieve the map for the
        # trait first:
        if ti.trait.type == T_CATEGORICAL:
            catMap = models.TraitCategory.getCategoricalTraitValue2NameMap(sess.DB(), ti.trait_id)
        else:
            catMap = None

        valList = []
        outList.append
        cur = con.cursor()
        cur.execute(qry.format(models.Datum.valueFieldName(ti.trait.type)), (ti.id, trialId, ti.id))
        for row in cur.fetchall():
            timestamp = row[1]
            if timestamp is None:          # no datum record case
                valList.append(["","","","",""])
            else:
                val = row[0]
                if val is None: val = "NA"
                elif catMap is not None:   # map value to name for categorical trait
                    val = catMap[int(val)]
                valList.append([val, util.epoch2dateTime(timestamp), row[2], row[3], row[4]])
        outList.append(valList)
        cur.close()
    return outList

def getTrialData(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes, table=False):
#-----------------------------------------------------------------------
# Returns trial data as plain text tsv form - i.e. for download, or as html table.
# The data is arranged in node rows, and trait instance score and attribute columns.
# Form params indicate what score metadata to display.
#
# Note we have improved performance (over a separate query for each value) by getting
# the data for each trait instance with one sql query.
# Note this will not scale indefinitely, it requires having the whole dataset in mem at one time.
# If necessary we could check the dataset size and if necessary switch to a different method.
# for example server side mode datatables.
# MFK Need better support for choosing attributes, metadata, and score columns to show. Ideally within
# datatables browse could show/hide columns and export current selection to tsv.
#
    # Get Trait Instances:
    tiList = dbUtil.GetTraitInstancesForTrial(sess, trialId)  # get Trait Instances
    valCols = getDataColumns(sess, trialId, tiList)            # get the data for the instances

    # Work out number of columns for each trait instance:
    numColsPerValue = 1
    if showTime:
        numColsPerValue += 1
    if showUser:
        numColsPerValue += 1
    if showGps:
        numColsPerValue += 2

    # Format controls, table or tsv
    #tables = True
    SEP = '</td><td>' if table else '\t'
    HSEP = '</th><th>'
    ROWSTART = '<tr><td>' if table else ''
    ROWEND = '</td></tr>\n' if table else '\n'
    HSEP = '</th><th>' if table else '\t'
    HROWSTART = '<thead><th>' if table else ''
    HROWEND = '</th></thead>\n' if table else '\n'
    # MFK unify with browseData (for attributes
    r = '<table id="trialData" class="display" cellspacing="0" width="100%" style="display: none">' if table else ''

    # Headers:
    r += HROWSTART
    r += "Row" + HSEP + "Column"
    if showAttributes:
        trl = dbUtil.GetTrial(sess, trialId)
        attValList = getAttributeColumns(sess, trialId, trl.tuAttributes)  # Get all the att vals in advance
        for tua in trl.tuAttributes:
            r += HSEP + tua.name
    for ti in tiList:
        tiName = "{0}_{1}.{2}.{3}".format(ti.trait.caption, ti.dayCreated, ti.seqNum, ti.sampleNum)
        r += "{1}{0}".format(tiName, HSEP)
        if showTime:
            r += "{1}{0}_timestamp".format(tiName, HSEP)
        if showUser:
            r += "{1}{0}_user".format(tiName, HSEP)
        if showGps:
            r += "{1}{0}_latitude{1}{0}_longitude".format(tiName, HSEP)
    if showNotes:
        r += HSEP + "Notes"  # Putting notes at end in case some commas slip thru and mess up csv structure
    r += HROWEND

    # Data:
    nodeList = dbUtil.getNodes(sess, trialId)
    for nodeIndex, node in enumerate(nodeList):
        r += ROWSTART

        # Row and Col:
        r += "{0}{2}{1}".format(node.row, node.col, SEP)

        # Attribute Columns:
        if showAttributes:
            for ind, tua in enumerate(trl.tuAttributes):
                r += SEP
                r += attValList[ind][nodeIndex]

        # Scores:
        for tiIndex, ti in enumerate(tiList):
            [val, timestamp, userid, lat, long] = valCols[tiIndex][nodeIndex]
            # Write the value:
            r += "{0}{1}".format(SEP, val)
            # Write any other datum fields specified:
            if showTime:
                r += "{0}{1}".format(SEP, timestamp)
            if showUser:
                r += "{0}{1}".format(SEP, userid)
            if showGps:
                r += "{0}{1}{0}{2}".format(SEP, lat, long)

        # Notes, as list separated by pipe symbols:
        if showNotes:
            r += SEP + '"'
            tuNotes = dbUtil.GetTrialUnitNotes(sess, node.id)
            for note in tuNotes:
                r += '{0}|'.format(note.note)
            r += '"'

        # End the line:
        r += ROWEND

    r += '</table>' if table else ''
    return r

@app.route('/trial/<trialId>/data/', methods=['GET'])
@dec_check_session()
def urlTrialDataTSV(sess, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    r = getTrialData(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes, False)
    return Response(r, content_type='text/plain')

@app.route('/trial/<trialId>/data/browse', methods=['GET'])
@dec_check_session()
def urlTrialDataBrowse(sess, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    r = htmlDataTableMagic('trialData')
    r += getTrialData(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes, True)
    return dataPage(sess, content=r, title='Browse')


@app.route('/deleteTrial/<trialId>/', methods=["GET", "POST"])
@dec_check_session()
def urlDeleteTrial(sess, trialId):
#===========================================================================
# Page for trial deletion. Display trial stats and request confirmation
# of delete.
#
    trl = models.GetTrial(sess.DB(), trialId)
    def getHtml(msg=''):
        out = '<div style="color:red">{0}</div><p>'.format(msg);  # should be red style="color:red"
        out += 'Trial {0} contains:<br>'.format(trl.name)
        out += '{0} Score Sets<br>'.format(trl.numScoreSets())
        out += '{0} Scores<br>'.format(trl.numScores())
        out += '<p>Password required: <input type=password name="password">'
        out += '<p>Do you really want to delete this trial?'
        out += '<p> <input type="submit" name="yesDelete" value="Yes, Delete">'
        out += '<input type="submit" name="noDelete" style="color:red" color:red value="Goodness me NO!">'
        return dataPage(sess, title='Delete Trial',
                        content=fpUtil.htmlHeaderFieldset(fpUtil.HtmlForm(out, post=True),
                                                          'Really Delete Trial {0}?'.format(trl.name)))
    if request.method == 'GET':
        return getHtml()
    if request.method == 'POST':
        out = ''
        if request.form.get('yesDelete'):
            if not request.form.get('password'):
                 return getHtml('You must provide a password')
            if request.form.get('password') != sess.GetPassword():
                return getHtml('Password is incorrect')
            else:
                # Delete the trial:
                fpTrial.deleteTrial(sess, trialId)
                return dataPage(sess, '', 'Trial Deleted')
        else:
            # Do nothing:
            return FrontPage(sess)

@app.route('/trial/<trialId>/newTrait/', methods=["GET", "POST"])
@dec_check_session()
def urlNewTrait(sess, trialId):
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
            return dataErrorPage(sess, errMsg)
        if trialId == 'sys':
            return FrontPage(sess, 'System trait created')
        return trialPage(sess, trialId)

# def attributeListHtmlSelect(sess, trialId, selectedId=None, datatypes=None):
# #===========================================================================
# # HTML for form select drop down for selecting an attribute.
# # Currently only relevant for integer traits.
# #
#     # Attribute list:
#     attListHtml = '<select name="attributeList" id="tdAttribute">'
#     attListHtml += '<option value="0">&lt;Choose Attribute&gt;</option>'
#     atts = dbUtil.GetTrialAttributes(sess, trialId)
#     for att in atts:
#         if datatypes is not None or att.datatype in datatypes:
#             attListHtml += '<option value="{0}" {2}>{1}</option>'.format(
#                 att.id, att.name, "selected='selected'" if att.id == selectedId else "")
#     attListHtml += '</select>'
#     return attListHtml

@app.route('/trial/<trialId>/trait/<traitId>', methods=['GET', 'POST'])
@dec_check_session()
def urlTraitValidation(sess, trialId, traitId):
#===========================================================================
# Page to display/modify validation parameters for a trait.
# Currently only relevant for integer traits.
#
    trt = dbUtil.GetTrait(sess, traitId)
    trlTrt = dbUtil.getTrialTrait(sess, trialId, traitId)
    trial = dbUtil.GetTrial(sess, trialId)

    title = 'Trial: ' + trial.name + ', Trait: ' + trt.caption
    comparatorCodes = [
        ["gt", "Greater Than", 1],
        ["ge", "Greater Than or Equal to", 2],
        ["lt", "Less Than", 3],
        ["le", "Less Than or Equal to", 4]
    ]

    if request.method == 'GET':
        ### Form fields applicable to all traits:
        formh = 'Trial: ' + trial.name
        formh += '<br>Trait: ' + trt.caption
        formh += '<br>Type: ' + TRAIT_TYPE_NAMES[trt.type]

        # Trait barcode selection:
        # Note it doesn't matter if a sysTrait, since the barcode is stored in trialTrait
        attSelector = '<p><label for=bcAttribute>Barcode for Scoring:</label><select name="bcAttribute" id="bcAttribute">'
        attSelector += '<option value="none">&lt;Choose Attribute&gt;</option>'
        atts = dbUtil.GetTrialAttributes(sess, trialId)
        for att in atts:
            attSelector += '<option value="{0}" {2}>{1}</option>'.format(
                att.id, att.name, "selected='selected'" if att.id == trlTrt.barcodeAtt_id else "")
        attSelector += '</select>'
        formh += attSelector

        if trt.type == T_INTEGER or trt.type == T_DECIMAL:
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
                minText = "value='{:f}'".format(ttn.getMin())
            maxText = ""
            if ttn and ttn.max is not None:
                maxText = "value='{:f}'".format(ttn.getMax())
            minMaxBounds = "<p>Minimum: <input type='text' name='min' id=tdMin {0}>".format(minText)
            minMaxBounds += "<p>Maximum: <input type='text' name='max' id=tdMax {0}><br>".format(maxText);

            # Parse condition string, if present, to retrieve comparator and attribute.
            # Format of the string is: ^. <2_char_comparator_code> att:<attribute_id>$
            # The only supported comparison at present is comparing the score to a
            # single attribute.
            # NB, this format needs to be in sync with the version on the app. I.e. what
            # we save here, must be understood on the app.
            # MFK note attribute id seems to be stored as text in cond string, will seems
            # not ideal. Probably should be a field in the table trialTraitNumeric.
            # Note that the same issue applies in the app database There is one advantage
            # I see to having a string is that we can change what is stored without requiring
            # a database structure change. And db structure changes on the app require
            # a database replace on the app.
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
            for att in atts:
                if att.datatype == T_DECIMAL or att.datatype == T_INTEGER:
                    attListHtml += '<option value="{0}" {2}>{1}</option>'.format(
                        att.id, att.name, "selected='selected'" if att.id == atId else "")
            attListHtml += '</select>'

            # javascript form validation
            # NEED TO Check that min and max are valid int or decimal
            # Check that if one of comp and att chosen both are
            # Note this is the same validation for integer and decimal. So integer
            # will allow decimal min/max. Could be made strict, but I'm not sure this is bad.
            script = """
                <script>
                function isValidDecimal(inputtxt) {
                    var decPat =  /^[+-]?[0-9]+(?:\.[0-9]+)?$/g;
                    return inputtxt.match(decPat);
                }

                function validateTraitDetails() {
                    // Check min and max fields:
                    /* It should be OK to have no min or max:
                    if (!isValidDecimal(document.getElementById("tdMin").value)) {
                        alert('Invalid value for minimum');
                        return false;
                    }
                    if (!isValidDecimal(document.getElementById("tdMax").value)) {
                        alert('Invalid value for maximum');
                        return false;
                    }
                    */

                    // Check attribute/comparator fields, either both or neither present:
                    var att = document.getElementById("tdAttribute").value;
                    var comp = document.getElementById("tdCompOp").value;
                    var attPresent = (att !== null && att !== "0");
                    var compPresent = (comp !== null && comp !== "0");
                    if (attPresent && !compPresent) {
                        alert("Attribute selected with no comparator specified, please fix.");
                        return false;
                    }
                    if (!attPresent && compPresent) {
                        alert("Comparator selected with no attibute specified, please fix.");
                        return false;
                    }
                    return true;
                }
                </script>
            """

            formh += minMaxBounds
            formh += '<p>Integer traits can be validated by comparison with an attribute:'
            formh += '<br>Trait value should be ' + valOp + attListHtml
            formh += ('\n<p><input type="button" style="color:red" value="Cancel"' +
                ' onclick="location.href=\'{0}\';">'.format(url_for("urlTrial", trialId=trialId)))
            formh += '\n<input type="submit" style="color:red" value="Submit">'

            return dataPage(sess, content=script + HtmlForm(formh, post=True, onsubmit='return validateTraitDetails()'), title='Trait Validation')

        return dataPage(sess, content=HtmlForm(formh, post=True), title='Trait Validation')
        #return dataPage(sess, content='No validation for this trait type', title=title)
    if request.method == 'POST':
        ### Form fields applicable to all traits:
        # Trait barcode selection:
        #MFK sys traits? barcode field is an trialUnitAttribute id but this is associated with a trial
        # we either have to move it to trialTrait, or make all trial traits non system traits.
        barcodeAttId = request.form.get('bcAttribute')  # value should be valid attribute ID
        if barcodeAttId == 'none':
            trlTrt.barcodeAtt_id = None
        else:
            trlTrt.barcodeAtt_id = barcodeAttId

        if trt.type == T_INTEGER or trt.type == T_DECIMAL: # clone of above remove above when integer works with numeric
            op = request.form.get('validationOp')  # value should be [1-4], see comparatorCodes
            if not re.match('[0-4]', op):
                return "Invalid operation {0}".format(op) # should be some function to show error page..
            at = request.form.get('attributeList') # value should be valid attribute ID

            # Check min/max:
            vmin = request.form.get('min')
            if len(vmin) == 0:
                vmin = None
            vmax = request.form.get('max')
            if len(vmax) == 0:
                vmax = None

            # Get existing trialTraitNumeric, or create new one if none:
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

        return redirect(url_for("urlTrial", trialId=trialId))


@app.route('/trial/<trialId>/uploadAttributes/', methods=['GET', 'POST'])
@dec_check_session()
def urlAttributeUpload(sess, trialId):
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
def urlAttributeDisplay(sess, trialId, attId):
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
def urlUserDetails(sess, userName):
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

        # Changing admin or app password:
        currUser = sess.GetUser()
        currPass = sess.GetPassword()
        password = form.get("password")
        if password != currPass:
            sess.close()
            return render_template('sessError.html', msg="Password is incorrect", title='FieldPrime Login')
        newpassword1 = form.get("newpassword1")
        newpassword2 = form.get("newpassword2")
        if not (password and newpassword1 and newpassword2):
            return dataTemplatePage(sess, 'profile.html', op=op, errMsg="Please fill out all fields", title=title)
        if newpassword1 != newpassword2:
            return dataTemplatePage(sess, 'profile.html', op=op, errMsg="Versions of new password do not match.", title=title)

        # OK, all good, change their password:
        try:
            con = getMYSQLDBConnection(sess)
            cur = con.cursor()
            msg = ''
            if op == 'newpw':
                cur.execute("set password for %s@localhost = password(%s)", (dbUserName(sess.GetUser()), newpassword1))
                sess.SetUserDetails(currUser, newpassword1)
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
def urlSystemTraits(sess, userName):
#---------------------------------------------------------------------------
#
#
    if request.method == 'GET':
        # System Traits:
        sysTraits = GetSysTraits(sess)
        sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else fpTrait.TraitListHtmlTable(sysTraits)
        r = HtmlFieldset(
            HtmlForm(sysTraitListHtml) + HtmlButtonLink("Create New System Trait", url_for("urlNewTrait", trialId='sys')),
            "System Traits")
        return dataPage(sess, title='System Traits', content=r)


@app.route('/trial/<trialId>/addSysTrait2Trial/', methods=['POST'])
@dec_check_session()
def urlAddSysTrait2Trial(sess, trialId):
# MFK here we should copy the system trait, not use it.
#
    errMsg = AddSysTrialTrait(sess, trialId, request.form['traitID'])
    if errMsg:
        return dataErrorPage(sess, errMsg)
    # If all is well, display the trial page:
    return trialPage(sess, trialId)

@app.route('/scoreSet/<traitInstanceId>/', methods=['GET'])
@dec_check_session()
def urlScoreSetTraitInstance(sess, traitInstanceId):
#-----------------------------------------------------------------------
# Display the data for specified trait instance.
# MFK this should probably display RepSets, not individual TIs
#
    ti = dbUtil.getTraitInstance(sess, traitInstanceId)
    typ = ti.trait.type
    name = ti.trait.caption + '_' + str(ti.seqNum) + ' sample ' + str(ti.sampleNum) # MFK add name() to TraitInstance
    data = dbUtil.getTraitInstanceData(sess, traitInstanceId)
    r = "Score Set: {0}".format(name)
    #r += "<br>Datatype : " + TRAIT_TYPE_NAMES[tua.datatype]

    # For photo score sets add button to download photos as zip file:
    if typ == T_PHOTO:
        r += ("<p><a href={1} download='{0}'>".format(ntpath.basename(photoArchiveZipFileName(sess, traitInstanceId)),
                                                 url_for('urlPhotoScoreSetArchive', traitInstanceId=traitInstanceId))
         + "<button>Download Photos as Zip file</button></a>"
         + " (browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)")

    r += "<p><table border='1'>"
    r += "<tr><th>Row</th><th>Column</th><th>Value</th><th>User</th><th>Time</th><th>Latitude</th><th>Longitude</th></tr>"
    for d in data:
        if typ == T_PHOTO:  # Special case for photos. Display a link to show the photo.
                            # Perhaps this should be done in Datum.getValue, but we don't have all info.
            if d.isNA():
                value = 'NA'
            else:
                fname = models.photoFileName(sess.GetUser(),
                                             ti.trial_id,
                                             ti.trait_id,
                                             d.trialUnit.id,
                                             ti.token,
                                             ti.seqNum,
                                             ti.sampleNum)
                value = '<a href=' + url_for('urlPhoto', filename=fname) + '>view photo</a>'
        else:
            value = d.getValue()

        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>".format(
            d.trialUnit.row, d.trialUnit.col, value, d.userid, util.epoch2dateTime(d.timestamp), d.gps_lat, d.gps_long)
    r += "</table>"
    return dataPage(sess, content=r, title='Score Set Data')


def makeZipArchive(sess, traitInstanceId, archiveFileName):
#-----------------------------------------------------------------------
# Create zip archive of all the photos for the given traitInstance.
    ti = dbUtil.getTraitInstance(sess, traitInstanceId)
    if ti.trait.type != T_PHOTO:
        return 'Not a photo trait'
    data = dbUtil.getTraitInstanceData(sess, traitInstanceId)
    try:
        with zipfile.ZipFile(archiveFileName, 'w') as myzip:  # MFK xxx how to return false on error, exception handler?
            for d in data:
                # Add all the photos in the traitInstance to the archive
                fname = models.photoFileName(sess.GetUser(),
                                             ti.trial_id,
                                             ti.trait_id,
                                             d.trialUnit.id,
                                             ti.token,
                                             ti.seqNum,
                                             ti.sampleNum)
                print 'upload folder ' + app.config['PHOTO_UPLOAD_FOLDER'] + fname
                myzip.write(app.config['PHOTO_UPLOAD_FOLDER'] + fname, fname)
    except Exception, e:
        return 'A problem occurred:\n{0}\n{1}'.format(type(e), e.args)
    return None

def photoArchiveZipFileName(sess, traitInstanceId):
#-----------------------------------------------------------
# Generate file name for zip of photos in traitInstance.
    ti = dbUtil.getTraitInstance(sess, traitInstanceId)
    return app.config['PHOTO_UPLOAD_FOLDER'] + '{0}_{1}_{2}.zip'.format(sess.GetUser(), ti.trial.name, traitInstanceId)

@app.route("/photo/scoreSetArchive/<traitInstanceId>", methods=['GET'])
@dec_check_session()
def urlPhotoScoreSetArchive(sess, traitInstanceId):
#--------------------------------------------------------------------
# Return zipped archive of the photos for given traitInstance
    archFname = photoArchiveZipFileName(sess, traitInstanceId)
    errMsg = makeZipArchive(sess, traitInstanceId, archFname)
    if errMsg is not None:
        return dataErrorPage(sess, errMsg)
    resp = make_response(open(archFname).read())
    resp.content_type = "image/jpeg"
    os.remove(archFname)    # delete the file
    return resp


@app.route("/photo/<filename>", methods=['GET'])
@dec_check_session()
def urlPhoto(sess, filename):
# This is a way to provide images to authenticated user only.
# An alternative would be to put the image in a static folder,
# but then (I think) they must be visible to everyone.
# Note this method is presumably slower to run than just having
# a static URL. I'm not sure whether the performance hit is significant.
    fullpath = app.config['PHOTO_UPLOAD_FOLDER'] + filename
    if not os.path.isfile(fullpath):
        return dataErrorPage(sess, "Can't find file {0}".format(fullpath))
    resp = make_response(open(fullpath).read())
    resp.content_type = "image/jpeg"
    return resp


@app.route('/user/<userName>/', methods=['GET'])
@dec_check_session()
def urlUserHome(sess, userName):
    return FrontPage(sess)

@app.route('/logout', methods=["GET"])
@dec_check_session()
def urlLogout(sess):
    sess.close()
    return redirect(url_for('urlMain'))

@app.route('/info/<pagename>', methods=["GET"])
@dec_check_session(True)
def urlInfoPage(sess, pagename):
    g.rootUrl = url_for('urlMain')
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)

@app.route('/', methods=["GET", "POST"])
def urlMain():
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
# necessary, eg for urlScoreSetTraitInstance, which doesn't need it since the TI id is unique within db.
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
            util.fpLog(app, 'Login failed attempt for user {0}'.format(username))
            error = 'Invalid Password'
        else:
            # Good to go, show the user front page, after adding cookie:
            util.fpLog(app, 'Login from user {0}'.format(username))
            sess.resetLastUseTime()
            sess.SetUserDetails(username, password)
            g.userName = username
            resp = make_response(FrontPage(sess))
            resp.set_cookie(COOKIE_NAME, sess.sid())      # Set the cookie
            return resp
        return render_template('sessError.html', msg=error, title='FieldPrime Login')

    # Request method is 'GET':
    return urlInfoPage('fieldprime')


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
    app.config['PHOTO_UPLOAD_FOLDER'] = expanduser("~") + '/proj/fpserver/photos/'
    app.config['FPLOG_FILE'] = expanduser("~") + '/proj/fpserver/fplog/fp.log'

    # Setup logging:
    app.config['FP_FLAG_DIR'] = expanduser("~") + '/proj/fpserver/fplog/'
    util.initLogging(app, True)  # Specify print log messages
    util.flog("calling flog")

    app.run(debug=True, host='0.0.0.0', port=5001)

