# fpAppWapi.py
# Michael Kirk 2013-2016
#
# This version a copy of fp_app_api/fpApi.py.
# This is now a blueprint part of the web admin app,
# it used to be a separate wsgi entry point.
#

from flask import Blueprint, current_app, Flask, request, Response, url_for
import simplejson as json

import os, traceback
from functools import wraps
from werkzeug import secure_filename

import fp_common.models as dal
import fp_common.util as util
from fp_common.const import *

from flask import current_app as app
from config import API_PREFIX

### SetUp: ######################################################################################

appApi = Blueprint('appApi', __name__)

##################################################################################################

def serverErrorResponse(msg):
    util.flog(msg)
    response = Response(msg)
    response.status = '500 {0}'.format(msg)
    return response

def successResponse():
#-------------------------------------------------------------------------------------------------
# Response to return for successful data upload. Currently this is just the string 'success'.
# I would like it to be JSON, but we have to first introduce support for this into the clients,
# and wait until there are no older clients still in use.
# Note this is for JSON uploads that do not expect content back, other than success indicator
# or error code. Perhaps we could just rely on the returned status code and message?
#
# A better solution would be to retrieve the client version number from the request, store
# it in a global var if possible so available everywhere without passing, and switch behaviour
# on that.
    return Response('success')

def dec_get_trial(jsonReturn):
#-------------------------------------------------------------------------------------------------
# Decorator, for appApi.route functions with username and trialid parameters.
# It is assumed there is a "request" variable in context. and this contains a password URL parameter "pw".
# "pw" - Scoring Devices password configured on the client.
# "ver" - client software version.
# "andid" - android id of the client device.
# The password is checked, and the trial object retrieved and passed to the decoratee instead
# of the trialid. The open db connection is also added as a third parameter.
# On error, if jsonReturn then a json error message is returned, else a plain text one.
#
    def param_dec(func):
        @wraps(func)
        def inner(username, trialid, *args, **kwargs):
            # Log request:
            util.fpLog(current_app, "client ver:{0} user:{1} andid:{2}".format(
                request.args.get('ver', '0'), username, request.args.get('andid', '')))

            password = request.args.get('pw', '')
            dbc, errMsg = dal.dbConnectAndAuthenticate(username, password)
            if dbc is None:
                if jsonReturn:
                    return JsonErrorResponse(errMsg)
                else:
                    return serverErrorResponse("error:" + errMsg)

            trl = dal.getTrial(dbc, trialid)
            if trl is None:
                errStr = "trial not found"
                if jsonReturn:
                    return JsonErrorResponse(errStr)
                else:
                    return Response("error:" + errStr)
            return func(username, trl, dbc, *args, **kwargs)
        return inner
    return param_dec

@appApi.route(API_PREFIX + '/user/<username>/', methods=['GET'])
def urlAppCoolTrialList(username):
#-------------------------------------------------------------------------------------------------
# Return JSON list of available trials for user.
# They are returned as a JSON object containing a named
# array of trial:url pairs:
#    { 'trials': [ <trialName>:<URLtoGetTheTrial>, ... ] }
#
# The URL to access this func is(should be) the only URL that has to be provided by the
# client, either by being hard coded or entered by the user. It should be a "cool" URL,
# i.e. it should never change.  All other URLs used by the client should be
# provided by the server, for example in the response to this URL we provide
# the URLs for further interactions with the server.
#
# curl http://0.0.0.0:5001/user/mk/
#
    password = request.args.get('pw', '')
    dbc, errMsg = dal.dbConnectAndAuthenticate(username, password)
    if dbc is None:
        return JsonErrorResponse(errMsg)

    # Get the trial list as json:
    # trials = dal.getTrialList(dbc)
    app.logger.debug("getTrialListByProject")
    trials = dal.getTrialListByProject(dbc,username)

    trialList = []
    for t in trials:
        url = url_for('appApi.urlAppGetTrial', username=username, trialid=t.id, _external=True)
        tdic = {'name':t.name, 'url':url}
        trialList.append(tdic)

