# fpApi.py
# Michael Kirk 2013
#
#

from flask import Flask, request, Response, url_for
import simplejson as json

import os, sys, time
from datetime import datetime
from functools import wraps
from werkzeug import secure_filename
from jinja2 import Environment, FileSystemLoader

# If we are running locally for testing, we need this magic for some imports to work:
if __name__ == '__main__':
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir)

from fp_common.const import *
import fp_common.util as util


### SetUp: ######################################################################################
if __name__ == '__main__':
    import os, sys, inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir)

app = Flask(__name__)
try:
    app.config.from_object('fp_app_api.fpAppConfig')
except ImportError:
    pass

# If env var FPAPI_SETTINGS is set then load configuration from the file it specifies:
app.config.from_envvar('FPAPI_SETTINGS', silent=True)

# Load the Data Access Layer Module (must be named in the config)
import importlib
dal = importlib.import_module(app.config['DATA_ACCESS_MODULE'])

gdbg = False  # Switch for logging to file


##################################################################################################


def dec_get_trial(jsonReturn):
#-------------------------------------------------------------------------------------------------
# Decorator, for functions with username and trialid parameters.
# It is assumed there is a request var in context. and this contains a password URL parameter "pw".
# The password is checked, and the trial object retrieved and passed to the decoratee instead
# of the trialid. The open db connection is also added as a third parameter.
# On error, if jsonReturn then a json error message is returned, else a plain text one.
#
    def param_dec(func):
        @wraps(func)
        def inner(username, trialid, *args, **kwargs):
            # Log request:
            util.fpLog(app, "client ver:{0} user:{1} andid:{2}".format(
                request.args.get('ver', '0'), username, request.args.get('andid', '')))

            password = request.args.get('pw', '')
            dbc, errMsg = dal.DbConnectAndAuthenticate(username, password)
            if dbc is None:
                if jsonReturn:
                    return JsonErrorResponse(errMsg)
                else:
                    return Response("error:" + errMsg)

            trl = dal.GetTrial(dbc, trialid)
            if trl is None:
                errStr = "trial not found"
                if jsonReturn:
                    return JsonErrorResponse(errStr)
                else:
                    return Response("error:" + errStr)
            return func(username, trl, dbc, *args, **kwargs)
        return inner
    return param_dec



@app.route('/user/<username>/', methods=['GET'])
def trial_list(username):
#-------------------------------------------------------------------------------------------------
# Return JSON list of available trials for user
#
    password = request.args.get('pw', '')
    dbc, errMsg = dal.DbConnectAndAuthenticate(username, password)
    if dbc is None:
        return JsonErrorResponse(errMsg)

    # Get the trial list as json:
    trials = dal.GetTrialList(dbc)

    trialList = []
    for t in trials:
        url = url_for('get_trial', username=username, trialid=t.id, _external=True)
        tdic = {'name':t.name, 'url':url}
        trialList.append(tdic)

    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    dic = {'trials':trialList}
    return Response(json.dumps(dic), mimetype='application/json')


