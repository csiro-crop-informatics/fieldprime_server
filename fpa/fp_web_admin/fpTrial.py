# trial.py
# Michael Kirk 2013
#
# Code for creation of new trials
#


import sys, os
import sqlalchemy
from flask import render_template
import fpUtil
import dbUtil
from fp_common.models import Trial, TrialUnit, TrialUnitAttribute, AttributeValue, Trait
from fp_common.util import ldebug

#
# Special column headers.
# If present in the uploaded trial file, these become column headers
# indicate node members rather than generic attributes:
#
ATR_ROW = 'row'
ATR_COL = 'column'
ATR_DES = 'description'
ATR_BAR = 'barcode'
ATR_LAT = 'latitude'
ATR_LON = 'longitude'
FIXED_ATTRIBUTES = [ATR_ROW, ATR_COL, ATR_DES, ATR_BAR, ATR_LAT, ATR_LON]

def ParseTrialUnitCSV(f):
#-----------------------------------------------------------------------
# Parses the file to check valid trial input. Also determines the
# number of fields, and the column index of each fixed and attribute columns.
# Returns dictionary, with either an 'error' key, or the above fields.
#
    # Get headers,
    hdrs = f.readline().strip().split(',')
    numFields = 0
    fixIndex = {}
    attIndex = {}
    for hd in hdrs:
        if not hd:
            return {'error':"Error - Empty column header found, aborting."}
        hdl = hd.lower()
        if hdl in FIXED_ATTRIBUTES:
            fixIndex[hdl] = numFields
        elif hd in attIndex.keys():
            return {'error':"Error - Duplicate attribute name ({0}), aborting.".format(hd)}
        else:
            attIndex[hd] = numFields
        numFields += 1

    # Check both row and column are present:
    for mand in [ATR_ROW, ATR_COL]:
        if not mand in fixIndex.keys():
            return {'error':"Error - Missing required column ({0}), aborting.".format(mand)}

    # Check that if either latitude or longitude are present then they both are,
    # else revert the one present to a generic attribute:
    if ATR_LAT in fixIndex.keys() and not ATR_LON in fixIndex.keys():
        attIndex[ATR_LAT] = fixIndex[ATR_LAT]
        del fixIndex[ATR_LAT]
    if ATR_LON in fixIndex.keys() and not ATR_LAT in fixIndex.keys():
        attIndex[ATR_LON] = fixIndex[ATR_LON]
        del fixIndex[ATR_LON]


    # Check trialUnit lines:
    line = f.readline()
    rowNum = 2
    while line:
        flds = line.strip().split(',')
        if not len(flds) == numFields:
            err =  "Error - wrong number of fields ({0}, should be {1}), line {2}, aborting. <br>".format(len(flds), numFields, rowNum)
            err += "Bad line was: " + line
            return {'error':err}
        if not (flds[fixIndex[ATR_ROW]].isdigit and flds[fixIndex[ATR_COL]].isdigit):
            return {'error':"Error - row or col field is not integer, line {0}, aborting".format(rowNum)}
        #print line + "<br>"
        rowNum += 1
        line = f.readline()

    # All good
    return {'numFields':numFields, 'fixIndex':fixIndex, 'attIndex':attIndex}



def uploadTrialFile(sess, f, tname, tsite, tyear, tacro):
#-----------------------------------------------------------------------
# Handle submitted create trial form.
# Return None on success, else dictionary with 'error' key.
#
    db = sess.DB()
    try:
        # Create trial:
        ntrial = Trial()
        ntrial.name = tname
        ntrial.site = tsite
        ntrial.year = tyear
        ntrial.acronym = tacro
        db.add(ntrial)
        db.commit()
        res = updateTrialFile(sess, f, ntrial.id)
        if res is not None and 'error' in res:
            return res
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"Database error ({0})".format(e.orig.args)}
    return None


