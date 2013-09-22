# fpApi.py
# Michael Kirk 2013
# 
#


from flask import Flask, request, Response, url_for
from flask import json, jsonify

import os, sys, time
from functools import wraps
from werkzeug import secure_filename
from jinja2 import Environment, FileSystemLoader

if __name__ == '__main__':
    import os,sys,inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0,parentdir) 


import fp_common.dbUtil
from fp_common.fpTrait import TRAIT_TYPE_TYPE_IDS, SYSTYPE_ADHOC


app = Flask(__name__)
try:
    app.config.from_object('fp_app_api.fpAppConfig')
except ImportError:
    pass

# If env var FPAPI_SETTINGS is set then load configuration from the file it specifies:
app.config.from_envvar('FPAPI_SETTINGS', silent=True)

# Load the Data Access Layer Module (must be named in the config)
# dal = __import__(app.config['DATA_ACCESS_MODULE'])
# print app.config['DATA_ACCESS_MODULE']
# print dal.models.DbConnectAndAuthenticate

import importlib
dal = importlib.import_module(app.config['DATA_ACCESS_MODULE'])

gdbg = True  # Switch for logging to file


##################################################################################################


def dec_get_trial(jsonReturn):
#-------------------------------------------------------------------------------------------------
# Decorator, for function that takes a username and trialid.
# It is assumed there is a request in context. and this contains a password and android ID.
# The password is checked, and the trial object retrieved and passed to the decoratee instead
# of the trialid. The open db connection is also added as a third parameter.
# On error, if jsonReturn then a json error message is returned, else a plain text one.
#
    def param_dec(func):
        @wraps(func)
        def inner(username, trialid, *args, **kwargs):
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
#-------------------------------------------------------------------------------------------------
def get_trial(username, trl, dbc):
    androidId = request.args.get('andid', '')

    # Trial attributes:
    jtrl = {'name':trl.name, 'site':trl.site, 'year':trl.year, 'acronym':trl.acronym}
    jtrl['adhocURL'] = url_for('create_adhoc', username=username, trialid=trl.id, _external=True)
    jtrl['uploadURL'] = url_for('upload_trial', username=username, trialid=trl.id, _external=True)

    # Server Token:
    # Use the android device ID postfixed with the current time in seconds as the serverTrialId.
    # This should ensure different tokens for the same trial being downloaded multiple times on
    # a single device (with delete in between), as long as they are not created within the same
    # second (and this is not an expected use case):
    epoch = int(time.time())
    servToken = androidId + "." + str(int(time.time()))
    jtrl['serverToken'] = servToken

    # Attribute Names:
    attNames = []
    for att in trl.attributeNames:
        attNames.append(att.name)
    jtrl['attributes'] = attNames

    # Trial Units:
    tuList = []
    tuNames = ["id", "row", "col", "description", "barcode"]
    for ctu in trl.trialUnits:
        jtu = {}
        # Trial unit attributes:
        for n in tuNames:
            jtu[n] = getattr(ctu, n)        
        # Attribute values:
        for att in ctu.attVals:
            jtu[att.trialUnitAttribute.name] = att.value        
        tuList.append(jtu)
    jtrl['trialUnits'] = tuList

    # Traits:
    traitList = []
    traitFieldNames = ['id', 'sysType', 'min', 'max', 'caption', 'description', 'type', 'unit']
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

        # Fields for categorical traits:
        if trt.type == TRAIT_TYPE_TYPE_IDS['Categorical']:
            cats = []
            for cat in trt.categories:
                oneCat = {}
                for fieldName in ['caption', 'value', 'imageURL']:
                    oneCat[fieldName] = getattr(cat, fieldName)
                cats.append(oneCat)
            jtrait['categories'] = cats
        elif trt.type == TRAIT_TYPE_TYPE_IDS['Photo']:
            jtrait['photoUploadURL'] = url_for('upload_photo', username=username, trialid=trl.id, traitid=trt.id,
                                      token=servToken, _external=True)

        traitList.append(jtrait)
    jtrl['traits'] = traitList

    return Response(json.dumps(jtrl), mimetype='application/json')

#
# upload_trait_data()
# Trait instances are uniquely identified by trial/trait/token/seqNum/sampleNum.
#
@app.route('/user/<username>/trial/<trialid>/trait/<traitid>/device/<token>/', methods=['POST'])
@dec_get_trial(False)
#-------------------------------------------------------------------------------------------------
def upload_trait_data(username, trial, dbc, traitid, token):
    password = request.args.get('pw', '')
    jti = request.json
    if gdbg:
        LogDebug("upload_trial:", json.dumps(jti))
    if not jti:
        return Response('Bad or missing JSON')

    errMsg = process_ti_json(jti, trial, traitid, token, dbc)
    if (errMsg is not None):
        return Response(errMsg)
    else:
        return Response('success')

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
#-------------------------------------------------------------------------------------------------
def upload_photo(username, trial, dbc, traitid, token):
    seqNum = request.args.get('seqNum', '')
    sampNum = request.args.get('sampleNum', '')
    file = request.files.get('uploadedfile')
    #LogDebug("upload_photo:", seqNum + ':' + sampNum)
    if file and allowed_file(file.filename):
        sentFilename = secure_filename(file.filename)
        #LogDebug("upload_photo:", 'filename:' + sentFilename)
        filename = '{0}_{1}_{2}_{3}_{4}_{5}_{6}'.format(username, trial.id, traitid, token, seqNum, sampNum, sentFilename)
        file.save(app.config[PHOTO_UPLOAD_FOLDER] + filename)
    return Response('success')


