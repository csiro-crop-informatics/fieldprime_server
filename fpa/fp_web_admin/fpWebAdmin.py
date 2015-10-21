# fpWebAdmin.py
# Michael Kirk 2013
#
#

#
# Standard or third party imports:
#
import os
import sys
import time
import traceback
import zipfile, ntpath
import MySQLdb as mdb
from flask import Flask, request, Response, redirect, url_for, render_template, g, make_response
from flask import jsonify
import simplejson as json
from functools import wraps


#
# Local imports:
#

# If we are running locally for testing, we need this magic for some imports to work:
if __name__ == '__main__':
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

import fpTrait
import fp_common.models as models    # why both this and dal!?
import fp_common.util as util
import fp_common.users as users
import fpTrial
import fpUtil
from fpUtil import hsafe

import fp_common.fpsys as fpsys
import trialProperties
from fp_common.const import *
from const import *
import datapage as dp
import websess
from fpRestApi import webRest

app = Flask(__name__)
app.register_blueprint(webRest)

#
# Load flask config:
# Note this is contained in a dedicated module in a separate package.
# When it was in a module in the same package as this file, the call ended
# up importing this file, which cause some problems when try to run this
# file a main. I believe this is because to import a module in a package
# seems require running the __init__ of the package. And the __init__ for
# this package imports app from this file, hence the re running of this file.
# That problem may go away, but it probably makes sense to have the config
# common between the fp_app_api and fp_web_admin packages anyway (which they
# are not currently).
#
try:
    app.config.from_object('fp_common.config')
except ImportError:
    print 'no fpAppConfig found'
    pass

# If env var FPAPI_SETTINGS is set then load configuration from the file it specifies:
app.config.from_envvar('FP_WEB_ADMIN_SETTINGS', silent=True)

# Import stats module, but note we need set env var first, we get value from app.config.
# NB this fails if in local mode, in which case we don't need to set the env var.
if __name__ != '__main__':
    os.environ['MPLCONFIGDIR'] = app.config['MPLCONFIGDIR']
import stats

# Load the Data Access Layer Module (which must be named in the config):
import importlib
dal = importlib.import_module(app.config['DATA_ACCESS_MODULE'])


#############################################################################################
###  FUNCTIONS: #############################################################################
#############################################################################################

@app.errorhandler(500)
def internalError(e):
#-------------------------------------------------------------------------------
# Trap for Internal Server Errors, these are typically as exception raised
# due to some problem in code or database. We log the details. Possibly should
# try to send an email (to me I guess) to raise the alarm..
#
    errmsg = 'Internal error:####################################\n{0}\nTraceback:\n{1}##########'.format(e, traceback.format_exc())
    util.flog(errmsg)
    return make_response('FieldPrime: An error has occurred\n', 500)

#@app.route('/crash', methods=['GET'])
#def crashMe():
#    x = 1 / 0
#    return 'hallo world'


def getMYSQLDBConnection(sess):
#-------------------------------------------------------------------------------
# Return mysqldb connection for user associated with session
#
    try:
        projectDBname = models.dbName4Project(sess.getProjectName())
        con = mdb.connect('localhost', models.APPUSR, models.APPPWD, projectDBname)
        return con
    except mdb.Error:
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
            if not sess.valid():  # Check if session is still valid
                if returnNoneSess:
                    return func(None, *args, **kwargs)
                return loginPage('Your session has timed out - please login again.')
            g.userName = sess.getUser()
            g.projectName = sess.getProjectName()
            return func(sess, *args, **kwargs)
        return inner
    return param_dec


def frontPage(sess, msg=''):
#-----------------------------------------------------------------------
# Return HTML Response for urlMain user page after login
#
    return dp.dataPage(sess, content=msg, title="FieldPrime")


def loginPage(error=None):
#-----------------------------------------------------------------------
# Response for login page, error shown as red message if present.
#
    return render_template('fieldprime.html', msg=error, title='FieldPrime Login')

def logoutPage(sess, msg):
#-----------------------------------------------------------------------
# Logs out and returns login page with msg.
#
    sess.close()
    g.userName = 'unknown'
    return loginPage(msg)


#####################################################################################################
# Trial page functions:
#

def htmlTrialTraitTable(trial):
#----------------------------------------------------------------------------------------------------
# Returns HTML for table showing all the traits for trial.
    if len(trial.traits) < 1:
        return "No traits configured"
    hdrs = ["Caption", "Description", "DataType", "Num ScoreSets", "Details"]
    trows = []
    for trt in trial.traits:
        trows.append([hsafe(trt.caption), hsafe(trt.description), TRAIT_TYPE_NAMES[trt.datatype],
             trt.getNumScoreSets(trial.id),
             fpUtil.htmlButtonLink2("Details",
                 url_for('urlTraitDetails', trialId=trial.id, traitId=trt.id, _external=True))])

    #xxx =  '''<button style="color: red" onClick="showIt('#fpTraitTable')">Press Me</button>'''
    return fpUtil.htmlDatatableByRow(hdrs, trows, 'fpTraitTable', showFooter=False)


def htmlTabScoreSets(sess, trialId):
#----------------------------------------------------------------------------------------------------
# Returns HTML for list of trial score sets.
# MFK - is there security issues showing user values in table - might they inject html scripts?
# Should protect in the datatables functions..
# See cgi.escape - but can't do automatically in htmlDatatable as we may want html in the
# table (eg links). Can either escape here as necessary (eg for values for text scores),
# or have htmlDatatables do it, but have parameters specifying columns to be excused.
#
# Maybe escape in the functions that get data for text traits?  Hopefully this is in one place only..
#
    trl = dal.getTrial(sess.db(), trialId)
    scoreSets = trl.getScoreSets()
    if len(scoreSets) < 1:
        htm =  "No trait score sets yet"
    else:
        # Make datatable of scoresets:
        hdrs = ["Trait", "Date Created", "Device Id", "fpId", "Score Data"]
        rows = []
        for ss in scoreSets:
            tis = ss.getInstances()
            firstTi = tis[0]   # check for none?
            row = []
            row.append(hsafe(firstTi.trait.caption))
            row.append(util.formatJapDateSortFormat(firstTi.dayCreated))
            row.append(firstTi.getDeviceId())
            row.append(ss.getFPId()) # was firstTi.seqNum
            samps = ''   # We show all the separate samples in a single cell
            for oti in tis:
                samps += "<a href={0}>&nbsp;Sample{1}&nbsp;:&nbsp;{2}&nbsp;scores&nbsp;(for&nbsp;{3}&nbsp;nodes)</a><br>".format(
                        url_for('urlScoreSetTraitInstance', traitInstanceId=oti.id), oti.sampleNum, oti.numData(),
                        oti.numScoredNodes())
            row.append(samps)
            rows.append(row)

        htm = fpUtil.htmlDatatableByRow(hdrs, rows, 'fpScoreSets', showFooter=False)
    # Add button to upload scores:
    htm += fpUtil.htmlButtonLink2("Upload ScoreSets", url_for("urlUploadScores", trialId=trialId))
    return htm

