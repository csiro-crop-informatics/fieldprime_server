# fpWebAdmin.py
# Michael Kirk 2013 - 2016
# Tim Erwin 2016
# Web site endpoints to administer and use FieldPrime
#

#
# Standard or third party imports:
#
from __future__ import print_function
import os
import sys
import time
import traceback
import zipfile, ntpath
import MySQLdb as mdb
from flask import Flask, request, Response, redirect, url_for, render_template, g, \
    make_response, session
from flask import jsonify
import simplejson as json
from functools import wraps, update_wrapper
import requests

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
import fpTrial
import fpUtil
from fpUtil import hsafe

import fp_common.fpsys as fpsys
import trialProperties
from fp_common.const import *
import datapage as dp
import websess
from fpRestApi import webRest, fprGetError, fprHasError, fprData
from fpAppWapi import appApi
import forms
import fpSess
from const import *

app = Flask(__name__)
app.register_blueprint(webRest)
app.register_blueprint(appApi)
app.secret_key = '** REMOVED **'

#
# The FieldPrime server can be run in various ways, and accordingly we may need to detect
# part of the URL. The FP_RUNTIME environment var should be used to indicate what configuration
# we are running as. An alternative would be to put the prefix itself in the environment.
#
FP_RUNTIME = os.environ.get('FP_RUNTIME', '')
PREURL = '/fieldprime' if FP_RUNTIME == 'docker' else ''

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
    app.config.from_object('config')
except ImportError:
    print('no fpAppConfig found')
    pass

# If env var FPAPI_SETTINGS is set then load configuration from the file it specifies:
app.config.from_envvar('FP_WEB_ADMIN_SETTINGS', silent=True)

# Load the Data Access Layer Module (which must be named in the config):
import importlib
dal = importlib.import_module(app.config['DATA_ACCESS_MODULE'])

class FPWebAdminException(Exception):
    pass



#############################################################################################
###  FUNCTIONS: #############################################################################
#############################################################################################

mkdbg = (lambda msg : print('fpsrver:'+msg)) if (__name__ == '__main__') else (lambda msg : None)

# def mkdbg(msg):
#     if __name__ == '__main__':
#         print msg

# @app.errorhandler(401)
# def custom_401(error):
#     print('in custom_401')
#     return Response('<Why access is denied string goes here...>', 401)
#                     #, {'WWWAuthenticate':'Basic realm="Login Required"'})

def getUserProjectInfo():
    usr = proj = None
    if hasattr(g, 'userName'):
        usr = g.userName
    if hasattr(g, 'sess'):
        proj = g.sess.getProjectName()
    return 'User:{0} Project:{1}'.format(usr, proj)

@app.errorhandler(500)
def internalError(e):
#-------------------------------------------------------------------------------
# Trap for Internal Server Errors, these are typically as exception raised
# due to some problem in code or database. We log the details. Possibly should
# try to send an email (to me I guess) to raise the alarm..
#
    errmsg = '### Internal error:#################################\n'
    # Get user and project names if available: NB must check references or lose error context, can't use try.
    errmsg += '{}\n'.format(getUserProjectInfo())
    errmsg += '{0}\n{1}##########'.format(e, traceback.format_exc())
    util.flog(errmsg)
    return make_response('FieldPrime: An error has occurred\n'+errmsg.replace('\n', '<br>'), 500)


def getMYSQLDBConnection(sess):
#-------------------------------------------------------------------------------
# Return mysqldb connection for user associated with session
#
    try:
        projectDBname = models.dbName4Project(sess.getProjectName())
        from config import FP_MYSQL_HOST, FP_MYSQL_PORT
        con = mdb.connect(host=FP_MYSQL_HOST, port=FP_MYSQL_PORT, user=models.fpDBUser(), passwd=models.fpPassword(), db=projectDBname)
        return con
    except mdb.Error:
        return None

