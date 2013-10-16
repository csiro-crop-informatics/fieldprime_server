# trial.py
# Michael Kirk 2013
#
# Code for creation of new trials
#


import sys, os
import sqlalchemy
from flask import render_template
import fp_common.fpUtil as fpUtil
from fp_common.models import Trial, TrialUnit, TrialUnitAttribute, AttributeValue, Trait

ROW = 'row'
COL = 'column'
DES = 'description'
BAR = 'barcode'


def ParseTrialUnitCSV(f):
#-----------------------------------------------------------------------
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
# Handle submitted create trial form:
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


def NewTrial(sess):
#-----------------------------------------------------------------------
# Show form to create new trial:
#
    return render_template('newTrial.html', title='Create Trial')


def CreateTrial(sess, uploadFile, form):
#-----------------------------------------------------------------------
# Handle submitted create trial form:
# If error, returns Result, otherwise returns None
#
    res = UploadTrialFile(sess, uploadFile, form.get('name'), form.get('site'), 
                          form.get('year'), form.get('acronym'))
    if res is not None and 'error' in res:
        return render_template('newTrial.html', title='Create Trial', msg = res['error'])
    else:
        return None