def htmlTabNodeAttributes(sess, trialId):
#----------------------------------------------------------------------------------------------------
# Returns HTML for trial attributes.
# MFK - improve this, showing type and number of values, also delete button? modify?
    attList = dal.getTrial(sess.db(), trialId).nodeAttributes
    out = ''
    if len(attList) < 1:
        out += "No attributes found"
    else:
        hdrs = ["Name", "Datatype", "Values"]
        rows = []
        for att in attList:
            valuesButton = fpUtil.htmlButtonLink2("values", url_for("urlAttributeDisplay", trialId=trialId, attId=att.id))
            rows.append([hsafe(att.name), TRAIT_TYPE_NAMES[att.datatype], valuesButton])
        out += fpUtil.htmlDatatableByRow(hdrs, rows, 'fpNodeAttributes', showFooter=False)

    # Add BROWSE button:
    out += '<p>'
    out += fpUtil.htmlButtonLink2("Browse Attributes", url_for("urlBrowseTrialAttributes", trialId=trialId))

    # Add button to upload new/modified attributes:
    out += fpUtil.htmlButtonLink2("Upload Attributes", url_for("urlAttributeUpload", trialId=trialId))

    return out

@app.route('/trialUpdate/<trialId>', methods=["POST"])
@dec_check_session()
def urlTrialNameDetailPost(sess, trialId):
#===========================================================================
# Page for trial creation.
#
    trialProperties.processPropertiesForm(sess, trialId, request.form)
    return "Trial Properties Updated on Server"

def htmlTabProperties(sess, trial):
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
    r += fpUtil.htmlFieldset(fpUtil.htmlForm(extrasForm, id='extras'))
    # JavaScript for AJAX form submission:
    r += '''
    <script>
    $(document).ready(function() {
        $("#extrasSubmit").click({url: "%s"}, fplib.extrasSubmit);
    });
    </script>\n''' % url_for('urlTrialNameDetailPost', trialId=trial.id)

    # Add DELETE button if admin: ------------------------------------------------
    if sess.adminRights():
        r += '<p>'
        r += fpUtil.htmlButtonLink2("Delete this trial", url_for("urlDeleteTrial", trialId=trial.id))
        r += '<p>'
    return r

def htmlTabTraits(sess, trial):
#--------------------------------------------------------------------
# Return HTML for trial name, details and top level config:
    createTraitButton = '<p>' + fpUtil.htmlButtonLink2("Create New Trait", url_for("urlNewTrait", trialId=trial.id))
    addSysTraitForm = '<FORM method="POST" action="{0}">'.format(url_for('urlAddSysTrait2Trial', trialId=trial.id))
    addSysTraitForm += '<select name="traitID" id="sysTraitSelId" ><option value="0">Select System Trait to add</option>'
    sysTraits = sess.getProject().getTraits()
    for st in sysTraits:
        for trt in trial.traits:   # Only add traits not already in trial
            if trt.id == st.id:
                break
        else:
            addSysTraitForm += '<option value="{0}">{1}</option>'.format(st.id, st.caption)
    addSysTraitForm += '</select> &nbsp; '
    addSysTraitForm += '''
    <script>
    function checkSelectionMade(selElementId) {
        var e = document.getElementById(selElementId);
        if (e.selectedIndex == 0) {
            alert('Please select a system trait to add');
            event.preventDefault()
        }
    }
    </script>
    '''
    addSysTraitForm += '<input type="submit" value="Add System Trait" onclick="checkSelectionMade(\'sysTraitSelId\')">'
    addSysTraitForm += '</form>'
    return fpUtil.htmlForm(htmlTrialTraitTable(trial)) + createTraitButton + addSysTraitForm

def htmlTabData(sess, trial):
#--------------------------------------------------------------------
# Return html chunk for data tab.
#
    # Javascript function to generate the href for the download links.
    # The generated link includes trialId and the user selected output options.
    # MFK, note we have problem with download link in that if the session has timed
    # out, the html for the login page will be downloaded instead of the actual data.
    # Could do a redirect? but have to pass all the params..
    #
    jscript = """
    <script>
    function addParams(url) {{
        var tdms = document.getElementById('tdms');
        var out = url;
        var first = true;
        // Add parameters indicating what to include in the download
        for (var i=0; i<tdms.length; i++)
            if (tdms[i].selected) {{
              out += first ? '?' : '&';
              first = false;
              out += tdms[i].value + '=1';
            }}
        return out;
    }};
    </script>
    """

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
    dl += "<div style='margin-bottom:20px'>"
    dl += "<select multiple='multiple' id='tdms'>";
    dl += "<option value='timestamp' selected='selected'>Timestamps</option>";
    dl += "<option value='user' selected='selected'>User Idents</option>"
    dl += "<option value='gps' selected='selected'>GPS info</option>"
    dl += "<option value='notes' selected='selected'>Notes</option>"
    dl += "<option value='attributes' selected='selected'>Attributes</option>"
    dl += "</select>"
    dl += "</div>"

    # Download wide format:
    dl += "<p><a href='dummy' download='{0}.tsv' onclick='this.href=addParams(\"{1}\")'>".format(trial.name, url_for("urlTrialDataWideTSV", trialId=trial.id))
    dl +=     "<button>Download Trial Data - wide format</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>(browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)</span>"

    # Download long format:
    dl += "<p><a href='dummy' download='{0}.tsv' onclick='this.href=addParams(\"{1}\")'>".format(trial.name, url_for("urlTrialDataLongForm", trialId=trial.id))
    dl +=     "<button>Download Trial Data - long format</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>(browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)</span>"

    # View plain text tsv long format (why?):
    dl += "<p><a href='dummy' onclick='this.href=addParams(\"{0}\")' onContextMenu='this.href=addParams(\"{0}\")'>".format(url_for("urlTrialDataWideTSV", trialId=trial.id))
    dl +=     "<button>View tab separated score data</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>Note data is TAB separated"

    # View wide format as datatable:
    dl += "<p><a href='dummy' onclick='this.href=addParams(\"{0}\")'>".format(url_for("urlTrialDataBrowse", trialId=trial.id))
    dl +=     "<button>Browse Trial Data</button></a>"
    return dl


class htmlChunkSet:
#-----------------------------------------------------------------------
# Class to manage a page made of separate "chunks", these can be
# displayed either as tabs or as fieldsets. Each chunk is a tuple of
# id, title, and html content.
#
    def __init__(self):
        self.chunks = []

    def addChunk(self, id, title, content):
        self.chunks.append((id,title,content))

    def htmlFieldSets(self):
        h = ''
        for c in self.chunks:
            h += fpUtil.htmlFieldset(c[2], c[1] + ':')
            h += '\n'
        return h

    def htmlTabs(self):
        h = '<script>  $(document).ready(function(){fplib.initTrialTabs();}) </script>\n'
        hlist = ''
        hcont = ''
        first = True
        for c in self.chunks:
            hlist += '  <li {2}><a href="#{0}" data-toggle="tab">{1}</a></li>\n'.format(
                c[0], c[1], 'class="active"' if first else '')
            hcont += '<div class="tab-pane {2}" id="{0}">\n{1}\n</div>\n\n'.format(
                c[0], c[2], 'active' if first else '')
            first = False

        # Tab headers:
        h += '<ul id="fpMainTabs" class="nav nav-tabs" data-tabs="tabs">\n{0}</ul>\n'.format(hlist)
        # Tab content divs:
        h += '<div id="my-tab-content" class="tab-content">\n{0}</div>'.format(hcont)
        return h

