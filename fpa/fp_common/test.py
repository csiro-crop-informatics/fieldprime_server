import models as md
import os.path
import sys

def photoCheck(dbc, photodir):
    trials = md.getTrialList(dbc)
    for tr in trials:
        tis = tr.getTraitInstances()
        for ti in tis:
            if ti.trait.type == 5:
                # print ti.trait.caption + ' type: ' + str(ti.trait.type)
                data = ti.getData()
                for dat in data:
                    tval = dat.txtValue
                    if tval.count('_') < 2 or tval.count('/') != 0:
                        fname = md.photoFileName(project,
                                         ti.trial_id,
                                         ti.trait_id,
                                         dat.node.id,
                                         ti.token.tokenString(),
                                         ti.seqNum,
                                         ti.sampleNum)
                        # Check if file exists:
                        fullPath = photodir + '/' + fname
                        print '{0} -> {1}: {2}'.format(tval, fullPath, 'Exists' if os.path.isfile(fullPath) else 'Missing')
                    else:
                        # File is named, check file exists:
                        fullPath = photodir + '/' + tval
                        if not os.path.isfile(fullPath):
                            print 'Named file Missing {0}'.format(fullPath)


### Main: ###################################################
if len(sys.argv) > 1:
    project = sys.argv[1]
else:
    project = 'mk'
if len(sys.argv) > 2:
    photodir = sys.argv[2]
else:
    '/proj/fpserver/photos/'
dbc = md.getSysUserEngine(project)
photoCheck(dbc, photodir)



