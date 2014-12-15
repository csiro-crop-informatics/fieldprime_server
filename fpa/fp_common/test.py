import models as md
import os.path


def photoCheck(dbc):
    photodir = '/proj/fpserver/photos/'
    trials = md.GetTrialList(dbc)
    for tr in trials:
        tis = tr.getTraitInstances()
        for ti in tis:
            if ti.trait.type == 5:
                print ti.trait.caption + ' type: ' + str(ti.trait.type)
                data = ti.getData()
                for dat in data:
                    tval = dat.txtValue
                    if tval.count('_') < 2 or tval.count('/') != 0:
                        fname = md.photoFileName(username,
                                         ti.trial_id,
                                         ti.trait_id,
                                         dat.node.id,
                                         ti.token,
                                         ti.seqNum,
                                         ti.sampleNum)
                        # Check if file exists:
                        print tval + ' -> ' + fname
                        if os.path.isfile(fname):
                            print '  file exists'
                        else:
                            print '  file missing'

username = 'mk'
dbc = md.GetEngineForApp(username)
photoCheck(dbc)