@app.route('/user/<username>/trial/<trialid>/', methods=['GET'])
@dec_get_trial(True)
def get_trial(username, trl, dbc):
#-------------------------------------------------------------------------------------------------
# Return trial design in JSON format.
#
    LogDebug('get_trial', 'start')
    androidId = request.args.get('andid', '')
    clientVersion = request.args.get('ver', '0')

    # Trial json object members:
    jtrl = {'name':trl.name, 'site':trl.site, 'year':trl.year, 'acronym':trl.acronym}
    jtrl['adhocURL'] = url_for('create_adhoc', username=username, trialid=trl.id, _external=True)
    jtrl['uploadURL'] = url_for('upload_trial', username=username, trialid=trl.id, _external=True)
    # Add trial attributes from database:
    jtatts = {}
    for tatt in trl.trialAtts:
        jtatts[tatt.name] = tatt.value
    jtrl[JTRL_TRIAL_ATTRIBUTES] = jtatts

    # Server Token:
    # Use the android device ID postfixed with the current time in seconds as the serverTrialId.
    # This should ensure different tokens for the same trial being downloaded multiple times on
    # a single device (with delete in between), as long as they are not created within the same
    # second (and this is not an expected use case):
    # MFK And why do we need such tokens? They are currently used in the traitInstance and nodeNote table.
    epoch = int(time.time())
    servToken = androidId + "." + str(int(time.time()))
    jtrl['serverToken'] = servToken

    # Node Attribute descriptors:
    LogDebug('get_trial', 'pre attributes')
    attDefs = []
    for att in trl.tuAttributes:
        tua = {}
        tua['id'] = att.id
        tua['name'] = att.name
        tua['datatype'] = att.datatype
        tua['func'] = att.func
        if int(clientVersion) > 0:
            attDefs.append(tua)
        else:     # MFK - support for old clients, remove when all clients updated
            attDefs.append(att.name)
    jtrl['attributes'] = attDefs
    ### MFK
    ### Note duplication here, we want to change 'attributes' to 'nodeAttributes', but need to continue
    ### support for old clients which will look only for 'attributes'. Can remove the 'attributes' version
    ### when all clients are updated.
    ###
    jtrl['nodeAttributes'] = attDefs

    # Nodes:
    LogDebug('get_trial', 'pre nodes')
    tuList = []
    tuNames = ["id", "row", "col", "description", "barcode"]
    jtrl['numTrialUnit'] = len(trl.nodes)   # MFK check if no trial units this is zero, not null
    for ctu in trl.nodes:
        jtu = {}
        # MFK - there is a problem here, the fixed names and the user provided
        # attribute names are in the same name space. This is a problem if, for example
        # there is a user provided 'id' attribute.
        # Solution is probably to put user attributes inside an 'attVals':object kv pair
        # but this change must be supported on the client.

        # Trial unit attributes:
        for n in tuNames:
            jtu[n] = getattr(ctu, n)

        # Attribute values:
        if len(ctu.attVals) > 0:
            if int(clientVersion) > 0:
                atts = {}
                for att in ctu.attVals:
                    atts[att.nodeAttribute.name] = att.value
                    jtu['attvals'] = atts
            else:     # MFK - support for old clients, remove when all clients updated
                for att in ctu.attVals:
                    jtu[att.nodeAttribute.name] = att.value

        # GPS location:
        if ctu.latitude is not None and ctu.longitude is not None:
            jloc = [ctu.latitude, ctu.longitude]
            jtu['location'] = jloc

        tuList.append(jtu)
    jtrl['trialUnits'] = tuList

    # Traits:
    LogDebug('get_trial', 'pre traits')
    traitList = []
    traitFieldNames = ['id', 'sysType', 'caption', 'description', 'type']
    for trt in trl.traits:
        jtrait = {}
        # Fields common to all traits:
        # Note hacked special case for 'min' and 'max'. These currently sql decimal types,
        # and they cause failure when converting to json for some reason, unless cast to float.
        for fieldName in traitFieldNames:
            val = getattr(trt, fieldName)
            if val is not None:
                if fieldName == 'min' or fieldName == 'max': val = float(val)
                jtrait[fieldName] = val

        jtrait['sysType'] = 0    # Hack forcing all traits on client to local (else problem with common upload url)

        # Add the uploadURL:
        jtrait['uploadURL'] = url_for('upload_trait_data', username=username, trialid=trl.id, traitid=trt.id,
                                      token=servToken, _external=True)

        #
        # Barcode - NB we rely on the fact that there are (now) no sys traits on the client.
        #
        trlTrt = dal.getTrialTrait(dbc, trl.id, trt.id)
        barcode = trlTrt.barcodeAtt_id
        if (barcode is not None):
            jtrait['barcodeAttId'] = barcode

        #########################################################################
        # Here we should have trait datatype specific stuff. Using polymorphism?
        #

        # Categorical traits:
        if trt.type == dal.TRAIT_TYPE_TYPE_IDS['Categorical']:
            cats = []
            for cat in trt.categories:
                oneCat = {}
                for fieldName in ['caption', 'value', 'imageURL']:
                    oneCat[fieldName] = getattr(cat, fieldName)
                cats.append(oneCat)
            jtrait['categories'] = cats

        # Photo traits:
        elif trt.type == dal.TRAIT_TYPE_TYPE_IDS['Photo']:
            jtrait['photoUploadURL'] = url_for('upload_photo', username=username, trialid=trl.id,
                                               traitid=trt.id, token=servToken, _external=True)

        # Numeric traits (integer and decimal):
        elif trt.type == T_DECIMAL or trt.type == T_INTEGER:
            # get the trialTraitInteger object, and send the contents
            ttn = dal.GetTrialTraitNumericDetails(dbc, trt.id, trl.id)
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

        #########################################################################

        traitList.append(jtrait)
    jtrl['traits'] = traitList

    return Response(json.dumps(jtrl), mimetype='application/json')