def htmlTrial(sess, trialId):
#-----------------------------------------------------------------------
# Returns the HTML for a top level page to display/manage a given trial.
# Or None if no trial with given id.
#
    trial = dal.getTrial(sess.db(), trialId)
    if trial is None: return None
    hts = htmlChunkSet()
    hts.addChunk('scoresets', 'Score Sets', htmlTabScoreSets(sess, trialId))
    hts.addChunk('natts', 'Node Attributes', htmlTabNodeAttributes(sess, trialId))
    hts.addChunk('traits', 'Traits', htmlTabTraits(sess, trial))
    hts.addChunk('data', 'Score Data', htmlTabData(sess, trial))
    hts.addChunk('properties', 'Properties', htmlTabProperties(sess, trial))
    # Handler for when tab is selected:
    # Bootstrap is managing the tabs, we use their hook to invoke an action
    # after a tab is shown. We need to reshow any datatables on the shown
    # tab since they can get messed up by being hidden. There is a problem
    # however in that this also gets sparked when the user gets to the page
    # via the back button. In this case the table doesn't exist yet, and
    # the dataTable() call inits the datatable, causing an error when it is
    # properly initialised later on.
    tabShownHandler = '''<script>
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
      var newtab = sessionStorage.getItem(fplib.STORAGE_TAG);
      if (newtab == '#traits') {
        if ($.fn.DataTable.isDataTable('#fpTraitTable'))
            $('#fpTraitTable').dataTable().fnAdjustColumnSizing();
      } else if (newtab == '#scoresets') {
         if ($.fn.DataTable.isDataTable('#fpScoreSets'))
            $('#fpScoreSets').dataTable().fnAdjustColumnSizing();
      } else if (newtab == '#natts') {
         if ($.fn.DataTable.isDataTable('#fpNodeAttributes'))
            $('#fpNodeAttributes').dataTable().fnAdjustColumnSizing();S
      }
    })
    </script>
    '''
    return tabShownHandler + hts.htmlTabs()


def trialPage(sess, trialId):
#----------------------------------------------------------------------------
# Return response that is the urlMain page for specified file, or error message.
#
    trialh = htmlTrial(sess, trialId)
    if trialh is None:
        trialh = "No trial selected"
    return dp.dataPage(sess, content=trialh, title='Trial Data', trialId=trialId)


@app.route('/trial/<trialId>', methods=["GET"])
@dec_check_session()
def urlTrial(sess, trialId):
#===========================================================================
# Page to display/modify a single trial.
#
    return trialPage(sess, trialId)


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
    return dp.dataPage(sess, content=apkListHtml, title='Download App', trialId=-1)


@app.route('/newTrial/', methods=["GET", "POST"])
@dec_check_session()
def urlNewTrial(sess):
#===========================================================================
# Page for trial creation.
#

    # Trial attribute stuff. We want table driven presentation of allowed trial attributes.
    extras = ''
    for tae in trialProperties.gTrialAttributes:
        extras += tae.htmlElement()
    if request.method == 'GET':
        return dp.dataTemplatePage(sess, 'newTrial.html', title='Create Trial', extraElements=extras)
    if request.method == 'POST':
        uploadFile = request.files['file']
        trl, errMsg = fpTrial.uploadTrialFile(sess, uploadFile, request.form.get('name'), request.form.get('site'),
                                      request.form.get('year'), request.form.get('acronym'),
                                      request.form.get(INDEX_NAME_1), request.form.get(INDEX_NAME_2))
        # Handle error (trl will be string error message):
        if trl is None:
            return dp.dataTemplatePage(sess, 'newTrial.html', title='Create Trial', msg = errMsg, extraElements=extras)
        #
        # All good. Trial created. Set extra trial attributes.
        # MFK in general we will need insert or update (merge)
        #
        trialProperties.processPropertiesForm(sess, trl.id, request.form)
        return frontPage(sess)

#MFK move to models
def getAllAttributeColumns(sess, trialId, fixedOnly=False):
#-----------------------------------------------------------------------
# Returns a list of columns of values for each attribute in attList, including
# the row column and barcode (which are stored in the node table rather than
# as attribute.  - each column
# being an array of attribute values with one entry for each node in the trial.
# The columns are in the same order as attList, and the column entries are
# ordered by row/col. Missing values are given as the empty string.
# NB - within columns the order is determined by node id.
#
# If fixedOnly is true, then only row, column and barcode are returned.
#

    # First get row, column, and barcode:
    con = getMYSQLDBConnection(sess)
    qry = 'select row, col, barcode from node where trial_id = %s order by id'
    cur = con.cursor()
    cur.execute(qry, trialId)
    colRow = []
    colCol = []
    colBarcode = []
    for row in cur.fetchall():
        colRow.append("" if row[0] is None else row[0])
        colCol.append("" if row[1] is None else row[1])
        colBarcode.append("" if row[2] is None else hsafe(row[2]))
    attValList = [colRow, colCol, colBarcode]
    trl = dal.getTrial(sess.db(), trialId)
    hdrs = [hsafe(trl.navIndexName(0)), hsafe(trl.navIndexName(1)), 'Barcode']

    if not fixedOnly:
        # And add the other attributes:
        trl = dal.getTrial(sess.db(), trialId)
        attList = trl.nodeAttributes
        qry = """
            select a.value from node n left join attributeValue a
            on n.id = a.node_id and a.nodeAttribute_id = %s
            where n.trial_id = %s
            order by n.id"""
        for att in attList:
            hdrs.append(hsafe(att.name))
            valList = []
            cur = con.cursor()
            cur.execute(qry, (att.id, trialId))
            for row in cur.fetchall():  # can we just store cur.fetchall()? Yes we could, but perhaps better this way
                valList.append("" if row[0] is None else hsafe(row[0]))
            attValList.append(valList)
            cur.close()
    return (hdrs, attValList)

@app.route('/browseTrial/<trialId>/', methods=["GET", "POST"])
@dec_check_session()
def urlBrowseTrialAttributes(sess, trialId):
#===========================================================================
# Page for display of trial data.
#
    (hdrs, cols) = getAllAttributeColumns(sess, int(trialId))
    return dp.dataPage(sess, content=fpUtil.htmlDatatableByCol(hdrs, cols, 'fpTrialAttributes'),
                       title='Browse', trialId=trialId)

def safeAppend(arr, val):
    arr.append(hsafe(val))