#     app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    dic = {'trials':trialList}
    return Response(json.dumps(dic), mimetype='application/json')

@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/device/<token>/', methods=['GET'])   # For trial update
@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/', methods=['GET'])                  # For new trial download
@dec_get_trial(True)
def urlAppGetTrial(username, trial, dbc, token=None):
#-------------------------------------------------------------------------------------------------
# Return trial design in JSON format.
#
# Note we can come to this with either of the 2 urls above. If there is a token present
# then this is an update, and we don't create a new token (which cause trouble when
# existing scores sets are re-exported). Currently when the client is getting a new trial,
# it uses the URL returned to it from the urlAppCoolTrialList function. When updating the trial, it uses
# the "uploadURL" provided to it with the trial. This is a little confusing perhaps. It works,
# however because this function and the urlAppUploadTraitData function have the same URL, but the
# upload is POST only, and this one is GET only. A better solution perhaps would be to provide
# an updateURL with the trial. Would have to add support on the client to use this.
#
# curl http://0.0.0.0:5001/user/mk/trial/1/?ver=500
#
    androidId = request.args.get('andid', '')
    clientVersion = request.args.get('ver', '0')
    if int(clientVersion) < 450:
        return JsonErrorResponse('This client version ({0}) is too old. Please upgrade, or contact support for help'.format(clientVersion))

    # Create new token if this is a new trial download:
    if token is None:
        token = dal.Token.createNewToken(dbc, androidId, trial.id).tokenString()
    else:
        # The token should be in the database, let's check:
        try:
            dal.Token.getTokenId(dbc, token)
        except:
            util.alertFieldPrimeAdmin(current_app, 'token ({0}) not found in database'.format(token))

    # Trial json object members:
    jtrl = {'name':trial.name, 'site':trial.site, 'year':trial.year, 'acronym':trial.acronym}
    jtrl['serverToken'] = token # MFK This could and should be removed, once client doesn't need it anymore.
                                # Currently used in upload of notes, but now we embed it in the uploadURL,
                                # and the notes upload should switch to using that.

    jtrl['adhocURL'] = url_for('appApi.urlAppCreateAdhocTrait', username=username, trialid=trial.id, _external=True)
    jtrl['uploadURL'] = url_for('appApi.urlAppUploadTrialData', username=username, trialid=trial.id, token=token, _external=True)
    # Add trial attributes from database:
    jprops = {}
    for tp in trial.trialProperties:
        jprops[tp.name] = tp.value
    jtrl[JTRL_TRIAL_PROPERTIES] = jprops

    # Node Attribute descriptors:
    attDefs = []
    attributes = trial.getAttributes()
    # NB node order must match that of trial.getNodes()
    # TE: Modified to get order to match row/col order getNodesSortedRowCol()
    attValueLists = [att.getValues(orderByNodeId=False, missingValue=None) for att in attributes]
    for att in attributes:
        ad = {}
        ad['id'] = att.id
        ad['name'] = att.name
        ad['datatype'] = att.datatype
        ad['func'] = att.func
        attDefs.append(ad)
    jtrl['nodeAttributes'] = attDefs

    # Nodes:
    nodeList = []
    nodePropertyNames = ["id", "row", "col", "description", "barcode"]
    for nodeIndex, nd in enumerate(trial.getNodesSortedRowCol()):
        jnode = {}
        ### Node built in properties:
        for n in nodePropertyNames:
            jnode[n] = getattr(nd, n)
            
        ### Attribute values:        
        atts = {}
        for attIndex, att in enumerate(attributes):
            val = attValueLists[attIndex][nodeIndex]
            if val is not None:
                atts[attributes[attIndex].fname()] = val
        if len(atts) > 0:
            jnode['attvals'] = atts
            
        ### GPS location:
        if nd.latitude is not None and nd.longitude is not None:
            jloc = [nd.latitude, nd.longitude]
            jnode['location'] = jloc
        nodeList.append(jnode)
    jtrl['nodes'] = nodeList

    # Traits:
    traitList = []
    for trt in trial.traits:
        jtrait = {}
        # Fields common to all traits:
        jtrait['id'] = trt.id
        jtrait['caption'] = trt.caption
        jtrait['description'] = trt.description
        jtrait['type'] = trt.datatype     # MFK 'datatype' would be better
        # Hack forcing all traits on client to local (else problem with common upload url)
        # Now deprecated 25/3/15 remove when no more too old clients
        jtrait['sysType'] = 0

        # Add the uploadURL:
        jtrait['uploadURL'] = url_for('appApi.urlAppUploadTraitData', username=username, trialid=trial.id, traitid=trt.id,
                                      token=token, _external=True)

        #
        # Barcode - NB we rely on the fact that there are (now) no sys traits on the client.
        #
        trlTrt = dal.getTrialTrait(dbc, trial.id, trt.id)
        if trlTrt is not None:
            barcode = trlTrt.barcodeAtt_id
            if (barcode is not None):
                jtrait['barcodeAttId'] = barcode

        #########################################################################
        # Here we should have trait datatype specific stuff. Using polymorphism?
        #

        # Categorical traits:
        if trt.datatype == T_CATEGORICAL:
            cats = []
            for cat in trt.categories:
                oneCat = {}
                for fieldName in ['caption', 'value', 'imageURL']:
                    oneCat[fieldName] = getattr(cat, fieldName)
                cats.append(oneCat)
            jtrait['categories'] = cats

        # Photo traits:
        elif trt.datatype == T_PHOTO:
            jtrait['photoUploadURL'] = url_for('appApi.urlAppUploadPhoto', username=username, trialid=trial.id,
                                               traitid=trt.id, token=token, _external=True)

        # Numeric traits (integer and decimal):
        # Historical comment: Note hacked special case for 'min' and 'max'. These currently sql decimal types,
        # and they cause failure when converting to json for some reason, unless cast to float.
        elif trt.datatype == T_DECIMAL or trt.datatype == T_INTEGER:
            # get the trialTraitNumeric object, and send the contents
            ttn = dal.GetTrialTraitNumericDetails(dbc, trt.id, trial.id)
            if ttn is not None:
                val = {}
                # min:
                tmin = ttn.getMin()
                if tmin is not None:
                    val['min'] = tmin
                # max:
                tmax = ttn.getMax()
                if tmax is not None:
                    val['max'] = tmax
                # Condition:
                if (ttn.cond):
                    val['cond'] = ttn.cond

                if len(val) > 0:  # Don't send record if empty
                    jtrait['validation'] = val

        # Text (string) traits:
        elif trt.datatype == T_STRING:
            tts = dal.getTraitString(dbc, trt.id, trial.id)
            if tts is not None:
                val = {}
                val['pattern'] = tts.pattern
                jtrait['validation'] = val

        #########################################################################

        traitList.append(jtrait)
    jtrl['traits'] = traitList

    return Response(json.dumps(jtrl), mimetype='application/json')


