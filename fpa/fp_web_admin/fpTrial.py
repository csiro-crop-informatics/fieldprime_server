# trial.py
# Michael Kirk 2013
#
# Code for creation of new trials
# Note we want to remove direct use of sqlalchemy in here, it should all
# be in models.py
#


import sys, os, traceback, datetime
import sqlalchemy
import fp_common.models as models
import csv
import StringIO
import simplejson as json
import time
from fp_common.const import T_DECIMAL, TRAIT_TYPE_NAMES


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


def _getCsvLineAsArray(fobj):
# fobj should be a file object.
# Returns tuple of errmsg, (None if no error), line (stripped of whitespace),
# array of values (None if line is empty or whitespace only).
#
    line = fobj.readline().strip();
    if not line:
        return None, None, None
    try:
        line.decode('ascii')
    except UnicodeDecodeError:
        return "Non ascii characters found in file", line, None

    sline = StringIO.StringIO(line)
    try:
        ar = csv.reader(sline).next()
    except csv.Error, e:
        #try:
        #   ar = csv.reader(StringIO.StringIO('n'.join(line.splitlines()))).next()
        #except Exception, e:
            #return str(e), line, None
            return 'CSV file problem, note Mac files need to be converted to unix line endings', line, None
    return None, line, ar


def _parseNodeCSV(fobj, ind1name, ind2name):
#-----------------------------------------------------------------------
# Parses the file to check valid trial input. Also determines the
# number of fields, and the column index of each fixed and attribute columns.
# Returns dictionary, with either an 'error' key, or the above fields.
#
    FIXED_ATTRIBUTES = [ind1name.lower(), ind2name.lower(), ATR_DES, ATR_BAR, ATR_LAT, ATR_LON]

    # NB - _getCsvLineAsArray fails on mac line ending files. Here are 2 potential ways
    # around this, but you would also need to fix the other readlines below.
    #s = StringIO.StringIO(x, fobj.read().replace('\r\n', '\n').replace('\r','\n'))
    #x = '\n'.join(fobj.read().splitlines())
    #fobj = StringIO.StringIO(x)

    # Get headers,
    (errmsg, line, hdrs) = _getCsvLineAsArray(fobj)
    if errmsg:
        return {'error':errmsg}
    if not hdrs:
        return {'error':"No header line in file"}

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
    rowNum = 2
    rowColSet = set()
    while True:
        (errmsg, line, flds) = _getCsvLineAsArray(fobj)
        if errmsg:
            return {'error': errmsg + " (line {0}). Please contact FieldPrime support".format(rowNum)}
        if not flds:
            break

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

    # All good
    return {'numFields':numFields, 'fixIndex':fixIndex, 'attIndex':attIndex}


def uploadTrialFile(sess, uploadFile, tname, tsite, tyear, tacro, i1name, i2name):
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
    res = updateTrialFile(sess, uploadFile, ntrial, i1name, i2name)
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
        currAtts = trl.getAttributes()
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
            # NB - _parseNodeCSV() checked that there were no duplicate row/cols
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

def errDict(errmsg):
# Returns dictionary with single key value pair 'error':errmsg
    return {'error':errmsg}

def csvErr(errmsg):
    return errDict('Invalid input: ' + errmsg)