def getTrialDataHeadersAndRows(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes):
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
# MFK Cloned code from getTrialData above, that could be replaced with this
# Returns (headers, rows), headers a list, rows a list of lists
#
    # Get Trait Instances:
    tiList = dal.Trial.getTraitInstancesForTrial(sess.db(), trialId)  # get Trait Instances
    trl = dal.getTrial(sess.db(), trialId)
    valCols = trl.getDataColumns(tiList)                   # get the data for the instances

    # Headers:
    hdrs = []
    hdrs.append('fpNodeId')
    safeAppend(hdrs, dal.navIndexName(sess.db(), trialId, 0))
    safeAppend(hdrs, dal.navIndexName(sess.db(), trialId, 1))
    if showAttributes:
        attValList = trl.getAttributeColumns(trl.getAttributes())  # Get all the att vals in advance
        for tua in trl.nodeAttributes:
            safeAppend(hdrs, tua.name)
    for ti in tiList:
        tiName = "{0}_{1}.{2}.{3}".format(ti.trait.caption, ti.dayCreated, ti.seqNum, ti.sampleNum)
        safeAppend(hdrs, tiName)
        if showTime:
            safeAppend(hdrs, "{0}_timestamp".format(tiName))
        if showUser:
            safeAppend(hdrs, "{0}_user".format(tiName))
        if showGps:
            safeAppend(hdrs, "{0}_latitude".format(tiName))
            safeAppend(hdrs, "{0}_longitude".format(tiName))
    if showNotes:
        hdrs.append("Notes")

    # Data:
    rows = []
    nodeList = trl.getNodesSortedRowCol()
    for nodeIndex, node in enumerate(nodeList):
        nrow = [node.id, node.row, node.col]
        rows.append(nrow)

        # Attribute Columns:
        if showAttributes:
            for ind, tua in enumerate(trl.nodeAttributes):
                safeAppend(nrow, attValList[ind][nodeIndex])

        # Scores:
        for tiIndex, ti in enumerate(tiList):
            [val, timestamp, userid, lat, long] = valCols[tiIndex][nodeIndex]
            # Write the value:
            safeAppend(nrow, val)
            # Write any other datum fields specified:
            if showTime:
                safeAppend(nrow, timestamp)
            if showUser:
                safeAppend(nrow, userid)
            if showGps:
                safeAppend(nrow, lat)
                safeAppend(nrow, long)

        # Notes, as list separated by pipe symbols:
        if showNotes:
            notes = '"'
            tuNotes = node.getNotes()
            for note in tuNotes:
                notes += '{0}|'.format(note.note)
            notes += '"'
            safeAppend(nrow, notes)
    return hdrs, rows


def getDataWideForm(trial, showTime, showUser, showGps, showNotes, showAttributes):
#---------------------------------------------------------------------------------------
# Return score data for the trial in wide form.
# NB - I briefly moved this into models.py, but have brought it back as it's basically a view function.
#
# should Keep an eye on efficiency, see getDataLongForm in models.py, we iterate over scoresets and do a single sql query on each.
# Output is one line per datum:
# TraitName, ssId, nodeId, sampleNum, value [,time] [,user] [,gps]
#
#-----------------------------------------------------------------------
# Returns trial data as plain text tsv form - eg for download.
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
    tiList = trial.getTraitInstances()           # get Trait Instances
    valCols = trial.getDataColumns(tiList)       # get the data for the instances

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
    SEP = '\t'
    ROWEND = '\n'
    HROWEND = '\n'

    r = '# FieldPrime wide form trial data\n'
    r += '# Trial: {0}\n'.format(trial.path())
    r += '# Creation time: {0}\n'.format(time.strftime("%Y-%m-%d %H:%M:%S"))

    # Headers:
    r += 'fpNodeId' + SEP + trial.navIndexName(0) + SEP + trial.navIndexName(1)
    # xxx need to show row col even if attributes not shown?
    if showAttributes:
        trlAttributes = trial.getAttributes()
        attValList = trial.getAttributeColumns(trlAttributes)  # Get all the att vals in advance
        for tua in trlAttributes:
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
        r += SEP + "Notes"  # Putting notes at end in case some commas slip thru and mess up csv structure
    r += HROWEND

    # Data:
    nodeList = trial.getNodesSortedRowCol()
    for nodeIndex, node in enumerate(nodeList):
        # Row and Col:
        r += "{0}{3}{1}{3}{2}".format(node.id, node.row, node.col, SEP)
        # Attribute Columns:
        if showAttributes:
            for ind, tua in enumerate(trlAttributes):
                r += SEP
                r += attValList[ind][nodeIndex]
        # Scores:
        for tiIndex, ti in enumerate(tiList):
            [val, timestamp, userid, lat, lon] = valCols[tiIndex][nodeIndex]
            # Write the value:
            r += "{0}{1}".format(SEP, val)
            # Write any other datum fields specified:
            if showTime:
                r += "{0}{1}".format(SEP, timestamp)
            if showUser:
                r += "{0}{1}".format(SEP, userid)
            if showGps:
                r += "{0}{1}{0}{2}".format(SEP, lat, lon)

        # Notes, as list separated by pipe symbols:
        if showNotes:
            r += SEP + '"'
            tuNotes = node.getNotes()
            for note in tuNotes:
                r += '{0}|'.format(note.note)
            r += '"'

        # End the line:
        r += ROWEND
    return r