@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/trait/<traitid>/device/<token>/', methods=['POST'])
@dec_get_trial(False)
def urlAppUploadTraitData(username, trial, dbc, traitid, token):
#-------------------------------------------------------------------------------------------------
# Process upload of json trait instance data.
# Trait instances are uniquely identified by trial/trait/token/seqNum/sampleNum.
#
    password = request.args.get('pw', '')
    jti = request.json
    if not jti:
        return Response('Bad or missing JSON')

    # Return None on success, else error string.
    # Separate func as used in two places (but one of these places now obsolete, as we now upload individual tis)
    # Get json fields:
    try:
        dayCreated = jti["dayCreated"]
        seqNum = jti["seqNum"]
        sampleNum = jti["sampleNum"]
    except Exception, e:
        return Response('Missing required traitInstance field: ' + e.args[0] + trial.name)
    try:
        aData = jti["data"]
    except Exception, e:
        aData = None

    # Log upload, but don't output json.dumps(jti), as it can be big:
    util.flog("urlAppUploadTraitData from {0}: dc:{1}, seq:{2}, samp:{3}".format(
                        token, dayCreated, seqNum, sampleNum, "None" if aData is None else len(aData)))

    # MFK: A problem here in that ideally we don't want to create empty scoresets.
    # The photo upload code, relies on being able to create an empty scoreset on the
    # server prior to uploading the pictures. Actually, that's now not the case, but
    # there may be versions of the app out there for a while that do require an empty
    # set to be created. So for the moment, we'll limit this to photo traits only,
    # and then remove that when we're confident all apps are updated:
    if (aData is None or len(aData) <= 0) and dal.getTrait(dbc, traitid).datatype != T_PHOTO:
        return successResponse()
    # Get/Create trait instance:
    dbTi = dal.getOrCreateTraitInstance(dbc, traitid, trial.id, seqNum, sampleNum, dayCreated, token)
    if dbTi is None:
        return Response('Unexpected error retrieving or creating trait instance')

    # Add the data, if there is any:
    if aData is None or len(aData) <= 0:
        errMsg = None
    else:
# MFK Replace with
#        dbTi.addData(aData)
# After testing thoroughly
        errMsg = dal.AddTraitInstanceData(dbc, dbTi.id, dbTi.trait.datatype, aData)

    return (successResponse() if errMsg is None else Response(errMsg))


def allowed_file(filename):
#--------------------------------------------------------------------------
# Return whether filename has allowed extension.
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/trait/<traitid>/device/<token>/photo/', methods=['POST'])
@dec_get_trial(False)
def urlAppUploadPhoto(username, trial, dbc, traitid, token):
#-------------------------------------------------------------------------------------------------
# Handle a photo upload from the app.
# These are uniquely identified by dbusername/trial/trait/token/seqNum/sampleNum.
# These are all provided in the url except for seqNum and sampleNum which come
# (out-of-band) as form parameters. In addition the score metadata is also provided
# in the form parameters. This enables us to create the datum record in this function.
# Note originally we only saved the photo here, and the client would separately upload
# the traitInstance containing all the meta data as for a non-photo traitInstance.
# This was problematic because until both the metadata, and the photo itself are both
# uploaded we have not successfully uploaded. Hence it is better done in a single
# transaction (this func). Currently, the client will first upload a trait instance
# WITHOUT any datums, to ensure the traitInstance is created on the server, and to
# set its creation date. If we didn't do this we would have to upload the creation
# date with every photo (or at least the first one) so as to allow us to create the
# traitInstance record in this function (if it was not already present).
#
# UPDATE - Attow the creation date is sent with each photo, and the client does NOT
# first create an empty ti.
#
# Note the node Id is uploaded in the file name (this should be same as server node id).
# But in addition it is (now) also uploaded as a form parameter, this reduces our
# dependence on it being in the file name (which may change).
# The photos are saved in the PHOTO_UPLOAD_FOLDER folder, with the name encoding
# all the relevant info:
# '{0}_{1}_{2}_{3}_{4}_{5}_{6}.jpg'.format(dbusername, trialId, traitId, nodeId, token, seqNum, sampNum)
#
    seqNum = request.args.get(TI_SEQNUM, '')
    sampNum = request.args.get(TI_SAMPNUM, '')
    timestamp = request.args.get(DM_TIMESTAMP, '')
    userid = request.args.get(DM_USERID, '')
    gpslat = request.args.get(DM_GPS_LAT, '')
    gpslong = request.args.get(DM_GPS_LONG, '')
    nodeId = request.args.get(DM_NODE_ID_CLIENT_VERSION, '')
    dayCreated = request.args.get(TI_DAYCREATED, '')

    file = request.files.get('uploadedfile')
    util.flog('urlAppUploadPhoto:node {0}, seq {1} samp {2} filename {3}'.format(nodeId, seqNum, sampNum, file.filename))
    if file and allowed_file(file.filename):
        sentFilename = secure_filename(file.filename)
        saveName = dal.photoFileName(username, trial.id, traitid, int(nodeId), token, seqNum, sampNum)
        try:
            # Need to check if file exists, if so postfix copy num to name so as not to overwrite:
            fullPath = current_app.config['PHOTO_UPLOAD_FOLDER'] + saveName
            print 'fullPath {}'.format(current_app.config['PHOTO_UPLOAD_FOLDER'] + saveName)
            base = os.path.splitext(fullPath)[0]
            ext = os.path.splitext(fullPath)[1]
            tryAgain = os.path.isfile(fullPath)
            i = 1
            while tryAgain:
                fullPath = '{0}_c{1}{2}'.format(base, i, ext)
                i += 1
                tryAgain = os.path.isfile(fullPath)

            file.save(fullPath)
        except Exception, e:
            util.flog('failed save {0}'.format(current_app.config['PHOTO_UPLOAD_FOLDER'] + saveName))
            util.flog(e.__doc__)
            util.flog(e.message)
            return serverErrorResponse('Failed photo upload : can''t save')

        # Now save datum record:
        # get TI - this should already exist, which is why we can pass in 0 for dayCreated
        # MFK note this outer if below is to support old versions of the app, to allow them to
        # upload their photos in the old way. It should be removed eventually..
        if nodeId is not None and len(nodeId) > 0:
            dbTi = dal.getOrCreateTraitInstance(dbc, traitid, trial.id, seqNum, sampNum, dayCreated, token)
            if dbTi is None:
                return serverErrorResponse('Failed photo upload : no trait instance')
            res = dal.AddTraitInstanceDatum(dbc, dbTi.id, dbTi.trait.datatype, nodeId, timestamp,
                                            userid, gpslat, gpslong, os.path.basename(fullPath))
            if res is None:
                return successResponse()
            else:
                return serverErrorResponse('Failed photo upload : datum create fail')
        else:
            util.flog('urlAppUploadPhoto: no nodeId, presumed old app version')
            return successResponse()
    else:
        return serverErrorResponse('Failed photo upload : bad file')