@app.route('/user/<username>/trial/<trialid>/trait/<traitid>/device/<token>/', methods=['POST'])
@dec_get_trial(False)
def upload_trait_data(username, trial, dbc, traitid, token):
#-------------------------------------------------------------------------------------------------
# Process upload of json trait instance data.
# Trait instances are uniquely identified by trial/trait/token/seqNum/sampleNum.
#
    password = request.args.get('pw', '')
    jti = request.json
    if not jti:
        return Response('Bad or missing JSON')
    util.flog("upload_trait_data:\n" + json.dumps(jti))

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

    # MFK: A problem here in that ideally we don't want to create empty scoresets.
    # The photo upload code, relies on being able to create an empty scoreset on the
    # server prior to uploading the pictures. Actually, that's now not the case, but
    # there may be versions of the app out there for a while that do require an empty
    # set to be created. So for the moment, we'll limit this to photo traits only,
    # and then remove that when we're confident all apps are updated:
    if (aData is None or len(aData) <= 0) and dal.getTrait(dbc, traitid).type != T_PHOTO:
        return Response('success')
    # Get/Create trait instance:
    dbTi = dal.GetOrCreateTraitInstance(dbc, traitid, trial.id, seqNum, sampleNum, dayCreated, token)
    if dbTi is None:
        return Response('Unexpected error retrieving or creating trait instance')

    # Add the data, if there is any:
    if aData is None or len(aData) <= 0:
        errMsg = None
    else:
        errMsg = dal.AddTraitInstanceData(dbc, dbTi.id, dbTi.trait.type, aData)

    return (Response('success') if errMsg is None else Response(errMsg))

#
# upload_photo()
# Trait instances are uniquely identified by trial/trait/token/seqNum/sampleNum.
#
def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/user/<username>/trial/<trialid>/trait/<traitid>/device/<token>/photo/', methods=['POST'])
@dec_get_trial(False)
def upload_photo(username, trial, dbc, traitid, token):
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
    util.flog('upload_photo:node {0}, seq {1} samp {2}'.format(nodeId, seqNum, sampNum))

    file = request.files.get('uploadedfile')
    if file and allowed_file(file.filename):
        sentFilename = secure_filename(file.filename)
        (nodeIdStr, fileExt) = os.path.splitext(sentFilename)  # only need nodeIdStr now as file ext must be .jpg
        saveName = dal.photoFileName(username, trial.id, traitid, int(nodeIdStr), token, seqNum, sampNum)
        try:
            file.save(app.config['PHOTO_UPLOAD_FOLDER'] + saveName)
        except Exception, e:
            util.flog('failed save {0}'.format(app.config['PHOTO_UPLOAD_FOLDER'] + saveName))
            util.flog(e.__doc__)
            util.flog(e.message)
            return serverErrorResponse('Failed photo upload : can''t save')

        # Now save datum record:
        # get TI - this should already exist, which is why we can pass in 0 for dayCreated
        # MFK note this outer if below is to support old versions of the app, to allow them to
        # upload their photos in the old way. It should be removed eventually..
        if nodeId is not None and len(nodeId) > 0:
            dbTi = dal.GetOrCreateTraitInstance(dbc, traitid, trial.id, seqNum, sampNum, dayCreated, token)
            if dbTi is None:
                return serverErrorResponse('Failed photo upload : no trait instance')
            res = dal.AddTraitInstanceDatum(dbc, dbTi.id, dbTi.trait.type, nodeId, timestamp, userid, gpslat, gpslong)
            if res is None:
                return Response('success')
            else:
                return serverErrorResponse('Failed photo upload : datum create fail')
        else:
            util.flog('upload_photo: no nodeId, presumed old app version')
            return Response('success')
    else:
        return serverErrorResponse('Failed photo upload : bad file')


