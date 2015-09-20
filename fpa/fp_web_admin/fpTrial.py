# trial.py
# Michael Kirk 2013
#
# Code for creation of new trials
# Note we want to remove direct use of sqlalchemy in here, it should all
# be in models.py
#


import sys, os, traceback
import sqlalchemy
import fp_common.models as models
import csv
import StringIO

#
# Special column headers.
# If present in the uploaded trial file, these become column headers
# indicate node members rather than generic attributes:
#
ATR_DES = 'description'
ATR_BAR = 'barcode'
ATR_LAT = 'latitude'
ATR_LON = 'longitude'

class Result:
    def __init__(self, status, msg, obj):
        self.status = status
        self.msg = msg
        self.obj = obj
    def good(self):
        return self.status
    def msg(self):
        return self.msg
    def obj(self):
        return self.obj


# def _getCsvLineAsArray(fobj):
#     line = fobj.readline().strip();
#     try:
#         line.decode('ascii')
#     except UnicodeDecodeError:
#         return {'error':"Non ascii characters found in file. Please contact FieldPrime support"}
#     sline = StringIO.StringIO(line)
#     return csv.reader(sline).next()

def _getCsvLineAsArray(fobj):
# Returns boolean (ascii error occurred), line, array
    line = fobj.readline().strip();
    if not line:
        return False, None, None
    try:
        line.decode('ascii')
    except UnicodeDecodeError:
        return True, line, None

    sline = StringIO.StringIO(line)
    return False, line, csv.reader(sline).next()


def _parseNodeCSV(fobj, ind1name, ind2name):
#-----------------------------------------------------------------------
# Parses the file to check valid trial input. Also determines the
# number of fields, and the column index of each fixed and attribute columns.
# Returns dictionary, with either an 'error' key, or the above fields.
#
    FIXED_ATTRIBUTES = [ind1name.lower(), ind2name.lower(), ATR_DES, ATR_BAR, ATR_LAT, ATR_LON]

    # Get headers,
    (asciiError, line, hdrs) = _getCsvLineAsArray(fobj)
    if asciiError:
        return {'error':"Non ascii characters found in file. Please contact FieldPrime support"}
    if not hdrs:
        return {'error':"No header line in file"}

#     hdrLine = fobj.readline().strip()
#     try:
#         hdrLine.decode('ascii')
#     except UnicodeDecodeError:
#         return {'error':"Non ascii characters found in file. Please contact FieldPrime support"}
#     hdrs = hdrLine.split(',')

    numFields = 0
    fixIndex = {}
    attIndex = {}
    for hd in hdrs:
        hdl = hd.strip().lower()
        if not hdl:
            return {'error':"Error - Empty header found for column {0}, aborting.".format(numFields + 1)}
        if len(hdl) > 127:
             return {'error':"Error - column header too long {0} for column {1}, aborting.".format(hdl, numFields + 1)}
        if hdl in FIXED_ATTRIBUTES:
            fixIndex[hdl] = numFields
        elif hdl in attIndex.keys():
            return {'error':"Error - Duplicate attribute name ({0}), aborting.".format(hd)}
        else:
            attIndex[hdl] = numFields
        numFields += 1

    # Check both row and column are present:
    for mand in [ind1name, ind2name]:
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

    # Check node lines:
    #line = fobj.readline()
    rowNum = 2
    rowColSet = set()
    while True:
        (asciiError, line, flds) = _getCsvLineAsArray(fobj)
        if asciiError:
            return {'error':"Non ascii characters found in file (line {0}). Please contact FieldPrime support".format(rowNum)}
        if not flds:
            break

#         try:
#             line.decode('ascii')
#         except UnicodeDecodeError:
#             return {'error':"Non ascii characters found in file (line {0}). Please contact FieldPrime support".format(rowNum)}
#         flds = line.strip().split(',')


        if not len(flds) == numFields:
            err =  "Error - wrong number of fields ({0}, should be {1}), line {2}, aborting. <br>".format(len(flds), numFields, rowNum)
            err += "Bad line was: " + line
            return {'error':err}
        srow = flds[fixIndex[ind1name]]
        scol = flds[fixIndex[ind2name]]
        if not (srow.isdigit() and scol.isdigit()):
            return {'error':"Error - row or col field is not integer, line {0}, aborting".format(rowNum)}

        # check for duplicates:
        nrow = int(srow)
        ncol = int(scol)
        if (nrow, ncol) in rowColSet:
            return {'error':"Error - duplicate row/column pair, line {0}, aborting".format(rowNum)}
        rowColSet.add((nrow, ncol))

        rowNum += 1
        #line = fobj.readline()

    # All good
    return {'numFields':numFields, 'fixIndex':fixIndex, 'attIndex':attIndex}