@appApi.route(API_PREFIX + '/crashReport', methods=['POST'])
def urlAppCoolUploadCrashReport():
#-------------------------------------------------------------------------------------------------
# check file size?
# Handle a crash report upload from the app.
    cfile = request.files.get('uploadedfile')
    util.flog('urlAppCoolUploadCrashReport: filename {0}'.format(cfile.filename))
    if cfile and allowed_file(cfile.filename):
        sentFilename = secure_filename(cfile.filename)
        saveName = sentFilename
        try:
            # Need to check if file exists, if so postfix copy num to name so as not to overwrite:
            fullPath = current_app.config['CRASH_REPORT_UPLOAD_FOLDER'] + saveName
            cfile.save(fullPath)
            return successResponse()
        except Exception, e:
            util.flog('failed save {0}'.format(current_app.config['CRASH_REPORT_UPLOAD_FOLDER'] + saveName))
            util.flog(e.__doc__)
            util.flog(e.message)
            return serverErrorResponse('Failed crash report upload : can''t save')

    else:
        return serverErrorResponse('Failed crash report upload')


@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/device/<token>/', methods=['POST'])
@dec_get_trial(False)
def urlAppUploadTrialData(username, trial, dbc, token):
#-------------------------------------------------------------------------------------------------
# This version should return JSON!
# NB historical peculiarities here, this attow only used for upload nodes, or notes.
# And the format of the response differs between these two. Probably would be better
# with separate urls.
#
# Note used to have old_version, where the token was in the json not the url, see svn history
# for this code if necessary. Only relevant if old clients are still out there, but I think
# not. URLs sent and stored on client when this function was
# used should still be able to access this func (since the URL will match). But now
# we send out the URL for the new version.
    jtrial = request.json
    if not jtrial:
        return Response('Bad or missing JSON')
    util.flog("upload_trial:\n" + json.dumps(jtrial))

    # Probably need a 'command' or 'type' field.
    # different types will need different responses.
    # Note old client would not have it, so perhaps below must stay

    # Old clients may just send 'notes', we process that here in the manner they expect:
    # MFK - so what do new clients do different? Nothing attow.
    if 'notes' in jtrial:   # We really should put these JSON names in a set of string constants somehow..
        err = trial.addNodeNotes(token, jtrial[jTrialUpload['notes']])
        if err is not None:
            util.flog('addNodeNotes fail:{0}'.format(err))
            return Response(err)

        # All done, return success indicator:
        return successResponse()

    #
    # Created Nodes:
    # Process nodes created on the client. We need to create them on the server,
    # and send back the ids of the new server versions. This needs to be idempotent,
    # i.e. if a client sends a node more than once, it should only be created once
    # on the server. This is managed by recording the token and the client node id
    # for each created node (in the database).
    #
    if JTRL_NODES_ARRAY in jtrial:
        # MFK - make this an array of objects, preferably same format as sent server to client.
        clientLocalIds = jtrial[JTRL_NODES_ARRAY]
        serverIds = []
        serverRows = []
        serverCols = []
        # We have to return array of server ids to replace the passed in local ids.
        # We need to record the local ids so as to be idempotent.
        tokenObj = dal.Token.getToken(dbc, token, trial.id)
        if tokenObj is None:
            util.flog('urlAppUploadTrialData: invalid token')
            return Response('invalid token')
        for newid in clientLocalIds:
            #print 'new id: {0}'.format(newid)
            # Create node, or get it if it already exists:
            node = dal.TokenNode.getOrCreateClientNode(dbc, tokenObj.id, newid, trial.id)
            serverIds.append(node.getId())
            serverRows.append(node.getRow())
            serverCols.append(node.getCol())
        returnObj = {'nodeIds':serverIds, 'nodeRows':serverRows, 'nodeCols':serverCols}
        return Response(json.dumps(returnObj), mimetype='application/json')  # prob need ob

    # All done, return success indicator:
    return successResponse()