def nocache(f):
# Decorator to and no-cache directive to response.
# Probably a good idea to use when response contains authentication tokens.
    def new_func(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return update_wrapper(new_func, f)

        
def session_check(projIdParamName='projId', trialIdParamName=None):
#-------------------------------------------------------------------------------------------------
# Decorator to check if in valid session. If not, send the login page.
# Generates function that has session as first parameter.
#
# A project must be identified. This is either in the parameters with key
# given by projIdParamName, or in the flask session if there is no such parameter.
#
# Ultimately all endpoints that reference a specific project should have the
# project id specified in the URL. That's not the case currently for historical
# reasons, but we should aim to make it so, and then remove the use of the
# flask session.
#
    def param_dec(func):
        @wraps(func)
        def inner(*args, **kwargs):
            app.logger.debug("session_check")
            
            # Get token, validate, and get user:
            token = request.cookies.get(NAME_COOKIE_TOKEN)
            if token is None:
                app.logger.debug("session_check: No token")
                return loginPage('Not logged in')
            resp = requests.get(url_for('webRest.urlGetTokenUser', _external=True), timeout=5,
                                headers={"Authorization": "fptoken " + token})
            try:
                jresp = resp.json()
                if resp.status_code != HTTP_OK:
                    return loginPage(fprGetError(jresp))
                data = jresp.get('data')
                userId = data.get('userId')
            except Exception as e:
                app.logger.debug('session_check: exception getting json response: {}'.format(e))
                return loginPage('Unexpected error')
                
            projId = kwargs.get(projIdParamName)
            if projId is None: 
                projId = session.get('projId')
                mkdbg('Got projId from session: {}'.format(projId))
            if projId is None: return loginPage('Unexpected error')
            
            try:
                sess = fpSess.FPsess(userId, projId)  # make session
            except Exception as e:
                return loginPage(str(e))
            
            fpsys.fpSetupG(g, userIdent=sess.getUserIdent(), projectName=sess.getProjectName())
            g.sess = sess           
            g.sessProjId = projId
            g.fpUrl = fpUrl

            # Get trial if specified:
            if trialIdParamName is not None:
                trialId = kwargs.get(trialIdParamName)
                try:
                    trial = dal.getTrial(sess.db(), trialId)
                except:
                    trial = None
                if trial is None:
                    return errorScreenInSession('trial not found')
                g.sessTrial = trial
                
            ret = make_response(func(sess, *args, **kwargs))
            # Reset the token:
            newToken = resp.cookies[NAME_COOKIE_TOKEN]
            mkdbg('newToken {}'.format(newToken))
            ret.set_cookie(NAME_COOKIE_TOKEN, newToken)
            return ret
        return inner
    return param_dec

def logged_in_check(func):
#-------------------------------------------------------------------------------------------------
# Decorator to check if we have a valid login token, and to get the user
# Generates function that has user (object from fpsys) as first parameter.
#
    @wraps(func)
    def inner(*args, **kwargs):
        app.logger.debug("logged_in_check")
        mkdbg('logged_in_check')
        
        # Get token, validate, and get user:
        token = request.cookies.get(NAME_COOKIE_TOKEN)
        if token is None:
            return loginPage('Not logged in')
        resp = requests.get(url_for('webRest.urlGetTokenUser', _external=True), timeout=5,
                            headers={"Authorization": "fptoken " + token})
        try:
            jresp = resp.json()
            if resp.status_code != HTTP_OK:
                return loginPage(fprGetError(jresp))
            data = jresp.get('data')
            userId = data.get('userId')
        except Exception as e:
            mkdbg('exception getting json response: {}'.format(e))
            return loginPage('unexpected error')
            
        g.fpUrl = fpUrl
        user = fpsys.User.getByLogin(userId)
        if user is None:
            return loginPage('Specified user not found')
        g.user = user
        
        ret = make_response(func(user, *args, **kwargs))
        # Reset the token:
        newToken = resp.cookies[NAME_COOKIE_TOKEN]
        ret.set_cookie(NAME_COOKIE_TOKEN, newToken)
        return ret
    return inner

def fpUrl(endpoint, sess=None, **kwargs):
# Adds projId param to url generator. The projId is retrieved from sess if present.
# Otherwise it is got from the g.sessProjId global var.
#
    if sess is not None: projId = sess.getProjectId()
    else: projId = g.sessProjId
    #return url_for(endpoint, projId=projId, _external=True, **kwargs)
    return url_for(endpoint, projId=projId, **kwargs)

# @app.route(PREURL+'/crash', methods=['GET'])
# @session_check()
# def crashMe(sess):
#     x = 1 / 0
#     return 'hallo world'

def frontPage(msg=''):
#-----------------------------------------------------------------------
# Return HTML Response for urlMain user page after login
#
    return dp.dataPage(content=msg, title="FieldPrime")


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
             fpUtil.htmlButtonLink("Details",
                 fpUrl('urlTraitDetails', trialId=trial.id, traitId=trt.id, _external=True))])
    #xxx =  '''<button style="color: red" onClick="showIt('#fpTraitTable')">Press Me</button>'''
    return fpUtil.htmlDatatableByRow(hdrs, trows, 'fpTraitTable', showFooter=False)

@app.route(PREURL+'/test', methods=["GET"])
@session_check()
def urlTest(sess):
    #return  dp.dataPageTest(sess, content=htmlTabScoreSets(sess, 1), title='foo', trialId=1)
    return render_template('foo.html', title="test")

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
        htm =  "<p>No trait score sets yet"
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
                        fpUrl('urlScoreSetTraitInstance', sess=sess, trialId=trialId, traitInstanceId=oti.id), oti.sampleNum, oti.numData(),
                        oti.numScoredNodes())
            row.append(samps)
            rows.append(row)

        htm = fpUtil.htmlDatatableByRow(hdrs, rows, 'fpScoreSets', showFooter=False)
    # Add button to upload scores:
    htm += '<p>'
    htm += fpUtil.htmlButtonLink("Upload ScoreSets", fpUrl("urlUploadScores", trialId=trialId))
    return htm

def htmlTabNodeAttributes(sess, trialId):
#----------------------------------------------------------------------------------------------------
# Returns HTML for trial attributes.
# MFK - improve this, showing type and number of values, also delete button? modify?
    attList = dal.getTrial(sess.db(), trialId).getAttributes()
    out = ''
    if len(attList) < 1:
        out += "No attributes found"
    else:
        hdrs = ["Name", "Datatype", "Values"]
        rows = []
        for att in attList:
            valuesButton = fpUtil.htmlButtonLink("values", fpUrl("urlAttributeDisplay", trialId=trialId, attId=att.id))
            rows.append([hsafe(att.name), TRAIT_TYPE_NAMES[att.datatype], valuesButton])
        out += fpUtil.htmlDatatableByRow(hdrs, rows, 'fpNodeAttributes', showFooter=False)

    # Add BROWSE button:
    out += '<p>'
    out += fpUtil.htmlButtonLink("Browse Attributes", fpUrl('urlBrowseTrialAttributes', sess, trialId=trialId))

    # Add button to upload new/modified attributes:
    out += fpUtil.htmlButtonLink("Upload Attributes", fpUrl('urlAttributeUpload', sess, trialId=trialId))

    return out

def htmlTabProperties(sess, trial):
#--------------------------------------------------------------------
# Return HTML for trial name, details and top level config:
    projId = sess.getProjectId()
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
    extrasForm += fpUtil.htmlButton("Save", id="extrasSubmit", color='btn-success', type='submit')
    r += fpUtil.htmlFieldset(fpUtil.htmlForm(extrasForm, formId='extras'))
    # JavaScript for AJAX form submission:
    r += '''<script>$(fplib.ajax.setupAjaxForm(false,"extras","{}","put"))</script>'''.format(
               url_for('webRest.urlUpdateTrial', _external=True,
                       projId=projId, trialId=trial.id))

    # Add DELETE button if admin: ------------------------------------------------
    if sess.adminRights():
        r += '<p>'
        r += fpUtil.htmlButtonLink("Delete this trial", url_for("urlDeleteTrial", projId=projId, trialId=trial.id), color='btn-danger')
        r += '<p>'
    return r