#
# upload_trial()
#
# Test data:
# https://***REMOVED***/owalboc/user/mk/trial/1/?pw=sec&andid=x
# Content-Type : application/json
# {"name":"josh", "serverToken":"tok",
# "traitInstances":[{"trait_id":1,"dayCreated":2,"seqNum":1,"sampleNum":1,"data":[]}]}
#
# Currently only used for uploading node notes, since the traitInstances are
# individually uploaded via the upload_trait_data().
#
# MFK - Ideally we would add the token to the URL, as has been done for upload_trait_data.
# Have to be carefully however about breaking the protocol for devices out there with
# the URL without a token..
#
@app.route('/user/<username>/trial/<trialid>/', methods=['POST'])
@dec_get_trial(False)
#-------------------------------------------------------------------------------------------------
def upload_trial(username, trial, dbc):
    jtrial = request.json
    util.flog("upload_trial:\n" + json.dumps(jtrial))

    if not jtrial:
        return Response('Bad or missing JSON')
    try:
        token = jtrial[jTrialUpload['serverToken']]
    except Exception, e:
        return Response('Missing field: ' + e.args[0])

    if 'notes' in jtrial:   # We really should put these JSON names in a set of string constants somehow..
        err = dal.AddNodeNotes(dbc, token, jtrial[jTrialUpload['notes']])
        if err is not None:
            util.flog('AddNodeNotes fail:{0}'.format(err))
            return Response(err)

    # All done, return success indicator:
    return Response('success')


@app.route('/user/<username>/trial/<trialid>/createAdHocTrait/', methods=['GET'])
@dec_get_trial(True)
def create_adhoc(username, trl, dbc):
#-------------------------------------------------------------------------------------------------
# Create an adhoc trait, and return the id of the trait in JSON
# This should be a url.
#
    # Bundle all this into get_trial(username, password), may not need dbs if all can be done from trial object
    # password = request.args.get('pw', '')
    # androidId = request.args.get('andid', '')

    caption = request.args.get('caption', '')
    description = request.args.get('description', '')
    vtype = request.args.get('type', '')
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


def LogDebug(hdr, text):
#-------------------------------------------------------------------------------------------------
# Writes stuff to file system (for debug)
    if gdbg:
        f = open('/tmp/fieldPrimeDebug','a')
        print >>f, "--- " + str(datetime.now()) + " " + hdr + ": -------------------"
        print >>f, text
        f.close


#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
# Old stuff:

def error_404(msg):
    response = Response(msg)
    response.status_code = 404
    return response

def serverErrorResponse(msg):
    util.flog(msg)
    response = Response(msg)
    response.status = '500 {0}'.format(msg)
    return response


#############################################################################################

@app.route('/')
def hello_world():
    return 'Hello Sailor!'

# For local testing:
if __name__ == '__main__':
    from os.path import expanduser
    app.config['PHOTO_UPLOAD_FOLDER'] = expanduser("~") + '/proj/fpserver/photos/'
    app.config['FPLOG_FILE'] = expanduser("~") + '/proj/fpserver/fplog/fp.log'

    # Setup logging:
    app.config['FP_FLAG_DIR'] = expanduser("~") + '/proj/fpserver/fplog/'
    util.initLogging(app, True)  # Specify print log messages
    util.flog("calling flog")

    app.run(debug=True, host='0.0.0.0')