@appApi.route(API_PREFIX + '/user/<username>/trial/<trialid>/createAdHocTrait/', methods=['GET'])
@dec_get_trial(True)
def urlAppCreateAdhocTrait(username, trl, dbc):
#-------------------------------------------------------------------------------------------------
# Create an adhoc trait, and return the id of the trait in JSON
# This should be a url.
#
    # Bundle all this into urlAppGetTrial(username, password), may not need dbs if all can be done from trial object
    # password = request.args.get('pw', '')
    # androidId = request.args.get('andid', '')

    caption = request.args.get('caption', '')
    description = request.args.get('description', '')
    vtype = request.args.get('datatype', '')
    #vmin = request.args.get('min', '')
    #vmax = request.args.get('max', '')
    vmin = -1000000
    vmax = 1000000
    # MFK Need to get rid of min and max, from general trait, it needs to be trait specific
    ntrt, errMsg = dal.CreateTrait2(dbc, caption, description, vtype, dal.SYSTYPE_ADHOC, vmin, vmax)
    if not ntrt:
        return JsonErrorResponse(errMsg)

    # Insert into trialTrait ?

    # Return the trait id in JSON:
#MFK need to send back upload url not id
    return Response(json.dumps({'traitId':ntrt.id}), mimetype='application/json')


def JsonErrorResponse(errMsg):
#-------------------------------------------------------------------------------------------------
# Returns Response with error message in JSON ('error' key)
#
    return Response(json.dumps({'error':errMsg}), mimetype='application/json')


#############################################################################################