def updateTrialFile(sess, trialCsv, trialId):
#-----------------------------------------------------------------------
# Update trial data according to csv file trialCsv.
# The trial should already exist. First line is headers,
# each subsequent line a node. The nodes, identified by trial/row/col
# may already exist or not. If not they are created, else updated.
#
# Any attribute columns in the file will be added to the trial
# and any attributes that match existing attributes
# will overwrite them.
# Returns None on success, else dictionary with 'error' key.
#
# Notes:
# Ideally, perhaps, for existing attributes, only new values
# would be overwritten, however, all values are - basically because
# with the current trial creation method (uploading from csv) an
# attributeValue gets created for every trial unit listed in the the
# upload file, even if the string value is empty.
#
# Note also that if a node is not listed in an upload file then its
# attribute values will remain - i.e. you would need to explicitly
# overwrite them to clear or delete them.
#
# NB It turns out that mysql varchar is by default case insensitive,
# in that if you search for a given string value, incorrect case
# values will match. This precludes having columns with names only
# differing in case.
#
    # Check trial units csv file:
    tuFileInfo = ParseTrialUnitCSV(trialCsv)  # Ideally need version that checks trial units, should we allow new ones?
    if 'error' in tuFileInfo:
        return tuFileInfo
    fixIndex = tuFileInfo['fixIndex']
    attIndex = tuFileInfo['attIndex']

    dbSess = sess.DB()
    try:
        trl = dbUtil.GetTrial(sess, trialId)

        # Add attributes:
        currAtts = dbUtil.GetTrialAttributes(sess, trialId)
        tuaObs = []
        attExists = []    # array of booleans indicating whether corresponding attIndex attribute exists already
        for at in attIndex.keys():
            # Does this attribute already exist?
            tua = None
            for cat in currAtts:
                if cat.name.upper() == at.upper():
                    tua = cat
                    break
            attExists.append(tua is not None)
            if tua is None:
                tua = TrialUnitAttribute()
                tua.trial_id = trl.id
                tua.name = at
                dbSess.add(tua)
            tuaObs.append(tua)
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"DB error adding trialUnitAttribute ({0})".format(e.orig.args)}
    try:
        # Iterate thru the nodes (each line is assumed to be a node):
        trialCsv.seek(0,0)
        trialCsv.readline() # skip headers
        line = trialCsv.readline()
        while line:
            flds = line.strip().split(',')
            # Get or create the node (specified by row/col):
            tu = trl.addOrGetNode(flds[fixIndex[ATR_ROW]], flds[fixIndex[ATR_COL]])
            if tu is None:
                out = "Problem getting or creating node: row" + str(flds[fixIndex[ATR_ROW]]) + " col " + str(flds[fixIndex[ATR_COL]])
                return {'error':out}

            # Update fixed node attributes in the node struct:
            if ATR_BAR in fixIndex.keys(): tu.barcode = flds[fixIndex[ATR_BAR]]
            if ATR_DES in fixIndex.keys(): tu.description = flds[fixIndex[ATR_DES]]
            if ATR_LAT in fixIndex.keys(): tu.latitude = flds[fixIndex[ATR_LAT]]
            if ATR_LON in fixIndex.keys(): tu.longitude = flds[fixIndex[ATR_LON]]

            # add attributes:
            for ind, attName in enumerate(attIndex.keys()):
                errMsg = 'Error adding {1} attribute {0}:'.format(attName, 'existing' if str(attExists[ind]) else 'new')
                tua = tuaObs[ind]
                newValue = flds[attIndex[attName]].strip() # get value minus surrounding whitespace

                # Get existing attributeValue if it exists.
                # If it does and newValue is empty then delete it.
                av = None
                if attExists[ind]:
                    try:
                        av = dbUtil.getAttributeValue(sess, tu.id, tua.id)
                    except Exception as e:
                            errMsg += " tua:" + str(tua.id) + " tuid:" + str(tu.id)
                            return {'error':("Missing attribute: " + errMsg)}
                    if av is not None and not newValue:
                        # If there is existing record, but new value is empty, then delete existing record:
                        dbSess.delete(av)
                        continue

                if not newValue:  # don't add empty value
                    continue

                # Create new attributeValue if necessary:
                if av is None:
                    # Set up new attribute value:
                    av = AttributeValue()
                    av.trialUnitAttribute = tua
                    av.trialUnit = tu
                    dbSess.add(av)

                av.setValueWithTypeUpdate(newValue)  # set the value
#                 if not attExists[ind]:   # Add to db, if new
#                     dbSess.add(av)

            line = trialCsv.readline()
        dbSess.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"DB error adding attributeValue ({0})".format(e.orig.args)}
    return None

