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

ROW = 'row'
COL = 'column'
DES = 'description'
BAR = 'barcode'


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
        if (hdl == ROW):
            fixIndex[ROW] = numFields
        elif (hdl == COL):
            fixIndex[COL] = numFields
        elif (hdl == DES):
            fixIndex[DES] = numFields
        elif (hdl == BAR):
            fixIndex[BAR] = numFields
        else:
            if hd in attIndex.keys():
                return {'error':"Error - Duplicate attribute name ({0}), aborting.".format(hd)}
            attIndex[hd] = numFields 
        numFields += 1

    for mand in [ROW, COL]:
        if not mand in fixIndex.keys():
            return {'error':"Error - Missing required column ({0}), aborting.".format(mand)}
        
    # Check trialUnit lines:
    line = f.readline()
    rowNum = 2
    while line:
        flds = line.strip().split(',')
        if not len(flds) == numFields:
            err =  "Error - wrong number of fields ({0}, should be {1}), line {2}, aborting. <br>".format(len(flds), numFields, rowNum)
            err += "Bad line was: " + line
            return {'error':err}
        if not (flds[fixIndex[ROW]].isdigit and flds[fixIndex[ROW]].isdigit):
            return {'error':"Error - row or col field is not integer, line {0}, aborting".format(rowNum)}
        #print line + "<br>"
        rowNum += 1
        line = f.readline()

    # All good
    return {'numFields':numFields, 'fixIndex':fixIndex, 'attIndex':attIndex}


def UploadTrialFile(sess, f, tname, tsite, tyear, tacro):
#-----------------------------------------------------------------------
# Handle submitted create trial form.
# Return None on success, else dictionary with 'error' key.
#
    # Check trial units csv file:
    tuFileInfo = ParseTrialUnitCSV(f)
    if 'error' in tuFileInfo:
        return tuFileInfo

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

        # when finished should give error msg or go back to a trial list, or display of new trial
        # Trial units
        f.seek(0,0)
        f.readline() # skip headers
        numFields = tuFileInfo['numFields']
        fixIndex = tuFileInfo['fixIndex']
        attIndex = tuFileInfo['attIndex']

        # Add attributes
        tuaObs = {}
        for at in attIndex.keys():
            tua = TrialUnitAttribute()
            tua.trial_id = ntrial.id
            tua.name = at
            db.add(tua)
            tuaObs[at] = tua

        # Add trial units
        line = f.readline()
        while line:
            flds = line.strip().split(',')
            tu = TrialUnit()
            tu.trial_id = ntrial.id
            tu.row = flds[fixIndex[ROW]]
            tu.col = flds[fixIndex[COL]]
            if BAR in fixIndex.keys(): tu.barcode = flds[fixIndex[BAR]]
            if DES in fixIndex.keys(): tu.description = flds[fixIndex[DES]]
            db.add(tu)
            # add attributes:
            for at in attIndex.keys():
                av = AttributeValue()
                av.trialUnitAttribute = tuaObs[at]
                av.trialUnit = tu
                av.value = flds[attIndex[at]]
                db.add(av)
            line = f.readline()

        db.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"Database error ({0})".format(e.orig.args)}
    return None


def UpdateTrialFile(sess, f, trialId):
#-----------------------------------------------------------------------
# Handle uploaded trial file for updating. I.e. the trial should
# exist, but we are to add or update any attributes in the file.
# Return None on success, else dictionary with 'error' key.
#
    #return {'error':"to err is human"}
    
    # Check trial units csv file:
    tuFileInfo = ParseTrialUnitCSV(f)  # Ideally need version that checks trial units, should we allow new ones?
    if 'error' in tuFileInfo:
        return tuFileInfo

    db = sess.DB()
    ln = 0
    try:
        trl = dbUtil.GetTrial(sess, trialId)

        # when finished should give error msg or go back to a trial list, or display of new trial
        # Trial units
        f.seek(0,0)
        f.readline() # skip headers
        numFields = tuFileInfo['numFields']
        fixIndex = tuFileInfo['fixIndex']
        attIndex = tuFileInfo['attIndex']

        # Add attributes  MFK Clear existing attributes?
        currAtts = dbUtil.GetTrialAttributes(sess, trialId)
        # currAttNames = []
        # for a in currAtts:
        #     currAttNames.append(a.name.upper())
        #return {'error':', '.join(currAttNames)}
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
                db.add(tua)
            tuaObs.append(tua)
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"DB error adding trialUnitAttribute ({0})".format(e.orig.args)}
    try:
        # Iterate thru trial units:
        ln = 1
        line = f.readline()
        while line:
            flds = line.strip().split(',')
            ln = 4
            try:
                tu = dbUtil.GetTrialUnit(sess, trialId, flds[fixIndex[ROW]], flds[fixIndex[COL]])
            except Exception as e:
                out = "Ex row " + str(flds[fixIndex[ROW]]) + " col " + str(flds[fixIndex[COL]])
                #out = "Ex row " + str(fixIndex[ROW]) + " col " + str(fixIndex[COL])
                return {'error':out}
            ln = 3
            # Update barcode and/or description:
            if BAR in fixIndex.keys(): tu.barcode = flds[fixIndex[BAR]]
            if DES in fixIndex.keys(): tu.description = flds[fixIndex[DES]]
            # add attributes:
            for ind, attName in enumerate(attIndex.keys()):
                out = attName + " ind: " + str(ind) + " exists: " + str(attExists[ind])
                #return {'error':out}
                tua = tuaObs[ind]
                ln = 2
                if attExists[ind]:
                    try:
                        av = dbUtil.GetAttributeValue(sess, tu.id, tua.id)
                        if av is None:
                            out += " tua " + str(tua.id) + " tuid " + str(tu.id)
                            return {'error':out}
                    except Exception as e:
                            out += "Ex tua " + str(tua.id) + " tuid " + str(tu.id)
                            return {'error':out}
                else:
                    av = AttributeValue()
                    
                av.trialUnitAttribute = tua
                av.trialUnit = tu
                av.value = flds[attIndex[attName]]
                if not attExists[ind]:
                    db.add(av)
            ln = 3
            line = f.readline()
        ln = 4
        db.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        #return {'error':"DB error adding attributeValue ({0})".format(e.orig.args)}
        return {'error':"DB error adding attributeValue ({0})".format(ln)}
    return None