def htmlTabTraits(sess, trial):
#--------------------------------------------------------------------
# Return HTML for trial name, details and top level config:
    createTraitButton = '<div class="top20">{}</div>'.format(
        fpUtil.htmlButtonLink("Create New Trial Trait", fpUrl("urlNewTrait", sess, trialId=trial.id)))
    adder = '<div class="top20" style="display:inline-block;">'
    adder += '<form class="form-inline">'
    adder += '''
    <script>
    function handleAddTrait() {
        var e = document.getElementById('trait2add');
        if (e.selectedIndex == 0) {
            alert('Please select a project trait to add');
            //event.preventDefault()
        } else {
            fplib.ajax.doAjax(e.value, "PUT", fplib.ajax.jsonSuccessReload);
        }
    }
    </script>
    '''
    adder += '<select class="form-control" style="min-width:300" name="tdd" id="trait2add"> '
    adder += '<option value="0">Select Project Trait to add</option>'
    sysTraits = sess.getProject().getTraits()
    print('len sysTraits {}'.format(len(sysTraits)))
    for st in sysTraits:
        for trt in trial.traits:   # Only add traits not already in trial
            if trt.id == st.id:
                break
        else:
            adder += '<option value="{0}">{1}</option>'.format(
                url_for('webRest.urlTrialProjectTrait', projId=sess.getProjectId(), trialId=trial.getId(), traitId=st.id), st.caption)
    adder += '</select>'
    adder += fpUtil.htmlButton("Add Existing Project Trait", click='handleAddTrait()')
    adder += '</form>'
    adder += '</div>'
    
    return fpUtil.htmlForm(htmlTrialTraitTable(trial)) + adder + createTraitButton

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
    dl += "<p><a href='dummy' download='{0}.tsv' onclick='this.href=addParams(\"{1}\")'>".format(trial.name, fpUrl("urlTrialDataWideTSV", sess, trialId=trial.id))
    dl +=     "<button class='fpButton'>Download Trial Data - wide format</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>(NB For Internet Explorer you may need to right click and Save Link As)</span>"

    # Download long format:
    dl += "<p><a href='dummy' download='{0}.tsv' onclick='this.href=addParams(\"{1}\")'>".format(trial.name, fpUrl("urlTrialDataLongForm", sess, trialId=trial.id))
    dl +=     "<button class='fpButton'>Download Trial Data - long format</button></a><br />"
    dl +=     "<span style='font-size: smaller;'>(NB For Internet Explorer you may need to right click and Save Link As)</span>"

    # View wide format as datatable:
    loc = fpUrl("urlTrialDataBrowse", sess, trialId=trial.id)
    dl += "<p>" + fpUtil.htmlFpButtonLink("Browse Trial Data",
         location='addParams(\'{0}\')'.format(loc), quoteLocation=False)
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
    return dp.dataPage(content=trialh, title='Trial Data', trialId=trialId)

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>', methods=["GET"])
@session_check()
def urlTrial(sess, projId, trialId):
#===========================================================================
# Page to display/modify a single trial.
#
    return trialPage(sess, trialId)

@app.route(PREURL+'/downloadApp/', methods=['GET'])
@logged_in_check
def urlDownloadApp(sess):
#-----------------------------------------------------------------------
# Display page for app download.
# Provide a link for each .apk file in the static/apk folder
#
    mkdbg('in downloadApp')
    from fnmatch import fnmatch
    apkDir = app.root_path + '/static/apk'
    apkListHtml = 'To download the app, right click on a link and select "Save Link As":'
    l = os.listdir(apkDir)
    for fname in l:
        if fnmatch(fname, '*.apk'):
            apkListHtml += '<p><a href="{0}">{1}</a>'.format(url_for('static', filename = 'apk/'+fname), fname)
    return dp.dataPage(content=apkListHtml, title='Download App', trialId=-1)


@app.route(PREURL+'/projects/<int:projId>/newTrial/', methods=["GET", "POST"])
@session_check()
def urlNewTrial(sess, projId):
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
        return frontPage()

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
# Raises FPWebAdminException on error.

    # First get row, column, and barcode:
    con = getMYSQLDBConnection(sess)
    qry = 'select row, col, barcode from node where trial_id = %s order by id'
    cur = con.cursor()
    cur.execute(qry, (trialId,))
    colRow = []
    colCol = []
    colBarcode = []
    for row in cur.fetchall():
        colRow.append("" if row[0] is None else row[0])
        colCol.append("" if row[1] is None else row[1])
        colBarcode.append("" if row[2] is None else hsafe(row[2]))
    attValList = [colRow, colCol, colBarcode]
    trl = dal.getTrial(sess.db(), trialId)
    if trl is None:
        raise FPWebAdminException('Cannot get trial')
    hdrs = [hsafe(trl.navIndexName(0)), hsafe(trl.navIndexName(1)), 'Barcode']

    if not fixedOnly:
        # And add the other attributes:
        attList = trl.getAttributes()
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
            con.close()
    return (hdrs, attValList)

