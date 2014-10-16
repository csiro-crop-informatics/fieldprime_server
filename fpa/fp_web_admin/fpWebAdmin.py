# fpWebAdmin.py
# Michael Kirk 2013
#
#

import os, sys, re, traceback
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
import trialProperties
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

@app.errorhandler(500)
def internalError(e):
#-------------------------------------------------------------------------------
# Trap for Internal Server Errors, these are typically as exception raised
# due to some problem in code or database. We log the details. Possibly should
# try to send an email (to me I guess) to raise the alarm..
#
    util.flog('internal error:')
    util.flog(e)
    util.flog(traceback.format_exc())
    return 'FieldPrime: Internal Server Error <br />{}::{}'.format(app.config['SESS_FILE_DIR'], traceback.format_exc())


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
    out = "<table class='fptable' cellspacing='0' cellpadding='5'>"
    out += "<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th></tr>".format( 
        "Caption", "Description", "Type", "Details")
    for trt in trial.traits:
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(
            trt.caption, trt.description, TRAIT_TYPE_NAMES[trt.type])
        # Add "Detail" button:
        url = url_for('urlTraitDetails', trialId=trial.id, traitId=trt.id,  _external=True)
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
    attList = dbUtil.getNodeAttributes(sess, trialId)
    out = ''
    if len(attList) < 1:
        out += "No attributes found"
    else:
        out = "<table class='fptable' cellspacing='0' cellpadding='5'>"
        out += "<tr><th>{0}</th><th>{1}</th><th>{2}</th></tr>".format(
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
    out += fpUtil.HtmlButtonLink2("Upload Attributes", url_for("urlAttributeUpload", trialId=trialId))

    return out

@app.route('/trialUpdate/<trialId>', methods=["POST"])
@dec_check_session()
def urlTrialNameDetailPost(sess, trialId):
#===========================================================================
# Page for trial creation.
#
    trialProperties.processPropertiesForm(sess, trialId, request.form)
    return "Trial Properties Updated on Server"

def htmlTrialNameDetails(sess, trial):
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

    # Make separate (AJAX) form for extras: -----------------------------
    extrasForm = trialProperties.trialPropertyTable(sess, trial, False)
    extrasForm += '<p><input type="submit" id="extrasSubmit" value="Update Values">'   # Add submit button:
    r += HtmlFieldset(HtmlForm(extrasForm, id='extras'))
    # JavaScript for AJAX form submission:
    r += '''
    <script>
    $(document).ready(function() {
        $("#extrasSubmit").click({url: "%s"}, fplib.extrasSubmit);
    });
    </script>\n''' % url_for('urlTrialNameDetailPost', trialId=trial.id)

    # Add DELETE button: ------------------------------------------------
    r += '<p>'
    r += fpUtil.HtmlButtonLink2("Delete this trial", url_for("urlDeleteTrial", trialId=trial.id))
    r += '<p>'
    return r

def htmlTrialTraits(sess, trial):
#--------------------------------------------------------------------
# Return HTML for trial name, details and top level config:
    createTraitButton = '<p>' + fpUtil.HtmlButtonLink2("Create New Trait", url_for("urlNewTrait", trialId=trial.id))
    addSysTraitForm = '<FORM method="POST" action="{0}">'.format(url_for('urlAddSysTrait2Trial', trialId=trial.id))
    addSysTraitForm += '<select name="traitID"><option value="0">Select System Trait to add</option>'
    sysTraits = dbUtil.GetSysTraits(sess)
    for st in sysTraits:
        for trt in trial.traits:   # Only add traits not already in trial
            if trt.id == st.id:
                break
        else:
            addSysTraitForm += '<option value="{0}">{1}</option>'.format(st.id, st.caption)
    addSysTraitForm += '</select> &nbsp; '
    addSysTraitForm += '<input type="submit" value="Add System Trait">'  #MFK need javascript to check selection made before submitting
    addSysTraitForm += '</form>'
    return HtmlForm(htmlTrialTraitTable(trial)) + createTraitButton + addSysTraitForm

def htmlTrialData(sess, trial):
#--------------------------------------------------------------------
# Return html chunk with table of scores and attributes.

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
    """.format(url_for("urlTrialDataTSV", trialId=trial.id), url_for("urlTrialDataBrowse", trialId=trial.id))

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
    dl += "<p><a href='dummy' download='{0}.tsv' onclick='this.href=downloadURL(false)'>".format(trial.name)
    dl +=     "<button>Download Trial Data</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>(browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)</span>"
    dl += "<p><a href='dummy' onclick='this.href=downloadURL(false)' onContextMenu='this.href=downloadURL()'>"
    dl +=     "<button>View tab separated score data</button></a><br />"
    dl += "<span style='font-size: smaller;'>Note data is TAB separated"
    dl += "<p><a href='dummy' onclick='this.href=downloadURL(true)'>".format(trial.name)
    dl +=     "<button>Browse Trial Data</button></a>"
    return dl


class htmlChunkSet:
#-----------------------------------------------------------------------
# Class to manage a page made of separate "chunks", these can be
# displayed either as tabs or as fieldsets.
#
    def __init__(self):
        self.chunks = []

    def addChunk(self, id, title, content):
        self.chunks.append((id,title,content))

    def htmlFieldSets(self):
        h = ''
        for c in self.chunks:
            h += HtmlFieldset(c[2], c[1] + ':')
            h += '\n'
        return h

    def htmlTabs(self):
        h = '<script>  $(document).ready(function(){fplib.initTabs("tabs");}) </script>\n'

        # Tab headers:
        h += '<ul id="tabs">\n'
        for c in self.chunks:
            h += '  <li><a href="#{0}">{1}</a></li>\n'.format(c[0], c[1])
        h += '</ul>\n'

        # Tab content divs:
        for c in self.chunks:
            h += '<div class="tabContent" id="{0}">\n{1}\n</div>\n\n'.format(c[0], c[2])
        return h

def TrialHtml(sess, trialId):
#-----------------------------------------------------------------------
# Returns the HTML for a top level page to display/manage a given trial.
# Or None if no trial with given id.
#
    trial = dbUtil.GetTrial(sess, trialId)
    if trial is None: return None
    hts = htmlChunkSet()
    hts.addChunk('scoresets', 'Score Sets', htmlTrialScoreSets(sess, trialId))
    hts.addChunk('natts', 'Node Attributes', htmlNodeAttributes(sess, trialId))
    hts.addChunk('traits', 'Traits', htmlTrialTraits(sess, trial))
    hts.addChunk('data', 'Score Data', htmlTrialData(sess, trial))
    hts.addChunk('properties', 'Properties', htmlTrialNameDetails(sess, trial))
    return '<h2>Trial: {0}</h2>'.format(trial.name) + hts.htmlTabs()


def trialPage(sess, trialId):
#----------------------------------------------------------------------------
# Return response that is the urlMain page for specified file, or error message.
#
    trialh = TrialHtml(sess, trialId)
    if trialh is None:
        trialh = "No such trial"
    return dataPage(sess, content=trialh, title='Trial Data', trialId=trialId)



def dataNavigationContent(sess, trialId):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
    nc = "<h1 style='float:left; padding-right:20px; margin:0'>User: {0}. {1}</h1>".format(sess.GetUser(), trialId)
    nc += '<div style="float:right; margin-top:10px">'
    nc += '<a href="{0}"><span class="fa fa-user"></span> Profile/Passwords</a>'.format(url_for('urlUserDetails', userName=g.userName))
    nc += '<a href="{0}"><span class="fa fa-gear"></span> System Traits</a>'.format(url_for('urlSystemTraits', userName=g.userName))
    nc += '<a href="{0}"><span class="fa fa-magic"></span> Create New Trial</a>'.format(url_for("newTrial"))
    nc += '<a href="{0}"><span class="fa fa-download"></span> Download App</a>'.format(url_for("downloadApp"))
    nc += '<a href="https://docs.google.com/document/d/1SpKO_lPj0YzhMV6RKlzPgpNDGFhpaF-kCu1-NTmgZmc/pub"><span class="fa fa-question-circle"></span> App User Guide</a>'
    nc += '</div><div style="clear:both"></div>' 

    trials = GetTrials(sess)
    trialListHtml = None if len(trials) < 1 else "" 
    for t in trials:
        if "{}".format(t.id) == "{}".format(trialId):
            trialListHtml += "\n  <li class='fa-li fa selected'><a href={0}>{1}</a></li>".format(url_for("urlTrial", trialId=t.id), t.name)
        else:
            trialListHtml += "\n  <li class='fa-li fa'><a href={0}>{1}</a></li>".format(url_for("urlTrial", trialId=t.id), t.name)

    if trialListHtml:
        nc += '<hr style="margin:15px 0; border: 1px solid #aaa;">'
        nc += "<h2>Trials:</h2><ul class='fa-ul'>"
        nc += trialListHtml
        nc += '</ul><hr style="margin:15px 0; border: 1px solid #aaa;">'
    return nc


def dataPage(sess, title, content, trialId=None):
#----------------------------------------------------------------------------
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
#
    nc = dataNavigationContent(sess, trialId)
    return render_template('dataPage.html', navContent=nc, content=content, title=title)

def dataTemplatePage(sess, template, **kwargs):
#----------------------------------------------------------------------------
# Return page for user data with given template, kwargs are passed through
# to the template. The point of this function is to add the navigation content.
#
    if 'trialId' in kwargs:
        nc = dataNavigationContent(sess, trialId=kwargs['trialId'])
    else:
        nc = dataNavigationContent(sess)
    # nc = dataNavigationContent(sess) # Generate content for navigation bar:
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
    for tae in trialProperties.gTrialAttributes:
        extras += tae.htmlElement()
    if request.method == 'GET':
        return dataTemplatePage(sess, 'newTrial.html', title='Create Trial', extraElements=extras)
    if request.method == 'POST':
        uploadFile = request.files['file']
        trl, errMsg = fpTrial.uploadTrialFile(sess, uploadFile, request.form.get('name'), request.form.get('site'),
                                      request.form.get('year'), request.form.get('acronym'))
        # Handle error (trl will be string error message):
        if trl is None:
            return dataTemplatePage(sess, 'newTrial.html', title='Create Trial', msg = errMsg, extraElements=extras)
        #
        # All good. Trial created. Set extra trial attributes.
        # MFK in general we will need insert or update (merge)
        #
        trialProperties.processPropertiesForm(sess, trl.id, request.form)
        return FrontPage(sess)

def getAttributeColumns(sess, trialId, attList):
#-----------------------------------------------------------------------
# Returns a list of columns one for each attribute in attList - each column
# being an array of attribute values with one entry for each node in the trial.
# The columns are in the same order as attList, and the column entries are
# ordered by row/col. Missing values are given as the empty string.
    con = getMYSQLDBConnection(sess)
    qry = """
        select a.value from node n left join attributeValue a
        on n.id = a.node_id and a.nodeAttribute_id = %s
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
#
    r = '<link rel="stylesheet" type="text/css" href="//cdn.datatables.net/1.10.0/css/jquery.dataTables.css" />'
    r += '\n<script type="text/javascript" language="javascript" src="//cdn.datatables.net/1.10.0/js/jquery.dataTables.js"></script>'
    r += '\n<link rel="stylesheet" type="text/css" href="{}" />'.format(url_for('static', filename='jquery.jeditable.css'))

    # We need to initialize the jquery datatable, but also a bit of hacking
    # to set the width of the page. We use the datatables scrollX init param
    # to get a horizontal scroll on the table, but it seems very hard in css to
    # get the table to fill the available screen space and not have the right
    # hand edge invisible off to the right of the page. You can set the width
    # of the dataTables_wrapper to a fixed amount and that works, but doesn't
    # reflect the actual window size. If you set the width to 100%, it just doesn't
    # work - partly it seems because we are using css tables (i.e. if I try the
    # same code NOT in these tables 100% does work. So we are doing here at the moment
    # is to (roughly) set the trialData_wrapper width to the appropriate size
    # after the datatable is initialized and hook up a handler to redo this whenever
    # the screen is resized. Not very nice or future proof, but it will have to do for
    # the moment..

    r += """
    <script>
    function setTrialDataWrapperWidth() {
        var w = window;
        var c = $(".dataContent").width();
        var leftBarWidth = 0;
        //var leftBarWidth = $("#dataLeftBar").width();
        var setWidthTo = w.innerWidth - leftBarWidth;
        //alert('w.width ' + w.innerWidth + ' ' + c + ' ' + setWidthTo);
        document.getElementById('trialData_wrapper').style.maxWidth = setWidthTo + 'px';
    }

    $(document).ready(
        function() {
            $("#%s").dataTable( {
                "autoWidth" : true,

                "scrollX": true,

                "fnPreDrawCallback":function(){
                    $("#%s").hide();
                    //$("#loading").show();
                    //alert("Pre Draw");
                },
                "fnDrawCallback":function(){
                    $("#%s").show();
                    //$("#loading").hide();
                    //alert("Draw");
                },

                "fnInitComplete": function(oSettings, json) {$("#%s").show();}
            });
            setTrialDataWrapperWidth();
            window.addEventListener('resize', setTrialDataWrapperWidth);
        }
    );
    </script>
    """ % (tableId, tableId, tableId, tableId)

    return r


@app.route('/browseTrial/<trialId>/', methods=["GET", "POST"])
@dec_check_session()
def urlBrowseTrial(sess, trialId):
#===========================================================================
# Page for display of trial data.
#
    attList = dbUtil.getNodeAttributes(sess, trialId)
    nodeList = dbUtil.getNodes(sess, trialId)

    # Get all the attribute values:
    attValList = getAttributeColumns(sess, trialId, attList)

    # generate html table of the trial data:
    r = htmlDataTableMagic('trialData')
    r += '<p><table class="fptable" id="trialData" class="display" cellspacing="0" width="100%" style="display: none">'
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

    return dataPage(sess, content=r, title='Browse', trialId=trialId)


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
    from node t
      left join datum d1 on t.id = d1.node_id and d1.traitInstance_id = %s
      left join datum d2 on d1.node_id = d2.node_id and d1.traitInstance_id = d2.traitInstance_id and d2.timestamp > d1.timestamp
    where t.trial_id = %s and ((d2.timestamp is null and d1.traitInstance_id = %s) or d1.timestamp is null)
    order by row, col
    """
    #print qry
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
    #r = '\n<table id="trialData" class="display" cellspacing="0" width="100%" style="display:none">' if table else ''
    r = '\n<table class="fptable" id="trialData" class="display" cellspacing="0" width="100%">' if table else ''

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
            tuNotes = dbUtil.GetNodeNotes(sess, node.id)
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
    return dataPage(sess, content=r, title='Browse', trialId=trialId)


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
                                                          'Really Delete Trial {0}?'.format(trl.name)), trialId=trialId)
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
                return dataPage(sess, '', 'Trial Deleted', trialId=trialId)
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
        errMsg = fpTrait.CreateNewTrait(sess, trialId, request)
        if errMsg:
            return dataErrorPage(sess, errMsg)
        if trialId == 'sys':
            return FrontPage(sess, 'System trait created')
        return trialPage(sess, trialId)


@app.route('/trial/<trialId>/trait/<traitId>', methods=['GET', 'POST'])
@dec_check_session()
def urlTraitDetails(sess, trialId, traitId):
#===========================================================================
# Page to display/modify the details for a trait.
#
    return fpTrait.traitDetailsPageHandler(sess, request, trialId, traitId)


@app.route('/trial/<trialId>/uploadAttributes/', methods=['GET', 'POST'])
@dec_check_session()
def urlAttributeUpload(sess, trialId):
    if request.method == 'GET':
        return dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes')

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.updateTrialFile(sess, uploadFile, dbUtil.GetTrial(sess, trialId))
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
    r += "<p><table class='fptable' cellspacing='0' cellpadding='5'>"
    r += "<tr><th>{0}</th><th>{1}</th><th>{2}</th></tr>".format("Row", "Column", "Value")
    aVals = dbUtil.GetAttributeValues(sess, attId)
    for av in aVals:
        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(av.node.row, av.node.col, av.value)
    r += "</table>"
    return dataPage(sess, content=r, title='Attribute', trialId=trialId)


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

    r += "<p><table class='fptable' cellspacing='0' cellpadding='5'>"
    r += "<tr><th>Row</th><th>Column</th><th>Value</th><th>User</th><th>Time</th><th>Latitude</th><th>Longitude</th></tr>"
    for d in data:
        if typ == T_PHOTO:  # Special case for photos. Display a link to show the photo.
                            # Perhaps this should be done in Datum.getValue, but we don't have all info.
            if d.isNA():
                value = 'NA'
            else:
                # New method is to have filename in datum.txtValue, but this may not
                # be in place for all datums in the database. Older records may have a
                # txtValue either of 'xxx' or <trial name>/<digits>_<digits>.jpg.
                # New ones should be the file name, which should include more that one underscore.
                # Note we could go through the db and change txtValues of photo datums to the new way,
                # and then dispense with this if.
                fname = d.txtValue
                if fname.count('_') < 2 or fname.count('/') != 0:
                    fname = models.photoFileName(sess.GetUser(),
                                                 ti.trial_id,
                                                 ti.trait_id,
                                                 d.node.id,
                                                 ti.token,
                                                 ti.seqNum,
                                                 ti.sampleNum)
                value = '<a href=' + url_for('urlPhoto', filename=fname) + '>view photo</a>'
        else:
            value = d.getValue()

        r += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>".format(
            d.node.row, d.node.col, value, d.userid, util.epoch2dateTime(d.timestamp), d.gps_lat, d.gps_long)
    r += "</table>"
    return dataPage(sess, content=r, title='Score Set Data', trialId=ti.trial_id)


def makeZipArchive(sess, traitInstanceId, archiveFileName):
#-----------------------------------------------------------------------
# Create zip archive of all the photos for the given traitInstance.
    ti = dbUtil.getTraitInstance(sess, traitInstanceId)
    if ti.trait.type != T_PHOTO:
        return 'Not a photo trait'
    data = dbUtil.getTraitInstanceData(sess, traitInstanceId)
    try:
        with zipfile.ZipFile(archiveFileName, 'w') as myzip:
            for d in data:
                # Add all the photos in the traitInstance to the archive
                fname = models.photoFileName(sess.GetUser(),
                                             ti.trial_id,
                                             ti.trait_id,
                                             d.node.id,
                                             ti.token,
                                             ti.seqNum,
                                             ti.sampleNum)
                #print 'upload folder ' + app.config['PHOTO_UPLOAD_FOLDER'] + fname
                # Generate a name for the photo to have in the zip file. This needs to show row and col.
                node = dbUtil.getNode(sess, d.node_id)
                # MFK - we should allow for alternate file extensions, not assume ".jpg"
                archiveName = 'r' + str(node.row) + '_c' + str(node.col) + '.jpg'
                myzip.write(app.config['PHOTO_UPLOAD_FOLDER'] + fname, archiveName)
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

# For local testing:
if __name__ == '__main__':
    from os.path import expanduser
    app.config['SESS_FILE_DIR'] = expanduser("~") + '/proj/fpserver/fpa/fp_web_admin/tmp2'
    app.config['PHOTO_UPLOAD_FOLDER'] = expanduser("~") + '/proj/fpserver/photos/'
    app.config['FPLOG_FILE'] = expanduser("~") + '/proj/fpserver/fplog/fp.log'
    app.config['CATEGORY_IMAGE_FOLDER'] = expanduser("~") + '/proj/fpserver/catPhotos'
    app.config['CATEGORY_IMAGE_URL_BASE'] = 'file://' + expanduser("~") + '/proj/fpserver/catPhotos'

    # Setup logging:
    app.config['FP_FLAG_DIR'] = expanduser("~") + '/proj/fpserver/fplog/'
    util.initLogging(app, True)  # Specify print log messages

    app.run(debug=True, host='0.0.0.0', port=5001)

