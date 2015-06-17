#!/usr/bin/python


import fileinput
import sys, getopt, re
import csv
import StringIO

class Result:
    def __init__(self, status, msg, obj):
        self._status = status
        self._msg = msg
        self._obj = obj
    def good(self):
        return self._status
    def msg(self):
        return self._msg
    def obj(self):
        return self._obj

def _getCsvLineAsArray(fobj):
# Returns False for no data, or Result()
    line = fobj.readline().strip();
    if not line:
        return False
        #return Result(True, None, None)
    try:
        line.decode('ascii')
    except UnicodeDecodeError:
        return Result(False, "Non ascii character found", line)

    sline = StringIO.StringIO(line)
    return Result(True, '%s\n' % line, csv.reader(sline).next())

def _NEW_getCsvLineAsArray(fobj):
# Returns False for no data, or Result()
    line = fobj.readline().strip();
    if not line:
        return False
        #return Result(True, None, None)
    try:
        line.decode('ascii')
    except UnicodeDecodeError:
        return Result(False, "Non ascii character found", line)



    sline = StringIO.StringIO(line)
    return Result(True, '%s\n' % line, csv.reader(sline).next())

def main(infile):
    switchCol = 'Entry Book Name'
    cutCols = []
    usage = "Usage:\n" + sys.argv[0] + ' -s<filterColumnHeader> -c<cutColumns>'
    try:
       opts, args = getopt.getopt(sys.argv[1:],"hs:c:",["switchColumn=","cutColumns="])
    except getopt.GetoptError:
       print usage
       return

    for opt, arg in opts:
        if opt == '-h':
            print usage
            return
        elif opt in ("-s", "--switchColumn"):
            switchCol = arg
        elif opt in ("-c", "--cutColumns"):
            # MFK check arg is digit comma or dash
            ranges = (x.split("-") for x in arg.split(","))
            cutCols = [i for r in ranges for i in range(int(r[0]), int(r[-1]) + 1)]

    res = _getCsvLineAsArray(infile)
    if not res.good():
        return "Error:" + res.msg()

    hline = res.msg()
    hlist = res.obj()
    try:
        sindex = hlist.index(switchCol)
    except ValueError:
        return 'Switch column header (%s) not found' % switchCol

    # We want cutCols to be an array of indicies with no dupes, descending order:
    #print cutCols
    cutCols.append(sindex+1)
    cutCols = list(set(cutCols))
    cutCols.sort(reverse=True)
    for idx, v in enumerate(cutCols):
        if v < 1 or v > len(hlist):
            return "Invalid cutColumns"
        cutCols[idx] -= 1
    #print cutCols
    #return
    lineNo = 2
    res = _getCsvLineAsArray(infile)
    indexVals = []
    while (res):
        if not res.good():
            return "Error:" + res.msg()
        fields = res.obj()
        index = fields[sindex]
        if not index:
            return "empty index value, line %d" %lineNo

        if index not in indexVals:
            indexVals.append(index)
        lineNo += 1
        res = _getCsvLineAsArray(infile)

    reg = re.compile('^[\sa-zA-Z0-9\.\(\)]+$') # No funny business please
    for fname in indexVals:
        if not reg.match(fname):
            return "Invalid switch value: x%sx" % fname

    # Make the files:
    def doCuts(arr):
        for dind in cutCols:
            del arr[dind]

    def joinStringLine(joinee):
        return '%s\n' % ','.join(joinee)

    doCuts(hlist)
    cutHline = joinStringLine(hlist)
    flist = []
    for fname in indexVals:
        fob = open('nx%s' % fname, "w")
        fob.write(cutHline)
        flist.append(fob)

    # Reset the input and do the switching:
    infile.seek(0)
    infile.readline() # skip headers
    lineNo = 2
    res = _getCsvLineAsArray(infile)
    while (res):
        if not res.good():
            return "Error:" + res.msg()
        fields = res.obj()
        sval = fields[sindex]
        index = indexVals.index(sval)
        doCuts(fields)
        for idx, f in enumerate(fields):
            if ',' in f:
                fields[idx] = '"%s"' % fields[idx]
        flist[index].write(joinStringLine(fields))
        lineNo += 1
        res = _getCsvLineAsArray(infile)

    # Close files?


#     for x in hlist:
#         print x
#     print hline

    # Run through to get all distinct values of split column.


# for line in fileinput.input():
#     process(line)

msg = main(sys.stdin)
if msg:
    print msg