@app.route(PREURL+'/projects/<int:projId>/browseTrial/<trialId>/', methods=["GET"])
@session_check()
def urlBrowseTrialAttributes(sess, projId, trialId):
#===========================================================================
# Page for display of trial data.
#
    try:
        (hdrs, cols) = getAllAttributeColumns(sess, int(trialId))
    except FPWebAdminException as e:
        return errorScreenInSession(str(e))
    return dp.dataPage(content=fpUtil.htmlDatatableByCol(hdrs, cols, 'fpTrialAttributes'),
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
# Raises FPWebAdminException on error.
    # Get Trait Instances:
    tiList = dal.Trial.getTraitInstancesForTrial(sess.db(), trialId)  # get Trait Instances
    trl = dal.getTrial(sess.db(), trialId)
    if trl is None:
        raise FPWebAdminException('Cannot get trial')
    valCols = trl.getDataColumns(tiList, quoteStrings=False, metadata=True) # get the data for the instances

    # Headers:
    hdrs = []
    metas = []
    hdrs.append('fpNodeId')
    safeAppend(hdrs, dal.navIndexName(sess.db(), trialId, 0))
    safeAppend(hdrs, dal.navIndexName(sess.db(), trialId, 1))
    if showAttributes:
        attValList = trl.getAttributeColumns(trl.getAttributes())  # Get all the att vals in advance
        for tua in trl.getAttributes():
            safeAppend(hdrs, tua.name)
    for ti in tiList:
        tiName = "{0}_{1}.{2}.{3}".format(ti.trait.caption, ti.dayCreated, ti.seqNum, ti.sampleNum)
        safeAppend(hdrs, tiName)
        if showTime:
            metas.append(len(hdrs))
            safeAppend(hdrs, "{0}_timestamp".format(tiName))
        if showUser:
            metas.append(len(hdrs))
            safeAppend(hdrs, "{0}_user".format(tiName))
        if showGps:
            metas.append(len(hdrs))
            safeAppend(hdrs, "{0}_latitude".format(tiName))
            metas.append(len(hdrs))
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
            for ind, tua in enumerate(trl.getAttributes()):
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
            notes = ''
            #notes = '"'
            tuNotes = node.getNotes()
            for note in tuNotes:
                if notes: notes += '|'
                notes += note.note
            #notes += '"'
            safeAppend(nrow, notes)
    return hdrs, rows, metas

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
        # Also surrounded by quotes - this may be a problem, and are we doing this for text scores?
        # MFK - I think we do need quotes, but then presumable need to escape quotes within
        # NB we also remove line ends.
        if showNotes:
            r += SEP + util.removeLineEnds(util.quote('|'.join([n.note for n in node.getNotes()])))

        # End the line:
        r += ROWEND
    return r


@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/data/', methods=['GET'])
@session_check(trialIdParamName='trialId')
def urlTrialDataWideTSV(sess, projId, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    #trl = dal.getTrial(sess.db(), trialId)
    trial = g.sessTrial
    out = getDataWideForm(trial, showTime, showUser, showGps, showNotes, showAttributes)
    return Response(out, content_type='text/plain')

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/data/browse', methods=['GET'])
@session_check()
def urlTrialDataBrowse(sess, projId, trialId):
#---------------------------------------------------------------------------------------
# Return page with datatable for the trial in wide form.
#
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showNotes = request.args.get("notes")
    showAttributes = request.args.get("attributes")
    try:
        (headers, rows, metas) = getTrialDataHeadersAndRows(sess, trialId, showAttributes, showTime, showUser, showGps, showNotes)
    except FPWebAdminException as e:
        return errorScreenInSession(str(e))
    # Probably should return array with type code for each column rather than metas
    r = fpUtil.htmlDatatableByRow(headers, rows, 'fpTrialData', showFooter=False, extraOptions='')
    r += '<script type="text/javascript" language="javascript" src="%s"></script>' % url_for('static', filename='lib/jquery.doubleScroll.js')
#     r += '''<script>jQuery(
#     function() {
#         var table = $('#fpTrialData').DataTable();
#         new $.fn.dataTable.Buttons(table,
#             {
#                 buttons: [
#                     { extend:'csvHtml5', exportOptions: {columns: ':visible'}},
#                     {   extend:'colvisGroup',
#                         action: function() {
#                            var hid;
#                            return function(){
#                                if (hid == null) {
#                                    hid = %s;
#                                    this.columns(hid).visible(false);
#                                } else {
#                                    this.columns(hid).visible(true);
#                                    hid = null;
#                                }
#                                //$('#scrooll_div').doubleScroll();
#                            }
#                         }(),
#                         text:'Metadata',
#                     }
#                 ]
#             });
#         table.buttons().container().appendTo($('.col-sm-6:eq(0)', table.table().container()));
#         // Double scrollbar:
#         //$('#fpTrialData').wrap("<div id='scrooll_div'></div>");
#         //$('#scrooll_div').doubleScroll();
#     });</script>''' % str(metas)
    return dp.dataPage(content=r, title='Browse', trialId=trialId)

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/datalong/', methods=['GET'])
@session_check()
def urlTrialDataLongForm(sess, projId, trialId):
    showGps = request.args.get("gps")
    showUser = request.args.get("user")
    showTime = request.args.get("timestamp")
    showAttributes = request.args.get("attributes")
    trl = dal.getTrial(sess.db(), trialId)
    out = trl.getDataLongForm(showTime, showUser, showGps, showAttributes)
    return Response(out, content_type='text/plain')

@app.route(PREURL+'/projects/<int:projId>/deleteTrial/<int:trialId>/', methods=["GET", "POST"])
@session_check(trialIdParamName='trialId')
def urlDeleteTrial(sess, projId, trialId):
#===========================================================================
# Page for trial deletion. Display trial stats and request confirmation
# of delete.
#
# MFK - replace the post part of this with a DELETE?
    trl = g.sessTrial
    def getHtml(msg=''):
        out = '<div style="color:red">{0}</div><p>'.format(msg);  # should be red style="color:red"
        out += 'Trial {0} contains:<br>'.format(trl.name)
        out += '{0} Score Sets<br>'.format(trl.numScoreSets())
        out += '{0} Scores<br>'.format(trl.numScores())
        out += '<p>Admin Password required: <input type=password name="password">'
        out += '<p>Do you really want to delete this trial?'
        out += '<p> <input type="submit" name="yesDelete" value="Yes, Delete">'
        out += '<input type="submit" name="noDelete" style="color:red" color:red value="Goodness me NO!">'
        return dp.dataPage(title='Delete Trial',
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
            if not fpsys.userPasswordCheck(sess.getUserIdent(), request.form.get('password')):
                return getHtml('Password is incorrect')
            # Require admin permissions for delete:
            if not sess.adminRights():
                return getHtml('Insufficient permissions to delete trial')
            else:
                # Delete the trial:
                dal.Trial.delete(sess.db(), trialId)
                return dp.dataPage('', 'Trial Deleted', trialId=trialId)
        else:
            # Do nothing:
            return frontPage()

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/newTrait/', methods=["GET", "POST"])
@session_check()
def urlNewTrait(sess, projId, trialId):
#===========================================================================
# Page for trait creation.
#
    if trialId == 0:
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
            return frontPage('System trait created')
        return trialPage(sess, trialId)


@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/trait/<traitId>', methods=['GET', 'POST'])
@session_check(trialIdParamName='trialId')
def urlTraitDetails(sess, projId, trialId, traitId):
#===========================================================================
# Page to display/modify the details for a trait.
#
    trial = g.sessTrial
    return fpTrait.traitDetailsPageHandler(sess, request, trial, trialId, traitId)

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/uploadScoreSets/', methods=['GET', 'POST'])
@session_check()
def urlUploadScores(sess, projId, trialId):
    if request.method == 'GET':
        return dp.dataTemplatePage(sess, 'uploadScores.html', title='Upload Scores', trialId=trialId)

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.uploadScores(sess, uploadFile, dal.getTrial(sess.db(), trialId))
        if res is not None and 'error' in res:
            return dp.dataTemplatePage(sess, 'uploadScores.html', title='Load Attributes', msg = res['error'], trialId=trialId)
        else:
            return trialPage(sess, trialId)


@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/uploadAttributes/', methods=['GET', 'POST'])
@session_check()
def urlAttributeUpload(sess, projId, trialId):
    if request.method == 'GET':
        return dp.dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes', trialId=trialId)

    if request.method == 'POST':
        uploadFile = request.files['file']
        res = fpTrial.updateTrialFile(sess, uploadFile, dal.getTrial(sess.db(), trialId))
        if res is not None and 'error' in res:
            return dp.dataTemplatePage(sess, 'uploadAttributes.html', title='Load Attributes', msg = res['error'], trialId=trialId)
        else:
            return trialPage(sess, trialId)

@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/attribute/<attId>/', methods=['GET'])
@session_check()
def urlAttributeDisplay(sess, projId, trialId, attId):
    natt = dal.getAttribute(sess.db(), attId)
    out = "<b>Attribute</b> : {0}".format(natt.name)
    out += "<br><b>Datatype</b> : " + TRAIT_TYPE_NAMES[natt.datatype]
    # Construct datatable:
    trl = dal.getTrial(sess.db(), trialId)  # MFK what is the cost of getting trial object?
    hdrs = ["fpNodeId", hsafe(trl.navIndexName(0)), hsafe(trl.navIndexName(1)), "Value"]
    rows = []
    aVals = natt.getAttributeValues()
    for av in aVals:
        node = av.getNode()
        rows.append([node.id, node.row, node.col, hsafe(av.getValueAsString())])
    out += fpUtil.htmlDatatableByRow(hdrs, rows, 'fpAttValues', showFooter=False)

    return dp.dataPage(content=out, title='Attribute', trialId=trialId)

#######################################################################################################
### USERS STUFF: ######################################################################################
#######################################################################################################

def manageUsersHTML(sess, msg=None):
# Project user list section of project administration form
# Show list of Ldap users for current project, with delete and add functionality.
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
    projId=sess.getProjectId()
    cont = '<button onClick=fplib.userSaveChanges("{0}")>Save Changes</button>'.format(
                url_for("webRest.urlAddProjectUser", projId=projId))

    cont += '<button onClick=fplib.userAdd()>Add User</button>'
    cont += '''
    <script>
        $(function(){fplib.fillUserTable("%s")});
    </script>
    ''' % (url_for("webRest.urlGetProjectUsers", projId=projId))
    cont += '<table id=userTable data-url="{0}"></table>'.format(url_for("webRest.urlGetProjectUsers", projId=projId))
    
    if msg is not None:
        cont += '<font color="red">{0}</font>'.format(msg)
    out = fpUtil.htmlFieldset(cont, 'Manage Ldap Users')
    return out

@app.route(PREURL+'/projects/<int:projId>/details/', methods=['GET', 'POST'])
@session_check()
def urlProjectAdmin(sess, projId):
# This is the project administration form.
    if not sess.adminRights():
        return badJuju('No admin rights')
    usr = sess.getUser()
    if usr is None:
        return badJuju('No user found')
    showPassChange = usr.allowPasswordChange()

    def theFormAgain(op=None, msg=None):
        cname = dal.getSystemValue(sess.db(), 'contactName') or ''
        cemail = dal.getSystemValue(sess.db(), 'contactEmail') or ''
        return dp.dataTemplatePage(sess, 'profile.html', contactName=cname, contactEmail=cemail,
                    title="Admin", op=op, errMsg=msg, passChange=showPassChange,
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
                return dp.dataTemplatePage(sess, 'profile.html', op=op, errMsg="Please fill out all fields",
                                           passChange=showPassChange, title=title)
            else:
                dal.setSystemValue(sess.db(), 'contactName', contactName)
                dal.setSystemValue(sess.db(), 'contactEmail', contactEmail)
                return dp.dataTemplatePage(sess, 'profile.html', op=op, contactName=contactName, contactEmail=contactEmail,
                           errMsg="Contact details saved", passChange=showPassChange, title=title)

        elif op == 'newpw' or op == 'setAppPassword':
            # Changing admin or app password:
            # MFK bug here: if we prompt with err message, the contact values are missing.
            oldPassword = form.get("password")
            newpassword1 = form.get("newpassword1")
            newpassword2 = form.get("newpassword2")
            if not (oldPassword and newpassword1 and newpassword2):
                return theFormAgain(op=op, msg="Please fill out all fields")
            if newpassword1 != newpassword2:
                return dp.dataTemplatePage(sess, 'profile.html', op=op, errMsg="Versions of new password do not match.",
                                           passChange=showPassChange, title=title)

            # OK, all good, change their password:
            currUser = sess.getUserIdent()
            if not fpsys.userPasswordCheck(g.userName, oldPassword):
                return logoutPage(sess, "Password is incorrect")
            user = fpsys.User.getByLogin(currUser)
            msg = user.setPassword(newpassword1)
            if msg is None:
                msg = 'Password reset successfully'
            return frontPage(msg)
        elif op == 'manageUsers':
            return theFormAgain(op='manageUser', msg='I\'m Sorry Dave, I\'m afraid I can\'t do that')
        else:
            return badJuju('Unexpected operation')

#######################################################################################################
### END USERS STUFF: ##################################################################################
#######################################################################################################

#######################################################################################################
### FPADMIN STUFF: ####################################################################################
#######################################################################################################

def formElements4ProjectManagement():
# Form elements for new project form.
    return [
        forms.formElement('Separate Database', 'Create database for this project', 'ownDatabase', 'ncid',
                    etype=forms.formElement.RADIO, typeSpecificData={'yes':'true', 'no':'false'}, default='true'),
        forms.formElement('Project Name', 'Name for new project', 'projectName', 'pnameId',
                   etype=forms.formElement.TEXT),
        forms.formElement('Contact', 'Name of contact person', 'contactName', 'contId', etype=forms.formElement.TEXT),
        forms.formElement('Contact Email', 'Email address of contact person',
                    'contactEmail', 'emailId', etype=forms.formElement.TEXT),
        forms.formElement('Project admin login', 'User to get admin access to the new project',
                          'adminLogin', 'adminLoginId', etype=forms.formElement.TEXT)
    ]

def formElements4UserManagement():
# Create user form:
# Let's try do this with ajax from client direct to rest api.
# To obviate the client having to login let's pass a token - but it would
# have to be a token for the userid, not the server power user..
# Use the jQuery .submit function.
# Perhaps this function should just return the form elements list -
# because we want to access the element ids without remembering and retyping them
# (but may not be able to as these needed on receiving response, but could regenerate),
# and also because the parameters to makeModalForm, and the presentation may need to vary.
# This could be just a global variable, but by placing it in a function, I'm assuming
# it will only get generated when needed.
#
    return [
        forms.formElement('Login Type', 'Specify user type', 'loginType', 'xncid',
            etype=forms.formElement.RADIO,
            typeSpecificData={'CSIRO Ldap':LOGIN_TYPE_LDAP, 'FieldPrime':LOGIN_TYPE_LOCAL}, default=LOGIN_TYPE_LOCAL),
        forms.formElement('Login ident', 'Login name', 'ident', 'xpnameId',
                          etype=forms.formElement.TEXT),
        forms.formElement('Password', 'Initial password for the new user', 'password', 'fpcuPassword',
                          etype=forms.formElement.TEXT),
        forms.formElement('User Name', 'Full name of new user', 'fullname', 'xcontId',
                          etype=forms.formElement.TEXT),
        forms.formElement('User Email', 'Email address of new user', 'email', 'xemailId',
                          etype=forms.formElement.TEXT)
    ]

@app.route(PREURL+'/fpadmin/', methods=['GET'])
@logged_in_check
def urlFPAdmin(usr):
    # Check permissions:
    if not usr.hasPermission(fpsys.User.PERMISSION_OMNIPOTENCE):
        return errorScreenInSession('No admin rights')

    # Get projects, show as list:
    newurl = url_for('webRest.urlGetProjects', _external=True)
    token = request.cookies.get(NAME_COOKIE_TOKEN)
    headers = {"Authorization": "fptoken " + token}
    params = {"all":1}
    resp = requests.get(newurl, timeout=5, headers=headers, params=params)
    #print 'status {}'.format(resp.status_code)
    try:
        jresp = resp.json()
    except Exception as e:
        return badJuju('exception getting json response: {}'.format(e))


#        try:
#             payload = {'projectName':frm['projectName'], 'contactName':frm['contactName'],
#                        'contactEmail':frm['contactEmail'], 'ownDatabase':frm['ownDatabase'], 'adminLogin':frm['adminLogin']}
#             newurl = url_for('webRest.urlCreateProject', _external=True)
#             print 'newurl:' + newurl
#             f = request.cookies.get(NAME_COOKIE_SESSION)
#             cooky = {NAME_COOKIE_SESSION:f}
#             resp = requests.post(newurl, cookies=cooky, data=payload, timeout=5)
#             respContent = resp.content
#             jresp = resp.json()
#         except Exception, e:
#             return errorScreenInSession('A problem occurred in project creation: ' + str(e))

    # Create project form:
    projEls = formElements4ProjectManagement()
    out = fpUtil.bsRow(fpUtil.bsCol(forms.makeModalForm('Create Project', projEls, divId='createProjForm',
              submitUrl=url_for('webRest.urlCreateProject', _external=True))))

    # Create user form:
    userEls = formElements4UserManagement()
    out += fpUtil.bsSingleColumnRow(forms.makeModalForm('Create User', userEls, divId='createUserForm',
               #action=url_for('urlFPAdminCreateUser'),
               submitUrl=url_for('webRest.urlCreateUser', _external=True)
               ), topMargin='20px')

    return dp.dataPage(title='Administration', content=out, trialId=-1)

#######################################################################################################
### END FPADMIN STUFF: ################################################################################
#######################################################################################################

@app.route(PREURL+'/projects/<int:projId>/projectTraits/', methods=['GET', 'POST'])
@session_check()
def urlProjectTraits(sess, projId):
#---------------------------------------------------------------------------
#
#
    if request.method == 'GET':
        # System Traits:
        sysTraits = sess.getProject().getTraits()
        sysTraitListHtml = "No project traits yet" if len(sysTraits) < 1 else fpTrait.traitListHtmlTable(sysTraits)
        r = fpUtil.htmlFieldset(
#            fpUtil.bsSingleColumnRow(fpUtil.htmlForm(sysTraitListHtml)) +
            fpUtil.htmlForm(sysTraitListHtml) +
            fpUtil.bsSingleColumnRow(
                       fpUtil.htmlButtonLink("Create New Project Trait", fpUrl("urlNewTrait", sess, trialId=0)),
                       '20px'),
            "Project Traits")
        return dp.dataPage(title='Project Traits', content=r, trialId=-1)


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
#     oStats += '<h3>Boxplot:</h3>'
#     oStats += stats.htmlBoxplot(data)

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


def tiAttributeHtml(sess, ti):
# Returns HTML segment for creating/deleting attribute version of the passed traitInstance.
# We have two states (att present or not) and toggle to different divs for these.
# Have buttons in each, either to create or delete. Create brings up bootstrap modal to
# collect name.
#
    att = ti.getAttribute()
    out = '''
        <script>
        function fpCreateTiAttributeSuccess(name, data, textStatus, jqXHR) {
            fplib.ajax.jsonSuccess(data, textStatus, jqXHR);
            var x = document.getElementById("fpTiAttName");
            x.textContent = name;
            fpToggleTiAttribute(false);
        };
        function fpCreateTiAttribute(name) {
            $.ajax({
                url:"%s",
                type:"POST",
                data:JSON.stringify({"name":name}),
                dataType:"json",
                contentType: "application/json",
                error : fplib.ajax.jsonError,
                success: function(data, textStatus, jqXHR) {fpCreateTiAttributeSuccess(name, data, textStatus, jqXHR)}
            });
        };
        </script>''' % url_for('webRest.urlCreateTiAttribute', projId=sess.getProjectId(), tiId=ti.getId())
    out += '''
        <script>
        function fpToggleTiAttribute(showCreate) {
            var createDiv = document.getElementById("divCreateTiAttribute");
            var deleteDiv = document.getElementById("divDeleteTiAttribute");
            if (showCreate) {
                createDiv.style.display = "inline";
                deleteDiv.style.display = "none";
            } else {
                createDiv.style.display = "none";
                deleteDiv.style.display = "inline";
            }
        }
        function fpDeleteTiAttributeSuccess(data, textStatus, jqXHR) {
            fplib.ajax.jsonSuccess(data, textStatus, jqXHR);
            fpToggleTiAttribute(true);
        };
        function fpDeleteTiAttribute(name) {
            $.ajax({
                url : "%s",
                type : "DELETE",
                dataType : "json",
                error : fplib.ajax.jsonError,
                success: fpDeleteTiAttributeSuccess
            });
        };
        </script>''' % url_for('webRest.urlDeleteTiAttribute', projId=sess.getProjectId(), tiId=ti.getId())

    # Create att div:
    out += '''
        <div id="divCreateTiAttribute" style="display:{0};">
            <button type="button" class="btn btn-primary btn-lg" data-toggle="modal" data-target="#createAttModal">
              Create Attribute
            </button>
            <!-- Modal -->
            <div class="modal fade" id="createAttModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
              <div class="modal-dialog" role="document">
                <div class="modal-content">
                  <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                    <h4 class="modal-title" id="myModalLabel">Create Attribute</h4>
                  </div>
                  <div class="modal-body">
                    <label for="attname">New attribute name</label>
                    <input type="text" size="30" name="attname" id="attname" />
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary" data-dismiss="modal"
                       onclick="fpCreateTiAttribute(document.getElementById('attname').value)">Save changes</button>
                  </div>
                </div>
              </div>
            </div>
        </div>
        '''.format('inline' if (att is None) else 'none')

    # Delete att div:
    out += '''
        <div id="divDeleteTiAttribute" style="display:{0}">
            Attribute name : <span id=fpTiAttName>{1}</span>&nbsp;
            <button type="button" class="btn btn-primary" onclick="fpDeleteTiAttribute()">Delete Attribute</button>
        </div>'''.format('none' if att is None else 'inline', 'null' if att is None else att.fname())

    return out


@app.route(PREURL+'/projects/<int:projId>/trials/<int:trialId>/scoreSet/<int:traitInstanceId>/', methods=['GET'])
@session_check(trialIdParamName='trialId')
def urlScoreSetTraitInstance(sess, projId, trialId, traitInstanceId):
#-------------------------------------------------------------------------------
# Try client graphics.
# Include table data as JSON
# Display the data for specified trait instance.
# NB deleted data are shown (crossed out), not just the latest for each node.
# MFK this should probably display RepSets, not individual TIs
#
    trl = g.sessTrial
    ti = trl.getTraitInstance(traitInstanceId)
    if ti is None:
        return errorScreenInSession('Trait instance not found')
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
                                                 url_for('urlPhotoScoreSetArchive', projId=projId, traitInstanceId=traitInstanceId))
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
                value = '<a href=' + url_for('urlPhoto', projId=projId, filename=fname, trialId=ti.getTrialId()) + '>view photo</a>'
        else:
            value = d.getValue()
        rows.append([d.node.id, d.node.row, d.node.col,
                     value if not overWritten else ('<del>' + str(value) + '</del>'),
                     d.userid, d.getTimeAsString(), d.gps_lat, d.gps_long])

    # Make list of urls for trial attributes:  MFK we should put urls for traitInstances as well
    nodeAtts = []
    for nat in trl.getAttributes():
        nodeAtts.append(
            {"name":nat.name,
             "url":url_for('webRest.urlAttributeData', projId=sess.getProjectId(),
                           attId=nat.id, trialId=trl.getId()),
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

    # Attribute creation/deletion:
    if typ in [T_INTEGER, T_DECIMAL, T_STRING, T_CATEGORICAL, T_DATE]:
        out += fpUtil.htmlFieldset(tiAttributeHtml(sess, ti), 'Attribute')

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
    return dp.dataPage(content=out, title='Score Set Data', trialId=ti.trial_id)


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
                #archiveName = 'r' + str(node.row) + '_c' + str(node.col) + '.jpg'
                #myzip.write(app.config['PHOTO_UPLOAD_FOLDER'] + fname, archiveName)
                # TE: Use default filename (remove achiveName)
                # TODO: Better file naming CSFA-191
                myzip.write(app.config['PHOTO_UPLOAD_FOLDER'] + fname, fname)
    except Exception, e:
        return 'A problem occurred:\n{0}\n{1}'.format(type(e), e.args)
    return None

def photoArchiveZipFileName(sess, traitInstanceId):
#-----------------------------------------------------------
# Generate file name for zip of photos in traitInstance.
    ti = dal.getTraitInstance(sess.db(), traitInstanceId)
    return app.config['PHOTO_UPLOAD_FOLDER'] + '{0}_{1}_{2}.zip'.format(sess.getProjectName(), ti.trial.name, traitInstanceId)

@app.route(PREURL+'/projects/<int:projId>/photo/scoreSetArchive/<traitInstanceId>', methods=['GET'])
@session_check()
def urlPhotoScoreSetArchive(sess, projId, traitInstanceId):
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


@app.route(PREURL+'/projects/<int:projId>/trial/<int:trialId>/photo/<filename>', methods=['GET'])
@session_check()
def urlPhoto(sess, projId, trialId, filename):
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


@app.route(PREURL+'/home', methods=['GET'])
@session_check()
def urlUserHome(sess):
    return frontPage()

@app.route(PREURL+'/projects/<int:projId>/', methods=['GET'])
@session_check()
def urlProject(sess, projId):
#-----------------------------------------------------------------------
# URL handler for user choice from project list.
#
# Need to check userName is of session user, and that they have access to the project,
# and find what permissions they have. We can't just use the username and project from
# the URL since they could just be typed in, BY A BAD PERSON. Session should be a LDAP login.
#
    projectName = sess.getProjectName()
    if projectName is not None:
        projList, errMsg = fpsys.getUserProjects(sess.getUserIdent())
        if errMsg is not None:
            return badJuju(errMsg)
        elif not projList:
            return badJuju('Unexpected project')
        else:
            for prj in projList:
                if prj.projectName() == projectName:
                    # All checks passed, set the project as specified:
                    sess.setProject(prj)
                    # Use Flask session so store project ID.
                    # Should not be needed when all endpoints contain
                    # 'projId' in URL, remove when this is completed.
                    session['projId'] = prj.projectId() # should not be needed when all endpoints contain projId
                    return frontPage()
            # No access to this project - bad user!
            return badJuju('no access to project')

@app.route(PREURL+'/logout', methods=["GET"])
def urlLogout():
    session.clear()
    ret = redirect(url_for('urlMain'))
    ret.set_cookie(NAME_COOKIE_TOKEN, 'loggedOut')
    return ret

def errorScreenInSession(msg, logit=True):
#-----------------------------------------------------------------------
# Show the message in red, with a warning that an error has occurred.
# User remains logged in and error is show with usual page header/footer.
# Intended as a return for a HTTP request after something bad, but not
# suspicious or catastrophic, has occurred.
#
    if logit:
        try:
            util.flog('Glitch: ({}) {}'.format(getUserProjectInfo(), msg))
        except Exception:
            pass
    out = '<font color="red">Something bad has happened: {}<font>'.format(msg)
    return dp.dataPage(content=out, title='Error', trialId=-1)


def badJuju(msg):
#-----------------------------------------------------------------------
# Close the session and return the message. Intended as a return for a HTTP request
# after something bad (and possibly suspicious) has happened.
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

#
# Endpoints for some static pages that don't require login.
#
@app.route(PREURL+'/info/news', methods=["GET"])
def urlInfoPageNews():
    pagename = 'news'
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)
@app.route(PREURL+'/info/about', methods=["GET"])
def urlInfoPageAbout():
    pagename = 'about'
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)
@app.route(PREURL+'/info/contact', methods=["GET"])
def urlInfoPageContact():
    pagename = 'contact'
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)
@app.route(PREURL+'/info/fieldprime', methods=["GET"])
def urlInfoPageFieldPrime():
    pagename = 'fieldprime'
    return render_template(pagename + '.html', title='FieldPrime {0}'.format(pagename), pagename=pagename)

def asyncGetToken(username, password):
# Could just call fpRestApi.generate_auth_token - if we have verified password.    
    try:
        newurl = url_for('webRest.urlGetToken', _external=True)
        jresp = requests.get(newurl, timeout=5, auth=(username, password)).json()
    except Exception, e:
        app.logger.error('getToken error: ' + str(e))
        return None
    return fprData(jresp)["token"]

@app.route(PREURL+'/', methods=["GET", "POST"])
def urlMain():
#-----------------------------------------------------------------------
# Entry point for FieldPrime web admin.
# As a GET it presents a login screen.
# As a POST it process the login data.
#
# THIS COMMENT IS OUT OF DATE, NOT REFLECTING CURRENT CODE STATE:
# In particular, I've removed the server state, so now the server is stateless.
# Session state is carried in cookies, one of which is obtained from the REST API.
# The other is (I think) used by the Flask session object, which I use to store
# the current project ID. Ultimately these should be in the URLs.
#
# Note the use of sessions. On login, a server side session is established (state is stored
# in the file system), and the id of this session is sent back to the browser in a cookie,
# which should be sent back with each subsequent request.
#
# Every access via the various app.routes above, should go through decorator session_check
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
    mkdbg("urlMain")
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
            # Check login details:
            authOK = fpsys.userPasswordCheck(username, password)
            app.logger.debug("authOK %s" % authOK)
            if authOK:
                # OK, valid user. Find projects they have access to:
                projList, errMsg = fpsys.getUserProjects(username)
                if errMsg is not None:
                    app.logger.debug("Error in getUserProjects: %s" % errMsg)
                    error = errMsg
                else:
                    # Good to go, show the user front page, after adding cookie:
                    app.logger.debug('Login from user {0}'.format(username))
                    fpsys.fpSetupG(g, userIdent=username)
                    resp = make_response(frontPage())

                    # Create an authentication token for the user:
                    # How can we refresh token timeout the way we do for sessions?
                    # Perhaps have to have it as a cookie and send back modified version each time.
                    token = asyncGetToken(username, password)
                    if token is not None:
                        resp.set_cookie(NAME_COOKIE_TOKEN, token)
                        app.logger.debug('Setting cookie token {0}'.format(token))
                    else:
                        app.logger.debug('Login failed to create token for user {0}'.format(username))
                        error = 'Login failed'

                    return resp
            elif authOK is None:
                app.logger.debug("Login failed for user {0}".format(username))
                util.flog('Login failed attempt for user {0}'.format(username))
                error = 'Login failed'
            else:
                app.logger.debug("Login failed for user {0}".format(username))
                util.flog('Login failed attempt for user {0}'.format(username))
                error = 'Invalid Password'

        # Error return
        return loginPage(error)

    # Request method is 'GET' - return login page:
    return urlInfoPageFieldPrime()


##############################################################################################################

# For local testing:
if __name__ == '__main__':
    from os.path import expanduser
    FPROOT = expanduser("~") + '/proj/fpserver/'
    app.config['SESS_FILE_DIR'] = FPROOT + '/wsessions'
    app.config['PHOTO_UPLOAD_FOLDER'] = FPROOT + '/photos/'
    app.config['FPLOG_FILE'] = FPROOT + '/fplog/fp.log'
    app.config['CATEGORY_IMAGE_FOLDER'] = FPROOT + '/catPhotos'
    app.config['CATEGORY_IMAGE_URL_BASE'] = 'file://' + FPROOT + '/catPhotos'
    app.config['FPPWFILE'] = FPROOT + '/fppw'
    app.config['FP_DB_CREATE_FILE'] = FPROOT + 'fprime.create.tables.sql'
    LOGIN_TIMEOUT = 36000

    # Setup logging:
    app.config['FP_FLAG_DIR'] = FPROOT + '/fplog/'
    util.initLogging(app, True)  # Specify print log messages

    app.run(debug=True, threaded=True, host='0.0.0.0', port=5001)

