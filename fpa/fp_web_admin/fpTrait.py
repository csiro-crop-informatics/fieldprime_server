#
# fpTrait.py
# Michael Kirk 2013
#

import os, re
from werkzeug import secure_filename
import flask
from flask import Flask, request, url_for, redirect

import fp_common.models as models
from fp_common.const import *
import fp_common.util as util
import datapage as dp
import fpUtil


app = flask.current_app

#-- FUNCTIONS: ---------------------------------------------------------------------

def traitListHtmlTable(traitList):
#-----------------------------------------------------------------------
# Returns html table of traitList
#
    if len(traitList) < 1:
        return "No traits configured"
    out = "<table class='fptable' cellspacing='0' cellpadding='5'>"
    out += "<tr><th>{0}</th><th>{1}</th><th>{2}</th></tr>".format("Caption", "Description", "Type")
    for trt in traitList:
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>".format(
            trt.caption, trt.description, TRAIT_TYPE_NAMES[trt.datatype])
    out += "</table>"
    return out


def createNewTrait(sess,  trialId, request):
#-----------------------------------------------------------------------
# Create trait in db, from data from html form.
# trialId is id of trial if a local trait, else it is -1.
# Returns error message if there's a problem, else None.
#
    caption = request.form.get("caption")
    description = request.form.get("description")
    type = request.form.get("type")
    isProjectTrait = True if trialId == -1 else False

    dbsess = sess.db()
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    if not isProjectTrait: # If local, check there's no other trait local to the trial with the same caption:
        trial = models.getTrial(sess.db(), trialId)
        for x in trial.traits:
            if x.caption == caption:
                return 'Error: A local trait with this caption already exists'
    else:  # If system trait, check there's no other system trait with same caption:
        projTraits = sess.getProject().getTraits()
        for x in projTraits:
            if x.caption == caption:
                return 'Error: A system trait with this caption already exists'
    ntrt = models.Trait(caption, description, type, isProjectTrait,
                        sess.getProject().id if isProjectTrait else trialId)
    if not isProjectTrait:
        ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
    dbsess.add(ntrt)
    dbsess.commit()   # Add the trait to the db (before trait specific stuff which may need id).
    # Trait type specific processing:
    if int(ntrt.datatype) == T_CATEGORICAL:
        _newTraitCategorical(sess, request, ntrt)
    dbsess.add(ntrt)
    dbsess.commit()
    return None

def _addTrait2Trial(sess, trial, trait):
#-----------------------------------------------------------------------
    # Check no trait with this caption already in trial:
    for trt in trial.traits:
        if trt.caption == trait.caption:
            return 'Error: Trial {0} already has trait with caption "{1}"'.format(trial.name, trait.caption)
    trait.trials.append(trial);
    sess.db().commit()
    return None

def addTrait2Trial(sess, trialId, traitId):
#-----------------------------------------------------------------------
# Return error string, None for success
    trial = models.getTrial(sess.db(), trialId)
    trait = models.getTrait(sess.db(), traitId)
    return _addTrait2Trial(sess, trial, trait)


# Could put all trait type specific stuff in trait extension classes.
# Aiming for this file to not contain any type specific code.
# class pTrait(models.Trait):
#     def ProcessForm(form):
#         pass