@app.route('/trial/<trialId>/data/', methods=['GET'])
@dec_check_session()
def urlTrialDataWideTSV(sess, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    trl = dal.getTrial(sess.db(), trialId)
    out = getDataWideForm(trl, showTime, showUser, showGps, showNotes, showAttributes)
    return Response(out, content_type='text/plain')

@app.route('/trial/<trialId>/data/browse', methods=['GET'])
@dec_check_session()
def urlTrialDataBrowse(sess, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    (headers, rows) = getTrialDataHeadersAndRows(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes)
    r = fpUtil.htmlDatatableByRow(headers, rows, 'fpTrialData', showFooter=False)
    return dp.dataPage(sess, content=r, title='Browse', trialId=trialId)

@app.route('/trial/<trialId>/datalong/', methods=['GET'])
@dec_check_session()
def urlTrialDataLongForm(sess, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showAttributes = request.args.get("attributes")
    trl = dal.getTrial(sess.db(), trialId)
    out = trl.getDataLongForm(showTime, showUser, showGps, showAttributes)
    return Response(out, content_type='text/plain')

@app.route('/deleteTrial/<trialId>/', methods=["GET", "POST"])
@dec_check_session()
def urlDeleteTrial(sess, trialId):
#===========================================================================
# Page for trial deletion. Display trial stats and request confirmation
# of delete.
#
# MFK - replace the post part of this with a DELETE?
    trl = dal.getTrial(sess.db(), trialId)
    def getHtml(msg=''):
        out = '<div style="color:red">{0}</div><p>'.format(msg);  # should be red style="color:red"
        out += 'Trial {0} contains:<br>'.format(trl.name)
        out += '{0} Score Sets<br>'.format(trl.numScoreSets())
        out += '{0} Scores<br>'.format(trl.numScores())
        out += '<p>Admin Password required: <input type=password name="password">'
        out += '<p>Do you really want to delete this trial?'
        out += '<p> <input type="submit" name="yesDelete" value="Yes, Delete">'
        out += '<input type="submit" name="noDelete" style="color:red" color:red value="Goodness me NO!">'
        return dp.dataPage(sess, title='Delete Trial',
                        content=fpUtil.htmlHeaderFieldset(fpUtil.htmlForm(out, post=True),
                                                          'Really Delete Trial {0}?'.format(trl.name)), trialId=trialId)
    if request.method == 'GET':
        return getHtml()
    if request.method == 'POST':
        out = ''
        if request.form.get('yesDelete'):
            if not request.form.get('password'):
                 return getHtml('You must provide a password')
            # Check session password is still correct:
            if not passwordCheck(sess, request.form.get('password')):
                return getHtml('Password is incorrect')
            # Require admin permissions for delete:
            if not sess.adminRights():
                return getHtml('Insufficient permissions to delete trial')
            else:
                # Delete the trial:
                dal.Trial.delete(sess.db(), trialId)
                return dp.dataPage(sess, '', 'Trial Deleted', trialId=trialId)
        else:
            # Do nothing:
            return frontPage(sess)

@app.route('/trial/<trialId>/newTrait/', methods=["GET", "POST"])
@dec_check_session()
def urlNewTrait(sess, trialId):
#===========================================================================
# Page for trait creation.
#
    if trialId == 'sys':
        trialId = -1
    if request.method == 'GET':
        # NB, could be a new sys trait, or trait for a trial. Indicated by trialId which will be
        # either -1 or the trial id respectively. NB dataTemplatePage doesn't check trialId,
        # but looks in sess instead. NB newTrait.html does check trialId.
        return dp.dataTemplatePage(sess, 'newTrait.html', trialId=trialId, traitTypes=TRAIT_TYPE_TYPE_IDS, title='New Trait')

    if request.method == 'POST':
        errMsg = fpTrait.createNewTrait(sess, trialId, request)
        if errMsg:
            return dp.dataErrorPage(sess, errMsg, trialId)
        if trialId == -1:
            return frontPage(sess, 'System trait created')
        return trialPage(sess, trialId)


@app.route('/trial/<trialId>/trait/<traitId>', methods=['GET', 'POST'])
@dec_check_session()
def urlTraitDetails(sess, trialId, traitId):
#===========================================================================
# Page to display/modify the details for a trait.
#
    return fpTrait.traitDetailsPageHandler(sess, request, trialId, traitId)

@app.route('/trial/<trialId>/uploadScoreSets/', methods=['GET', 'POST'])
@dec_check_session()
def urlUploadScores(sess, trialId):
    if request.method == 'GET':
        return dp.dataTemplatePage(sess, 'uploadScores.html', title='Upload Scores', trialId=trialId)

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.uploadScores(sess, uploadFile, dal.getTrial(sess.db(), trialId))
        if res is not None and 'error' in res:
            return dp.dataTemplatePage(sess, 'uploadScores.html', title='Load Attributes', msg = res['error'], trialId=trialId)
        else:
            return trialPage(sess, trialId)


@app.route('/trial/<trialId>/uploadAttributes/', methods=['GET', 'POST'])
@dec_check_session()
def urlAttributeUpload(sess, trialId):
    if request.method == 'GET':
        return dp.dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes', trialId=trialId)

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.updateTrialFile(sess, uploadFile, dal.getTrial(sess.db(), trialId))
        if res is not None and 'error' in res:
            return dp.dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes', msg = res['error'], trialId=trialId)
        else:
            return trialPage(sess, trialId)

@app.route('/trial/<trialId>/attribute/<attId>/', methods=['GET'])
@dec_check_session()
def urlAttributeDisplay(sess, trialId, attId):
    tua = dal.getAttribute(sess.db(), attId)
    out = "<b>Attribute</b> : {0}".format(tua.name)
    out += "<br><b>Datatype</b> : " + TRAIT_TYPE_NAMES[tua.datatype]
    # Construct datatable:
    trl = dal.getTrial(sess.db(), trialId)  # MFK what is the cost of getting trial object?
    hdrs = ["fpNodeId", hsafe(trl.navIndexName(0)), hsafe(trl.navIndexName(1)), "Value"]
    rows = []
    aVals = tua.getAttributeValues()
    for av in aVals:
        rows.append([av.node.id, av.node.row, av.node.col, hsafe(av.value)])
    out += fpUtil.htmlDatatableByRow(hdrs, rows, 'fpAttValues', showFooter=False)

    return dp.dataPage(sess, content=out, title='Attribute', trialId=trialId)

#######################################################################################################
### USERS STUFF: ######################################################################################
#######################################################################################################

def manageUsersHTML(sess, msg=None):
# Show list of ***REMOVED*** users for current project, with delete and add functionality.
# Current login must have admin rights to the project.
#
# admin tab needs security thinking - any admin functionality must have security check before
# it is provided. An admin tab itself on the main page should be OK since server checks admin
# access before sending page with that tab. But server processing of any user interaction on
# that tab must recheck. This can be done by checking the existing session - the user must have
# the right access.
    # Check security:
    if not sess.adminRights():
        return ''
    cont = '<button onClick=fplib.userSaveChanges("{0}")>Save Changes</button>'.format(
                url_for("urlUsersPost", projectName=sess.getProjectName()))
    cont += '<button onClick=fplib.userAdd()>Add User</button>'

    # NB We could get user list for this project, here, but we now rely on ajax call from the browser:
    cont += '<script>$(fplib.fillUserTable)</script>'  # javascript will fill the table using ajax call
    # NB store url for table data in attribute for javascript to access.
    cont += '<table id=userTable data-url="{0}"></table>'.format(url_for("urlUsersPost", projectName=sess.getProjectName()))
    if msg is not None:
        cont += '<font color="red">{0}</font>'.format(msg)
    out = fpUtil.htmlFieldset(cont, 'Manage ***REMOVED*** Users')
    return out

@app.route('/project/<projectName>/user/<ident>', methods=['DELETE'])
@dec_check_session()
def urlUserDelete(sess, projectName, ident):
    if not sess.adminRights() or projectName != sess.getProjectName():
        return fpUtil.badJuju(sess, 'No admin rights')
    errmsg = fpsys.deleteUser(sess.getProjectName(), ident)
    if errmsg is not None:
        return jsonify({"error":errmsg})
    else:
        return jsonify({"status":"good"})

@app.route('/project/<projectName>/users', methods=['GET'])
@dec_check_session()
def urlUsersGet(sess, projectName):
    if not sess.adminRights():
        return badJsonJuju(sess, 'No admin rights')
    users, errMsg = fpsys.getProjectUsers(sess.getProjectName())
    if errMsg is not None:
        return badJsonJuju(sess, errMsg)
    retjson = []
    for login, namePerms in sorted(users.items()):
        retjson.append([url_for('urlUserDelete', projectName=projectName, ident=login),
                        login, namePerms[0], namePerms[1]])
    print 'json dumps:'
    print json.dumps(retjson)
    return jsonify({'users':retjson})

@app.route('/project/<projectName>/users', methods=['POST'])
@dec_check_session()
def urlUsersPost(sess, projectName):
    if not sess.adminRights():
        return badJuju(sess, 'No admin rights')
    # Check admin rights:
    try:
        userData = request.json
    except Exception, e:
        print 'exception'

    if not userData:
        return Response('Bad or missing JSON')
    util.flog("ajaxData:\n" + json.dumps(userData))
    print 'ajax ' + json.dumps(userData)
    # Go thru userData and process - it might be nice to try using
    # http CRUD/REST operations here. Identify a user in a project as resource
    # /project/<project>/user/<userid>. But for the moment we're doing it all here.
    # We will however use separate functions for what would be the individual
    # CRUD operations.
    errMsgs = []
    newUsers = userData.get('create')
    if newUsers is not None:
        for user, perms in newUsers.iteritems():
            errmsg = fpsys.addUserToProject(user, sess.getProjectName(), perms)
            if errmsg is not None:
                errMsgs.append(('create', user, errmsg))
    updateUsers = userData.get('update')
    if updateUsers is not None:
        for user, perms in updateUsers.iteritems():
            errmsg = fpsys.updateUser(user, sess.getProjectName(), perms)
            if errmsg is not None:
                errMsgs.append(('update', user, errmsg))

    return jsonify({"status":"ok", "errors":errMsgs})

@app.route('/project/<projectName>/details/', methods=['GET', 'POST'])
@dec_check_session()
def urlUserDetails(sess, projectName):
    if projectName != sess.getProjectName():
        return badJuju(sess, 'Incorrect project name')
    if not sess.adminRights():
        return badJuju(sess, 'No admin rights')

    def theFormAgain(op=None, msg=None):
        cname = dal.getSystemValue(sess.db(), 'contactName') or ''
        cemail = dal.getSystemValue(sess.db(), 'contactEmail') or ''
        return dp.dataTemplatePage(sess, 'profile.html', contactName=cname, contactEmail=cemail,
                    title="Admin", op=op, errMsg=msg,
                    usersHTML=manageUsersHTML(sess, msg if op is 'manageUser' else None))

    title = "Profile"
    if request.method == 'GET':
        return theFormAgain()
    if request.method == 'POST':
        op = request.args.get('op')
        form = request.form
        if op == 'contact':
            contactName = form.get('contactName')
            contactEmail = form.get('contactEmail')
            if not (contactName and contactEmail):
                return dp.dataTemplatePage(sess, 'profile.html', op=op, errMsg="Please fill out all fields", title=title)
            else:
                dal.setSystemValue(sess.db(), 'contactName', contactName)
                dal.setSystemValue(sess.db(), 'contactEmail', contactEmail)
                return dp.dataTemplatePage(sess, 'profile.html', op=op, contactName=contactName, contactEmail=contactEmail,
                           errMsg="Contact details saved", title=title)

        elif op == 'newpw' or op == 'setAppPassword':
            # Changing admin or app password:
            # MFK bug here: if we prompt with err message, the contact values are missing.
            currUser = sess.getUser()
            oldPassword = form.get("password")
            if not users.systemPasswordCheck(sess.getProjectName(), oldPassword):
                return logoutPage(sess, "Password is incorrect")
            newpassword1 = form.get("newpassword1")
            newpassword2 = form.get("newpassword2")
            if not (oldPassword and newpassword1 and newpassword2):
                return theFormAgain(op=op, msg="Please fill out all fields")
            if newpassword1 != newpassword2:
                return dp.dataTemplatePage(sess, 'profile.html', op=op, errMsg="Versions of new password do not match.", title=title)

            # OK, all good, change their password:
            try:
                # New way - get a connection for the system project user for changing the password.
                # This to avoid having the fpwserver user needing ability to set passwords (access to mysql database).
                # Ideally however, we should be able to have admin privileges for ***REMOVED*** users, so remembering the system
                # user password is not compulsory.
                usrname = models.dbName4Project(sess.getProjectName())
                usrdb = usrname
                con = mdb.connect('localhost', usrname, oldPassword, usrdb)

                cur = con.cursor()
                msg = ''
                if op == 'newpw':
                    cur.execute("set password for %s@localhost = password(%s)", (models.dbName4Project(sess.getProjectName()), newpassword1))
                    msg = 'Admin password reset successfully'
                elif op == 'setAppPassword':
                    cur.execute("REPLACE system set name = 'appPassword', value = %s", newpassword1)
                    con.commit()
                    msg = 'Scoring password reset successfully'
                con.close()
                return frontPage(sess, msg)
            except mdb.Error, e:
                return logoutPage(sess, 'Unexpected error trying to change password')
        elif op == 'manageUsers':
            return theFormAgain(op='manageUser', msg='I\'m Sorry Dave, I\'m afraid I can\'t do that')
        else:
            return badJuju(sess, 'Unexpected operation')

#######################################################################################################
### END USERS STUFF: ##################################################################################
#######################################################################################################

@app.route('/FieldPrime/<projectName>/systemTraits/', methods=['GET', 'POST'])
@dec_check_session()
def urlSystemTraits(sess, projectName):
#---------------------------------------------------------------------------
#
#
    if request.method == 'GET':
        # System Traits:
        sysTraits = sess.getProject().getTraits()
        sysTraitListHtml = "No system traits yet" if len(sysTraits) < 1 else fpTrait.traitListHtmlTable(sysTraits)
        r = fpUtil.htmlFieldset(
            fpUtil.htmlForm(sysTraitListHtml) +
            fpUtil.htmlButtonLink("Create New System Trait", url_for("urlNewTrait", trialId='sys')),
            "System Traits")
        return dp.dataPage(sess, title='System Traits', content=r, trialId=-1)


@app.route('/trial/<trialId>/addSysTrait2Trial/', methods=['POST'])
@dec_check_session()
def urlAddSysTrait2Trial(sess, trialId):
#-------------------------------------------------------------------------------
# MFK need check valid traitId and preferably trialId too (it could be hacked).
#
    # Get and validate traitId:
    traitId = 0
    try:
        traitId = int(request.form['traitID'])
    except Exception:
        return dp.dataErrorPage(sess, "Invalid system trait specified", trialId)
    if traitId <= 0:
        return dp.dataErrorPage(sess, "Invalid system trait specified", trialId)

    errMsg = fpTrait.addTrait2Trial(sess, trialId, traitId)
    if errMsg:
        return dp.dataErrorPage(sess, errMsg, trialId)
    # If all is well, display the trial page:
    return trialPage(sess, trialId)

def hackyPhotoFileName(sess, ti, d):
# This should eventually be replaced by call do models.photoFileName, but:
# New method is to have filename in datum.txtValue, but this may not
# be in place for all datums in the database. Older records may have a
# txtValue either of 'xxx' or <trial name>/<digits>_<digits>.jpg.
# New ones should be the file name, which should include more that one underscore.
# Note we could go through the db and change txtValues of photo datums to the new way,
# and then dispense with this if.
    fname = d.txtValue
    if fname.count('_') < 2 or fname.count('/') != 0:
        fname = models.photoFileName(sess.getProjectName(),
                                     ti.trial_id,
                                     ti.trait_id,
                                     d.node.id,
                                     ti.token.tokenString(),
                                     ti.seqNum,
                                     ti.sampleNum)
    return fname


def htmlNumericScoreSetStats(data, name):
#--------------------------------------------------------------------------
# Return some html stats/charts for numeric data, which is assumed to have
# at least one non-NA value. In JS context we are assuming the data is available
# in global var fplib.tmpScoredata. This function just for neatness, really
# just part of urlScoreSetTraitInstance.
#
    oStats = '' #<button type="button" onclick=fplib.stuff()>Click me</button>'
    oStats += '''
    <script>
    $(document).ready(function() {
        // Get array of the non-NA values, and get some stats.
        var values = [];
        var valsWithNodeIds = []; // store vals with node ids, some redundancy with values array.
        var rows = fplib.tmpScoredata.rows;
        var min, max;
        var count=0, sum=0;
        for (var i = 0; i<rows.length; ++i) {
            var val = rows[i][3];
            if (typeof val === 'number') {
                values.push(val);
                valsWithNodeIds.push([rows[i][0], val]);
                if (min === undefined || val < min) min = val;
                if (max === undefined || val > max) max = val;
                sum += val;
                ++count;
            }
        }
        fplib.tmpScoredata.values = values;
        fplib.tmpScoredata.valsWithNodeIds = valsWithNodeIds;
        fplib.tmpScoredata.min = min;
        fplib.tmpScoredata.max = max;

        var statsDiv = document.getElementById("statsText");
        statsDiv.appendChild(document.createTextNode("Mean value is " + parseFloat(sum/count).toFixed(2)));
        statsDiv.appendChild(document.createElement("br"));
        statsDiv.appendChild(document.createTextNode("Min value: " + parseFloat(min).toFixed(2)));
        statsDiv.appendChild(document.createElement("br"));
        statsDiv.appendChild(document.createTextNode("Max value: " + parseFloat(max).toFixed(2)));

    });
    </script>
    '''

    # Boxplot after table:
    oStats += '<h3>Boxplot:</h3>'
    oStats += stats.htmlBoxplot(data)

    # Histogram(s):
    width = 900
    height = 500

    # D3 histogram MFK - note use of non standard CDN - could store library locally instead.
    d3hist = '''
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js"></script>
    <h3>Histogram:</h3>
    <div id="hist_div" style="width: %dpx; height: %dpx;"></div>
    <script>
        $(document).ready(function() {
            fplib.drawHistogram(fplib.tmpScoredata.values, fplib.tmpScoredata.min, fplib.tmpScoredata.max, "hist_div", %d, %d);
        });
    </script>
    ''' % (width, height, width, height)
    oStats += d3hist

    scatters = '''
    <div id=scatterPlotWrapper>
    <h3>Scatter Plot:</h3>
    ''' + '''<div id="scatter_div" style="width: %dpx; height: %dpx;"></div>''' % (width, height+20) + '''
    <script>
    function scatterPlot () {
        var url = this.value;
        var yname = this.options[this.selectedIndex].text;
        // go get the data:
        fplib.getUrlData(url, function (data) {
            fplib.drawScatterPlot(fplib.tmpScoredata.valsWithNodeIds, '%s', data, yname, 'scatter_div', %d, %d);
        });
    };''' % (name, width, height) + '''
    $(document).ready(function() {
        var sdiv = document.getElementById("scatter_div");
        ''' + "sdiv.appendChild(document.createTextNode('X Axis:\u00a0' + '%s'));" % (name) + '''
        sdiv.appendChild(document.createElement('br'));
        sdiv.appendChild(document.createTextNode("Y Axis:\u00a0"));
        var atts = fplib.tmpScoredata.atts;
        var attSelect = document.createElement("select");
        attSelect.onchange = scatterPlot;
        sdiv.appendChild(attSelect);
        for (var i=0; i<atts.length; ++i) {
            if (atts[i].datatype === 0 || atts[i].datatype === 1) { // restrict to numeric
                var option = document.createElement("option");
                option.text = atts[i].name;
                option.value = atts[i].url;
                attSelect.appendChild(option);
            }
        }
    });
    </script>
    </div>
    '''
    oStats += scatters
    return oStats

#
# Example of getting response from another URL:
# NB to use, uncomment this and change the current
# method to:
# @app.route('/scoreSet2/<traitInstanceId>/', methods=['GET'])
# @dec_check_session()
# def urlScoreSetTraitInstance2(sess, traitInstanceId):
#
#
# import requests
# @app.route('/scoreSet/<traitInstanceId>/', methods=['GET'])
# @dec_check_session()
# def urlScoreSetTraitInstance(sess, traitInstanceId):
#     newurl = url_for('urlScoreSetTraitInstance2', traitInstanceId=traitInstanceId, _external=True)
#     print 'newurl:' + newurl
#     f = request.cookies.get('sid')
#     cooky = {'sid':f}
#     return requests.get(newurl, cookies=cooky).content

@app.route('/scoreSet/<traitInstanceId>/', methods=['GET'])
@dec_check_session()
def urlScoreSetTraitInstance(sess, traitInstanceId):
#-------------------------------------------------------------------------------
# Try client graphics.
# Include table data as JSON
# Display the data for specified trait instance.
# NB deleted data are shown (crossed out), not just the latest for each node.
# MFK this should probably display RepSets, not individual TIs
#
    ti = dal.getTraitInstance(sess.db(), traitInstanceId)
    trl = ti.trial
    typ = ti.trait.datatype
    name = ti.trait.caption + '_' + str(ti.seqNum) + ', sample ' + str(ti.sampleNum) # MFK add name() to TraitInstance
    data = ti.getData()
    out = ''

    # Name:
    out += "<h2>Score Set: {0}</h2>".format(name)
    #r += "<br>Datatype : " + TRAIT_TYPE_NAMES[tua.datatype]

    # For photo score sets add button to download photos as zip file:
    if typ == T_PHOTO:
        out += ("<p><a href={1} download='{0}'>".format(ntpath.basename(photoArchiveZipFileName(sess, traitInstanceId)),
                                                 url_for('urlPhotoScoreSetArchive', traitInstanceId=traitInstanceId))
         + "<button>Download Photos as Zip file</button></a>"
         + " (browser permitting, Chrome and Firefox OK. For Internet Explorer right click and Save Link As)")

    # Get data:
    hdrs = ('fpNodeId', trl.navIndexName(0), trl.navIndexName(1), 'Value', 'User', 'Time', 'Latitude', 'Longitude')
    rows = []
    for idx, d in enumerate(data):
        # Is this an overwritten datum?
        overWritten = idx > 0 and data[idx-1].node_id == data[idx].node_id

        # Special case for photos. Display a link to show the photo.
        # Perhaps this should be done in Datum.getValue, but we don't have all info.
        if typ == T_PHOTO:
            if d.isNA():
                value = 'NA'
            else:
#               fname = d.txtValue    This is what we should be doing, when hack is no longer necessary
                fname = hackyPhotoFileName(sess, ti, d)
                value = '<a href=' + url_for('urlPhoto', filename=fname, trialId=ti.getTrialId()) + '>view photo</a>'
        else:
            value = d.getValue()
        rows.append([d.node.id, d.node.row, d.node.col,
                     value if not overWritten else ('<del>' + str(value) + '</del>'),
                     d.userid, d.getTimeAsString(), d.gps_lat, d.gps_long])

    # Make list of urls for trial attributes:  MFK we should put urls for traitInstances as well
    nodeAtts = []
    for nat in ti.trial.nodeAttributes:
        nodeAtts.append(
            {"name":nat.name,
             "url":url_for('webRest.urlAttributeData', projectName=sess.getProjectName(), attId=nat.id),
             "datatype":nat.datatype})

    # Embed the data as JSON in the page (with id "ssdata"):
    jtable = {"headers":hdrs, "rows":rows, "atts":nodeAtts}
    dtab = '''<script type="application/json" id="ssdata">
    {0}
    </script>'''.format(json.dumps(jtable))

    # Script to create DataTable of the data:
    dtab += '<div id="dtableDiv"></div>'
    #dtab += '<link rel="stylesheet" type="text/css" href="//cdn.datatables.net/1.10.0/css/jquery.dataTables.css">'
    #dtab += '\n<script type="text/javascript" language="javascript" src="//cdn.datatables.net/1.10.0/js/jquery.dataTables.js"></script>'
    dtab +=  '''<script>
        $(document).ready(function() {
            fplib.tmpScoredata = JSON.parse(document.getElementById("ssdata").text); // use global var as needed elsewhere
            stab = fplib.makeDataTable(fplib.tmpScoredata, 'sstable', 'dtableDiv');
        });
    </script>'''
    out += fpUtil.htmlFieldset(dtab, 'Data:')

    # Stats:
    numDeleted = 0
    numNA = 0
    numScoredNodes = 0
    isNumeric = (typ == T_INTEGER or typ == T_DECIMAL)
    numSum = 0
    for idx, d in enumerate(data):
        overWritten = idx > 0 and data[idx-1].node_id == data[idx].node_id
        if overWritten:
            numDeleted += 1
        else:
            numScoredNodes += 1
            if d.isNA():
                numNA += 1
            elif isNumeric:
                numSum += d.getValue()
    numValues = numScoredNodes - numNA
    statsText = 'Number of scored nodes: {0} (including {1} NAs)<br>'.format(numScoredNodes, numNA)
    statsText += 'Number of nodes with non-NA scores: {0}<br>'.format(numValues)
    statsText += 'Number of overwritten scores: {0}<br>'.format(numDeleted)
    oStats = fpUtil.htmlDiv(statsText, 'statsText')

    if isNumeric and numValues > 0:
        oStats += htmlNumericScoreSetStats(data, name)

    #
    out += fpUtil.htmlFieldset(fpUtil.htmlDiv(oStats, "statsDiv"), 'Statistics:')
    return dp.dataPage(sess, content=out, title='Score Set Data', trialId=ti.trial_id)


def makeZipArchive(sess, traitInstanceId, archiveFileName):
#-----------------------------------------------------------------------
# Create zip archive of all the photos for the given traitInstance.
    ti = dal.getTraitInstance(sess.db(), traitInstanceId)
    if ti.trait.datatype != T_PHOTO:
        return 'Not a photo trait'
    data = ti.getData(True)
    try:
        with zipfile.ZipFile(archiveFileName, 'w') as myzip:
            for d in data:
                # Add all the photos in the traitInstance to the archive
                fname = hackyPhotoFileName(sess, ti, d)

                #print 'upload folder ' + app.config['PHOTO_UPLOAD_FOLDER'] + fname
                # Generate a name for the photo to have in the zip file. This needs to show row and col.
                node = dal.getNode(sess.db(), d.node_id)
                # MFK - we should allow for alternate file extensions, not assume ".jpg"
                archiveName = 'r' + str(node.row) + '_c' + str(node.col) + '.jpg'
                myzip.write(app.config['PHOTO_UPLOAD_FOLDER'] + fname, archiveName)
    except Exception, e:
        return 'A problem occurred:\n{0}\n{1}'.format(type(e), e.args)
    return None

def photoArchiveZipFileName(sess, traitInstanceId):
#-----------------------------------------------------------
# Generate file name for zip of photos in traitInstance.
    ti = dal.getTraitInstance(sess.db(), traitInstanceId)
    return app.config['PHOTO_UPLOAD_FOLDER'] + '{0}_{1}_{2}.zip'.format(sess.getProjectName(), ti.trial.name, traitInstanceId)

@app.route("/photo/scoreSetArchive/<traitInstanceId>", methods=['GET'])
@dec_check_session()
def urlPhotoScoreSetArchive(sess, traitInstanceId):
#--------------------------------------------------------------------
# Return zipped archive of the photos for given traitInstance
    archFname = photoArchiveZipFileName(sess, traitInstanceId)
    errMsg = makeZipArchive(sess, traitInstanceId, archFname)
    if errMsg is not None:
        ti = dal.getTraitInstance(sess.db(), traitInstanceId)
        return dp.dataErrorPage(sess, errMsg, ti.getTrialId())  # MFK This doesnt work! response is saved as downloaded file
    resp = make_response(open(archFname).read())
    resp.content_type = "image/jpeg"
    os.remove(archFname)    # delete the file
    return resp


@app.route("/trial/<trialId>/photo/<filename>", methods=['GET'])
@dec_check_session()
def urlPhoto(sess, trialId, filename):
# This is a way to provide images to authenticated user only.
# An alternative would be to put the image in a static folder,
# but then (I think) they must be visible to everyone.
# Note this method is presumably slower to run than just having
# a static URL. I'm not sure whether the performance hit is significant.
    fullpath = app.config['PHOTO_UPLOAD_FOLDER'] + filename
    if not os.path.isfile(fullpath):
        return dp.dataErrorPage(sess, "Can't find fat file {0}".format(fullpath), trialId)
    resp = make_response(open(fullpath).read())
    resp.content_type = "image/jpeg"
    return resp


@app.route('/FieldPrime/user/<userName>/', methods=['GET'])
@dec_check_session()
def urlUserHome(sess, userName):
    return frontPage(sess)

@app.route('/FieldPrime/project/<project>/', methods=['GET'])
@dec_check_session()
def urlProject(sess, project):
#-----------------------------------------------------------------------
# URL handler for user choice from project list.
#
# Need to check userName is of session user, and that they have access to the project,
# and find what permissions they have. We can't just use the username and project from
# the URL since they could just be typed in, BY A BAD PERSON. Session should be a ***REMOVED*** login.
#
    if project is not None:
        if sess.getLoginType() != LOGIN_TYPE_***REMOVED***:
            return badJuju(sess, 'Unexpected login type')
        projList, errMsg = fpsys.getProjects(sess.getUser())
        if errMsg is not None:
            return badJuju(sess, errMsg)
        elif not projList:
            return badJuju(sess, 'Unexpected project')
        else:
            for prj in projList:
                if prj.projectName == project:
                    # All checks passed, set the project as specified:
                    sess.setProject(prj.projectName, prj.dbname, prj.access)
                    return frontPage(sess)
            # No access to this project - bad user!
            return badJuju(sess, 'no access to project')


@app.route('/logout', methods=["GET"])
@dec_check_session()
def urlLogout(sess):
    sess.close()
    return redirect(url_for('urlMain'))

def badJuju(sess, msg):
#-----------------------------------------------------------------------
# Close the session and return the message. Intended as a return for a HTTP request
# after something bad (and possibly suspicious) has happened.
    sess.close()
    return "Something bad has happened: " + msg


def badJsonJuju(sess, error=None):
#-----------------------------------------------------------------------
# Close the session and return the message. Intended as a return for a HTTP request
# after something bad (and possibly suspicious) has happened.
    sess.close()
    message = {
            'status': 500,
            'message': 'An snail error occurred: ' + error
    }
    resp = jsonify(message)
    resp.status_code = 500
    return resp


@app.route('/info/<pagename>', methods=["GET"])
@dec_check_session(True)
def urlInfoPage(sess, pagename):
    g.rootUrl = url_for('urlMain')
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)

def passwordCheck(sess, password):
#-----------------------------------------------------------------------
# Check password is valid for current user/loginType
#
    if sess.getLoginType() == LOGIN_TYPE_SYSTEM:
        return users.systemPasswordCheck(sess.getUser(), password)
    elif sess.getLoginType() == LOGIN_TYPE_***REMOVED***:
        return users.***REMOVED***PasswordCheck(sess.getUser(), password)


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
# the frontPage, but shows the URL for the op.
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

        if not error:
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
                resp = make_response(frontPage(sess))
                resp.set_cookie(COOKIE_NAME, sess.sid())      # Set the cookie
                return resp

        # Error return
        return loginPage(error)

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

    app.run(debug=True, threaded=True, host='0.0.0.0', port=5001)