#
# process_ti_json()
# Return None on success, else error string.
# Separate func as used in two places (but one of these places now obselete, as we now upload individual tis)
def process_ti_json(ti, trial, traitID, token, dbc):
    try:
        dayCreated = ti["dayCreated"]
        seqNum = ti["seqNum"]
        sampleNum = ti["sampleNum"]
        aData = ti["data"]
    except Exception, e:
        return 'Missing traitInstance field: ' + e.args[0] + trial.name

    # There seems no point in processing a traitInstance with no data:
    if len(aData) <= 0:
        return None

    dbTi = dal.GetOrCreateTraitInstance(dbc, traitID, trial.id, seqNum, sampleNum, dayCreated, token)
    if dbTi is None:
        return 'Unexpected error retrieving or creating trait instance'

    # Now add the datums:
    return dal.AddTraitInstanceData(dbc, dbTi.id, dbTi.trait.type, aData)


#
# upload_trial()
#
# Test data:
# https://***REMOVED***/owalboc/user/mk/trial/1/?pw=sec&andid=x
# Content-Type : application/json
# {"name":"josh", "serverToken":"tok",
# "traitInstances":[{"trait_id":1,"dayCreated":2,"seqNum":1,"sampleNum":1,"data":[]}]}
#
# NB - currently not used, replaced by individual ti upload above
# Actually, we're using it again now, for notes.
# MFK - Ideally we would add the token to the URL, as has been done for upload_trait_data.
# Have to be carefully however about breaking the protocol for devices out there with
# the URL without a token..
#
@app.route('/user/<username>/trial/<trialid>/', methods=['POST'])
@dec_get_trial(False)
#-------------------------------------------------------------------------------------------------
def upload_trial(username, trial, dbc):
    password = request.args.get('pw', '')
    #androidId = request.args.get('andid', '')
    jtrial = request.json
    if gdbg:
        LogDebug("upload_trial:", json.dumps(jtrial))
    if not jtrial:
        return Response('Bad or missing JSON')
    try:
        token = jtrial['serverToken']
        # tis = jtrial['traitInstances']    # Not compulsory anymore, there might just be "notes" for example
    except Exception, e:
        return Response('Missing field: ' + e.args[0])

    # Process trait instances:  MFK current client will not upload tis this way, but need to leave this
    # here a while perhaps while there still may be older clients.
    if 'traitInstance' in jtrial:
        tis = jtrial['traitInstances']
        for ti in tis:  # loop over tis, note returns error if any fail.
            try:
                traitID = ti["trait_id"];  # This could be part of trait upload instance URL
                dayCreated = ti["dayCreated"]
                seqNum = ti["seqNum"]
                sampleNum = ti["sampleNum"]
                aData = ti["data"]
            except Exception, e:
                return Response('Missing traitInstance field: ' + e.args[0] + trial.name)

            errMsg = process_ti_json(ti, trial, traitID, token, dbc)
            if (errMsg is not None):
                return Response(errMsg)

    if 'notes' in jtrial:   # We really should put these JSON names in a set of string constants somehow..
        dal.AddTrialUnitNotes(dbc, token, jtrial['notes'])
        # notes = jtrial['notes']
        # for note in notes:
        #     tuId = note['trialUnit_id']
        #     timestamp = note['timestamp']
        #     userid = note['userid']    # the name of the note taker
        #     noteText = note['note']
        #     dal.AddTrialUnitNote(dbc, tuId, timestamp, userid, noteText)


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
    vmin = request.args.get('min', '')
    vmax = request.args.get('max', '')
    ntrt, errMsg = dal.CreateTrait2(dbc, caption, description, vtype, SYSTYPE_ADHOC, vmin, vmax)
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
    f = open('/tmp/fieldPrimeDebug','a')
    print >>f, "--- " + hdr + ": ---"
    print >>f, text
    print >>f, "------------------"
    f.close


#-------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------
# Old stuff:



def error_404():
    response = Response('Resource not found')
    response.status_code = 404
    return response

def PostRequest(request, environ, start_response):
    f = open('/tmp/xyzPost','a')
    print >>f, request
    print >>f, request.files
    file = request.files.get('uploadedfile')
    response = Response()
    if file:
        file.save('/tmp/' + file.filename)
    else:
        f.write("Not File")
        response.status_code = 400
    return response(environ, start_response)



#############################################################################################

@app.route('/')
def hello_world():
    return 'Hello Sailor!'

# For local testing:
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