def allowed_file(filename):  # MFK cloned code warning
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def _newTraitCategorical(sess, request, trt):
    capKeys = [key for key in request.form.keys() if key.startswith("caption_")]
    for key in capKeys:
        caption = request.form.get(key)
        value = request.form.get(key.replace("caption_", "value_"))

        # If image provided we need to store it
        imageURL = None
        try:
            imageURLFile = request.files[key.replace("caption_", "imgfile_")]
            if imageURLFile:
                sentFilename = secure_filename(imageURLFile.filename)
                if allowed_file(sentFilename):
                    # Note, file are stored under a configured category image folder,
                    # and then with path <userName>/<trait id>/<value>.<original file extension>
                    subpath = os.path.join(app.config['CATEGORY_IMAGE_FOLDER'], sess.getProject(), str(trt.id))
                    if not os.path.exists(subpath):
                        os.makedirs(subpath)
                    fileExt = sentFilename.rsplit('.', 1)[1]
                    newFilename = '{0}.{1}'.format(value, fileExt)
                    imageURLFile.save(subpath +  "/" + newFilename)
                    imageURL = app.config['CATEGORY_IMAGE_URL_BASE'] + "/" + sess.getProject() + "/" + str(trt.id) + "/" + newFilename
                else:
                    util.flog("_newTraitCategorical bad file name")
        except Exception, e:
            util.flog("Exception: {0}".format(str(e)))


        util.flog("A key category: cap:{0} value:{1}".format(caption, value))

        # MFK here we should determine if this is an existing category - in which we may need
        # to update fields or a new one. Trait categories are identified by the value (within
        # a trait).
        tcat = trt.getCategory(value)
        newCat = tcat is None
        if newCat:
            # Add new trait category:
            tcat = models.TraitCategory()
            tcat.value = value
            tcat.caption = caption
            tcat.trait_id = trt.id
            tcat.imageURL = imageURL
            sess.db().add(tcat)

        else:
            util.flog("Existing category: cap:{0} value:{1}".format(caption, value))
            # This is an existing category, update caption, or image URL if necessary:
            if tcat.caption != caption:
                tcat.caption = caption
            tcat.imageURL = imageURL

        # Note no commit - we assume calling function will do it.