def uploadTrialFile(sess, f, tname, tsite, tyear, tacro, i1name, i2name):
#-----------------------------------------------------------------------
# Handle submitted create trial form.
# Return Trial object, None on success, else None, string error message.
#
    dbc = sess.db()
    try:
        ntrial = sess.getProject().newTrial(tname, tsite, tyear, tacro)
        # NB index names for the trial are set by the caller of this func.
    except models.DalError as e:
        return (None, e.__str__())

    # Add trial details from csv:
    res = updateTrialFile(sess, f, ntrial, i1name, i2name)
    if res is not None and 'error' in res:
        models.Trial.delete(dbc, ntrial.id)   # delete the new trial if some error
        return (None, res['error'])
    return ntrial, None


def updateTrialFile(sess, trialCsv, trl, i1name=None, i2name=None):
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
    # Get index names if not supplied:
    if i1name is None:
        i1name = trl.navIndexName(0).lower()
    if i2name is None:
        i2name = trl.navIndexName(1).lower()
    # Convert to lower case here - this means user needs to know (and can rely on) this is case insensitive.
    i1name = i1name.lower()
    i2name = i2name.lower()

    # Check csv file:
    tuFileInfo = _parseNodeCSV(trialCsv, i1name, i2name)
    if 'error' in tuFileInfo:
        return tuFileInfo
    fixIndex = tuFileInfo['fixIndex']
    attIndex = tuFileInfo['attIndex']

    dbSess = sess.db()
    # Add (new) node attributes, create/fill attExists, nodeAtts:
    try:
        currAtts = trl.nodeAttributes
        nodeAtts = []
        attExists = []    # array of booleans indicating whether corresponding attIndex attribute exists already
        for attName in attIndex.keys():
            # Does this attribute already exist?
            nodeAtt = None
            for cat in currAtts:
                if cat.name.upper() == attName.upper():
                    nodeAtt = cat
                    break
            attExists.append(nodeAtt is not None)
            if nodeAtt is None:
                nodeAtt = models.NodeAttribute(attName, trl.id)
                dbSess.add(nodeAtt)
            nodeAtts.append(nodeAtt)
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"DB error adding nodeAttribute ({0})".format(e.orig.args)}

    # Iterate thru the nodes (each line is assumed to be a node), creating or updating as necessary:
    try:
        trialCsv.seek(0,0)
        trialCsv.readline() # skip headers
        line = trialCsv.readline()
        while line:
            flds = line.strip().split(',')
            # Get or create the node (specified by row/col):
            # MFK if duplicate row col?
            node = trl.addOrGetNode(flds[fixIndex[i1name]], flds[fixIndex[i2name]])
            if node is None:
                out = "Problem getting or creating node: row" + str(flds[fixIndex[i1name]]) + " col " + str(flds[fixIndex[i2name]])
                return {'error':out}

            # Update fixed node attributes in the node struct:
            if ATR_BAR in fixIndex.keys(): node.barcode = flds[fixIndex[ATR_BAR]]
            if ATR_DES in fixIndex.keys(): node.description = flds[fixIndex[ATR_DES]]
            if ATR_LAT in fixIndex.keys(): node.latitude = flds[fixIndex[ATR_LAT]]
            if ATR_LON in fixIndex.keys(): node.longitude = flds[fixIndex[ATR_LON]]

            # add attributes:
            for ind, attName in enumerate(attIndex.keys()):
                errMsg = 'Error adding {1} attribute {0}:'.format(attName, 'existing' if str(attExists[ind]) else 'new')
                nodeAtt = nodeAtts[ind]
                newValue = flds[attIndex[attName]].strip() # get value minus surrounding whitespace

                # Get existing attributeValue if it exists.
                # If it does and newValue is empty then delete it.
                av = node.getAttributeValue(nodeAtt.id)
                if av is not None and not newValue:
                    # If there is existing record, but new value is empty, then delete existing record:
                    dbSess.delete(av)
                    continue

                if not newValue:  # don't add empty value
                    continue

                # Create new attributeValue if necessary:
                if av is None:
                    # Set up new attribute value:
                    av = models.AttributeValue()
                    av.nodeAttribute = nodeAtt
                    av.node = node
                    dbSess.add(av)

                av.setValueWithTypeUpdate(newValue)  # set the value

            line = trialCsv.readline()
        dbSess.commit()
    except sqlalchemy.exc.SQLAlchemyError as e:
        return {'error':"DB error adding attributeValue ({0})".format(e.orig.args)}
    return None