def _parseScoresCSV(fobj, trl, ind1name, ind2name):
#-----------------------------------------------------------------------
# Parses the file to check valid format.
# Makes list of scoresets within the file, see comment below for structure of this list.
# number of fields, and the column index of each fixed and attribute columns.
# Expected file format is header line then one line per node.
# Columns must first be attribute names (including fixed attributes), and
# then trait names, optionally followed by metadata.
# {Att Names} { <traitname> (<traitname>:user | <traitname>:time | <traitname>:latitude | <traitname>:longitude)*}
# Returns dictionary, with either an 'error' key, or the scoreset list with key 'scoreSets'.
#
    #
    # Process headers:
    #
    (errmsg, line, hdrs) = _getCsvLineAsArray(fobj)
    if errmsg:
        return csvErr(errmsg)
    if not hdrs:
        return csvErr("No header line in file")
    #
    # First 1 or 2 columns must identify the nodes, there are 3 options:
    # . The first 2 columns are the row and column (with whatever user names for these are set)
    # . single 'barcode' column
    # . single non-fixed attribute name.
    # Work out which of these is in play:
    nodeIdOption = 0
    firstDataCol = 1
    numFields = len(hdrs)
    if numFields < 2: # Check we have at least 2 columns
        return csvErr('Too few columns in file')
    h0, h1 = hdrs[0].strip().lower(), hdrs[1].strip().lower()
    if h0 == 'barcode':
        nodeIdOption = 1
    elif h0 == ind1name.lower() and h1 == ind2name.lower():
        nodeIdOption = 2
        firstDataCol = 2
    else:
        idAttr = trl.getAttribute(h0)
        if idAttr is not None:
            nodeIdOption = 3
        else:
            return csvErr('First 1 or 2 columns must identify node.' + '{0} {1}'.format(h0, h1))
    #
    # Process rest of headers. Make list, one item for each scoreset. Each item should be a dictionary:
    # {trait:traitObject, value:colIndex, user:colIndex, latitude:colIndex, longitude:colIndex}
    #
    scoreSets = []
    currScoreSet = None
    currTraitName = None
    ind = firstDataCol - 1
    while ind + 1 < len(hdrs):
        ind += 1  # python doesn't have good old fashioned for loops
        hdr = hdrs[ind].strip()  #.lower()
        #
        # Parse column header from scores upload file, and check stuff:
        #
        tokes = hdr.split(':')
        if len(tokes) == 1: # Value field, start new scoreSet dict
            trt = trl.getTrait(hdr)
            if trt is None:
                return csvErr("Expected trait name as header in column {0}".format(ind+1))
            currTraitName = hdr
            currScoreSet = {'data':[], 'trait':trt, 'value':ind}
            scoreSets.append(currScoreSet)
            continue
        if len(tokes) != 2 or tokes[1] not in ('time', 'user', 'latitude', 'longitude'): # Bad header
            return csvErr('Invalid column header ({0})'.format(hdr))
        trtName, mdType = tokes  # Get the trait name and metadata kind
        if trtName != currTraitName:   # Disallow metadata column without preceding trait value column
            return csvErr('Metadata header ({0}) for trait without preceding trait column'.format(hdr))
        if currScoreSet.has_key(mdType): # Disallow multiple columns for same metadata kind
            return csvErr('Multiple {0} columns for trait {1}'.format(mdType, currTraitName))
        # All good
        currScoreSet[mdType] = ind
    #
    # Iterate over data rows, checking stuff and getting nodeIds and data:
    # Maybe a bit of code overlap with _parseNodeCSV()
    # May need to detect end of file properly - currently treats empty line as eof.
    #
    rowNum = 2
    nodeIdSet = set()
    while True:
        (errmsg, line, flds) = _getCsvLineAsArray(fobj)
        if errmsg:
            return csvErr(errmsg + " (line {0}). Please contact FieldPrime support".format(rowNum))
        if not flds:
            break
        if not len(flds) == numFields:
            err =  "wrong number of fields ({0}, should be {1}), line {2}.".format(len(flds), numFields, rowNum)
            return csvErr(err)

        # get and store nodeId - but can these be deleted in the meantime? no worse than current upload from app I guess..
        if nodeIdOption == 1:
            fpNodeId = trl.getNodeIdFromBarcode(flds[0])
        elif nodeIdOption == 2:
            srow = flds[0].strip()
            scol = flds[1].strip()
            if not (srow.isdigit() and scol.isdigit()):
                return csvErr("{0} or {1} field is not integer, line {2}".format(ind1name, ind2name, rowNum))
            fpNodeId = trl.getNodeId(srow, scol)
        else:
            fpNodeId = idAttr.getUniqueNodeIdFromValue(flds[0])

        if fpNodeId is None:
            if nodeIdOption == 1:
                optionSpecificErr = 'using barcode "{0}"'.format(flds[0])
            elif nodeIdOption == 2:
                optionSpecificErr = 'using {0} "{1}" and {2} "{3}"'.format(ind1name, flds[0], ind2name, flds[1])
            else:
                optionSpecificErr = 'using {0} "{1}"'.format(hdrs[0], flds[0])
            return csvErr('Cannot determine node id for line {0}, {1}'.format(rowNum, optionSpecificErr))

        # check for duplicates:
        if fpNodeId in nodeIdSet:
            return csvErr("Multiple lines identifying same node, line {0}, aborting".format(rowNum))
        nodeIdSet.add(fpNodeId)

        #
        # Get the data:
        #
        # NB For values we need to consider the following cases:
        # . empty or whitespace - no error, no value
        # . NA - NA value
        # . Valid value
        # . anything else - error
        #
        # Note the processing of the metadata options, and even the value, have a lot in common,
        # there is probably a more elegant way..
        for ss in scoreSets:
            valueField = flds[ss['value']].strip()    # NB remove surrounding whitespace.
            if len(valueField) == 0:  # If no value, then assume no score intended, metadata ignored
                continue
            newy = {'node_id':fpNodeId}
            if valueField != 'NA':   # NA means NA. If it is NA, then no value key is added, this means NA in the db load func.
                trt = ss['trait']
                val = trt.valueFromString(valueField)
                if val is None:
                    return csvErr('Cannot convert value ({0}) to {1} at line {2}'.format(
                                valueField, trt.getDatatypeName(), rowNum))
                newy['value'] = val
            if 'time' in ss:
                timeField = flds[ss['time']].strip()   # should we strip all fields in one go somehow above?
                if len(timeField) == 0:
                    newy['timestamp'] = None
                else:
                    if not timeField.isdigit():
                        try:
                            pattern = '%m/%d/%Y'
                            epoch = int(time.mktime(time.strptime(timeField, pattern)))
                            newy['timestamp'] = epoch
                        except ValueError:
                            return csvErr('Invalid time field line {0}'.format(rowNum))
                    else:
                        newy['timestamp'] = timeField
            if 'user' in ss:
                userField = flds[ss['user']].strip()   # should we strip all fields in one go somehow above?
                if len(userField) == 0:
                    newy['userid'] = None
                else:
                    newy['userid'] = userField
            if 'latitude' in ss:
                field = flds[ss['latitude']].strip()   # should we strip all fields in one go somehow above?
                if len(field) == 0:
                    newy['gps_lat'] = None
                else:
                    val = models.valueFromString(T_DECIMAL, field)
                    if val is None:
                        return csvErr('Cannot convert latitude value ({0}) to {1} at line {2}'.format(
                                field, TRAIT_TYPE_NAMES[T_DECIMAL], rowNum))
                    newy['gps_lat'] = val
            if 'longitude' in ss:
                field = flds[ss['longitude']].strip()   # should we strip all fields in one go somehow above?
                if len(field) == 0:
                    newy['gps_long'] = None
                else:
                    val = models.valueFromString(T_DECIMAL, field)
                    if val is None:
                        return csvErr('Cannot convert longitude value ({0}) to {1} at line {2}'.format(
                                field, TRAIT_TYPE_NAMES[T_DECIMAL], rowNum))
                    newy['gps_long'] = val
            ss['data'].append(newy)
        rowNum += 1
    # All good:
    return {'scoreSets':scoreSets}


def uploadScores(sess, scoresCsv, trl, i1name=None, i2name=None):
#-----------------------------------------------------------------------
# Update trial data according to csv file scoresCsv.
#
    # Get index names if not supplied:
    if i1name is None:
        i1name = trl.navIndexName(0).lower()
    if i2name is None:
        i2name = trl.navIndexName(1).lower()

    # We may load all the file's data into memory, so should put a size limit in here. A few mb?
    info = _parseScoresCSV(scoresCsv, trl, i1name, i2name)
        # Check csv file:
    if 'error' in info:
        return info
    scoreSets = info['scoreSets']
    # get or create dummy token representing data uploaded via this function
    token = models.Token.getOrCreateToken(sess.db(), "web upload", trl.getId())
    now = datetime.datetime.now()
    fpDate = now.year * 10000 + now.month * 100 + now.day
    for ss in scoreSets:
        trt = ss['trait']
        trlTrait = models.getTrialTrait(sess.db(), trl.getId(), trt.getId())   # trait existence checked in parse
        newti = trlTrait.addTraitInstance(fpDate, token.getId())
        newti.addData(ss['data'])
    return None