def traitDetailsPageHandler(sess, request, trialId, traitId):
#===========================================================================
# Handles both GET and POST for page to display/modify details for a trait.
#
# MFK Note overlap with code from trait creation.
#
    trt = models.getTrait(sess.db(), traitId)
    trlTrt = models.getTrialTrait(sess.db(), trialId, traitId)
    trial = models.getTrial(sess.db(), trialId)
    title = 'Trial: ' + trial.name + ', Trait: ' + trt.caption
    comparatorCodes = [
        ["gt", "Greater Than", 1],
        ["ge", "Greater Than or Equal to", 2],
        ["lt", "Less Than", 3],
        ["le", "Less Than or Equal to", 4]
    ]

    if request.method == 'GET':
        ###########################################################################
        # Form fields applicable to all traits:
        ###
        formh = fpUtil.htmlLabelValue('Trait', trt.caption) + '<br>'
        formh += fpUtil.htmlLabelValue('Type', TRAIT_TYPE_NAMES[trt.datatype])
        formh += fpUtil.htmlHorizontalRule()

        formh += fpUtil.htmlLabelValue('Description',
            '<input type="text" size=96 name="description" value="{0}">'.format(trt.description))

        # Trait barcode selection:
        # Note it doesn't matter if a sysTrait, since the barcode is stored in trialTrait
        attSelector = '<select name="bcAttribute" id="bcAttribute">'
        attSelector += '<option value="none">&lt;Choose Attribute&gt;</option>'
        atts = trial.nodeAttributes
        for att in atts:
            attSelector += '<option value="{0}" {2}>{1}</option>'.format(
                att.id, att.name, "selected='selected'" if att.id == trlTrt.barcodeAtt_id else "")
        attSelector += '</select>'
        formh += '<br>' + fpUtil.htmlLabelValue('Barcode for Scoring', attSelector)

        # Vars that may be set by trait specifics, to be included in output:
        preform = ''
        onsubmit = ''
        if trt.datatype == T_CATEGORICAL:
            # Note the intended policy: Users may modify the caption or image of an existing
            # category, but not change the numeric value. They may add new categories.
            # The reasoning is that they should remove existing categories (as identified
            # by the value) because there may be data collected already with the values
            # which would then become undefined, or perhaps ambiguous. We could have a look
            # up and allow removal if there is no data, but we cannot be sure data will
            # not come in in the future referencing current values (unless we know trial
            # has never been downloaded). In any case this limited functionality is better
            # than none.

            #####
            ## Setup javascript to manage the display/modification of the categories.
            #####

            # Retrieve the categories from the database and make of it a javascript literal:
            catRecs = trt.categories
            catObs = ''
            first = True
            for cat in catRecs:
                if first:
                    first = False
                else:
                    catObs += ','
                catObs += '{{caption:"{0}", imageURL:"{1}", value:{2}}}'.format(cat.caption, cat.imageURL, cat.value)
            jsRecDec = '[{0}]'.format(catObs)
            print jsRecDec

            div = '<div id="traitDiv"></div>\n'
            scrpt1 = """<script src="{0}"></script>\n""".format(url_for('static', filename='newTrait.js'))
            scrpt2 = """<script type="text/javascript">
            $(document).ready ( function(){{
                if (typeof(SetTraitFormElements) === "function") {{
                   SetTraitFormElements('traitDiv', '3', {0});
                }} else alert('no SetTraitFormElements');
            }});</script>""".format(jsRecDec)
            formh += div + scrpt1 + scrpt2
        elif trt.datatype == T_INTEGER or trt.datatype == T_DECIMAL:
            #
            # Generate form on the fly. Could use template but there's lots of variables.
            # Make this a separate function to generate html form, so can be used from
            # trait creation page.
            #
            ttn = models.GetTrialTraitNumericDetails(sess.db(), traitId, trialId)

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
                        alert("Comparator selected with no attribute specified, please fix.");
                        return false;
                    }
                    return true;
                }
                </script>
            """

            formh += minMaxBounds
            formh += '<p>Integer traits can be validated by comparison with an attribute:'
            formh += '<br>Trait value should be ' + valOp + attListHtml
            preform = script
            onsubmit ='return validateTraitDetails()'
        elif trt.datatype == T_STRING:
            tts = models.getTraitString(sess.db(), traitId, trialId)
            patText = "value='{0}'".format(tts.pattern) if tts is not None else ""
            formh += "<p>Pattern: <input type='text' name='pattern' id=tdMin {0}>".format(patText)

        formh += ('\n<p><input type="button" style="color:red" value="Cancel"' +
            ' onclick="location.href=\'{0}\';">'.format(url_for("urlTrial", trialId=trialId)))
        formh += '\n<input type="submit" style="color:red" value="Submit">'
        return dp.dataPage(sess,
                    content=preform + fpUtil.htmlForm(formh, post=True, onsubmit=onsubmit, multipart=True),
                    title='Trait Validation', trialId=trialId)

    ##################################################################################################
    if request.method == 'POST':
        ### Form fields applicable to all traits:
        # Trait barcode selection:
        #MFK sys traits? barcode field is an nodeAttribute id but this is associated with a trial
        # we either have to move it to trialTrait, or make all trial traits non system traits.
        barcodeAttId = request.form.get('bcAttribute')  # value should be valid attribute ID
        if barcodeAttId == 'none':
            trlTrt.barcodeAtt_id = None
        else:
            trlTrt.barcodeAtt_id = barcodeAttId
        trt.description = request.form.get('description')

        #
        # Trait type specific stuff:
        #
        if trt.datatype == T_CATEGORICAL:
            _newTraitCategorical(sess, request, trt)
        elif trt.datatype == T_INTEGER or trt.datatype == T_DECIMAL: # clone of above remove above when integer works with numeric
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
            ttn = models.GetTrialTraitNumericDetails(sess.db(), traitId, trialId)
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
                sess.db().add(ttn)
        elif trt.datatype == T_STRING:
            newPat = request.form.get('pattern')
            tts = models.getTraitString(sess.db(), traitId, trialId)
            if len(newPat) == 0:
                newPat = None
            # delete tts if not needed:
            if not newPat:
                if tts:
                    sess.db().delete(tts)
            else:
                if tts:
                    tts.pattern = newPat
                else:
                    tts = models.TraitString(trait_id=traitId, trial_id=trialId, pattern=newPat)
                    sess.db().add(tts)

        sess.db().commit()

        return redirect(url_for("urlTrial", trialId=trialId))