def _parseScoresCSV(fobj, trl, ind1name, ind2name):
#-----------------------------------------------------------------------
# Parses the file to check valid trial input. Also determines the
# number of fields, and the column index of each fixed and attribute columns.
# Expected file format is header line then one line per node.
# Columns must first be attribute names (including fixed attributes), and
# then trait names, optionally followed by metadata.
# {Att Names} { <traitname> (<traitname>_user | <traitname>_time | <traitname>_latitude | <traitname>_longitude)*}
# Returns dictionary, with either an 'error' key, or the above fields.
#
    FIXED_ATTRIBUTES = [ind1name.lower(), ind2name.lower(), ATR_BAR]

    #
    # Process headers:
    #
    (asciiError, line, hdrs) = _getCsvLineAsArray(fobj)
    if asciiError:
        return {'error':"Non ascii characters found in file. Please remove or contact FieldPrime support"}
    if not hdrs:
        return {'error':"No header line in file"}

    scoreSets = []  # each item should be a dictionary trait:trait value:valueCol, user:userCol..
    idColNames = []
    idColIndex = []
    stateIndexes = True # mandate that indexs must be row/col, barcode, or single attribute.
    currTraitName = None
    for ind in range(len(hdrs)):
        hdr = hdrs[ind].lower()
        if stateIndexes:
            if trl.hasNodeProperty(hdr):
                idColNames.append(hdr)
                idColIndex.append(ind)
                continue
#             att = trl.getAttribute(hdr)  # we need to allow index names and barcode here
#             if att is not None:
#                 stateIndexes.append(att)
#                 idColNames.append(hdr)
#                 idColIndex.append(ind)
#                 continue
#             elif hdr in FIXED_ATTRIBUTES:
#                 idColNames.append(hdr)
#                 idColIndex.append(ind)
#                 continue  # wait and see what we need to do with these things, then maybe make return nodeProperty from trial, duck typ

        stateIndexes = False
        if currTraitName is None:
            ssDetails = {}
            trt = trl.getTrait(hdr)
            if trt is None:
                return {'error':"Expected trait name as header in column {0}".format(ind+1)}
            currTraitName = hdr
            ssDetails['trait'] = hdr
            ssDetails['valueCol'] = ind
            # Look ahead for metadata, up to 4 fields.
            numMetadataCol = 0
            for j in range(ind+1, min(ind+5, len(hdrs)-ind)):
                for mdfield in ('time', 'user', 'latitude', 'longitude'):
                    if hdrs[j] == currTraitName + '_' + mdfield:  # case insensitive?
                        numMetadataCol += 1
                        ssDetails[mdfield] = j
                        continue
            ind += numMetadataCol

        scoreSets.append(ssDetails)


            # check hdr is an attribute name, or ind1, ind2, or barcode

#     hdrLine = fobj.readline().strip()
#     try:
#         hdrLine.decode('ascii')
#     except UnicodeDecodeError:
#         return {'error':"Non ascii characters found in file. Please contact FieldPrime support"}
#     hdrs = hdrLine.split(',')

    numFields = 0
    fixIndex = {}
    attIndex = {}
    for hd in hdrs:
        hdl = hd.strip().lower()
        if not hdl:
            return {'error':"Error - Empty header found for column {0}, aborting.".format(numFields + 1)}
        if len(hdl) > 127:
             return {'error':"Error - column header too long {0} for column {1}, aborting.".format(hdl, numFields + 1)}
        if hdl in FIXED_ATTRIBUTES:
            fixIndex[hdl] = numFields
        elif hdl in attIndex.keys():
            return {'error':"Error - Duplicate attribute name ({0}), aborting.".format(hd)}
        else:
            attIndex[hdl] = numFields
        numFields += 1

    # Check both row and column are present:
    for mand in [ind1name, ind2name]:
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

    # Check node lines:
    #line = fobj.readline()
    rowNum = 2
    rowColSet = set()
    while True:
        (asciiError, line, flds) = _getCsvLineAsArray(fobj)
        if asciiError:
            return {'error':"Non ascii characters found in file (line {0}). Please contact FieldPrime support".format(rowNum)}
        if not flds:
            break

#         try:
#             line.decode('ascii')
#         except UnicodeDecodeError:
#             return {'error':"Non ascii characters found in file (line {0}). Please contact FieldPrime support".format(rowNum)}
#         flds = line.strip().split(',')


        if not len(flds) == numFields:
            err =  "Error - wrong number of fields ({0}, should be {1}), line {2}, aborting. <br>".format(len(flds), numFields, rowNum)
            err += "Bad line was: " + line
            return {'error':err}
        srow = flds[fixIndex[ind1name]]
        scol = flds[fixIndex[ind2name]]
        if not (srow.isdigit() and scol.isdigit()):
            return {'error':"Error - row or col field is not integer, line {0}, aborting".format(rowNum)}

        # check for duplicates:
        nrow = int(srow)
        ncol = int(scol)
        if (nrow, ncol) in rowColSet:
            return {'error':"Error - duplicate row/column pair, line {0}, aborting".format(rowNum)}
        rowColSet.add((nrow, ncol))

        rowNum += 1
        #line = fobj.readline()

    # All good
    return {'numFields':numFields, 'fixIndex':fixIndex, 'attIndex':attIndex}


def uploadScores(sess, trialCsv, trl, i1name=None, i2name=None):
    # We may load all the file's data into memory, so should put a size limit
    # in here. A few mb?
    _parseScoresCSV(trialCsv, trl, i1name, i2name)
    return {'error':"Software engineer underpaid"}

