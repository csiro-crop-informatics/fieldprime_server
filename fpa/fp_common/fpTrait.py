#
# fpTrait.py
# Michael Kirk 2013
#

from fpUtil import *
from fpUtil import ShowHtml
from models import *
from dbUtil import GetTrialFromDBsess
import dbUtil


#-- CONSTANTS: ---------------------------------------------------------------------

# Trait type values:
TRAIT_NONE = -1
TRAIT_INTEGER = 0
TRAIT_DECIMAL = 1
TRAIT_STRING = 2
TRAIT_CATEGORICAL = 3
TRAIT_DATE = 4
TRAIT_PHOTO = 5

TRAIT_TYPE_NAMES = ["Integer", "Decimal", "Text", "Categorical", "Date", "Photo"]
TRAIT_TYPE_TYPE_IDS = {"Integer":0, "Decimal":1, "Text":2, "Categorical":3, "Date":4, "Photo":5}

SYSTYPE_TRIAL = 0
SYSTYPE_SYSTEM = 1;
SYSTYPE_ADHOC = 2;


#-- FUNCTIONS: ---------------------------------------------------------------------

def TraitListHtmlTable(traitList):
#-----------------------------------------------------------------------
# Returns html table of traitList
#
    if len(traitList) < 1:
        return "No traits configured"
    out = "<table border='1'>"
    out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format("Caption", "Description", "Type", "Min", "Max")
    for trt in traitList:
        out += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(
            trt.caption, trt.description, TRAIT_TYPE_NAMES[trt.type], trt.min, trt.max)
    out += "</table>"
    return out


def NewTraitForm(sess, form):
#-----------------------------------------------------------------------
    def newTrait():
        trialId = GetFormKey(form, "tid")
        out = """<h2>Create New Trait</h2><form enctype="multipart/form-data" action="{0}?op=createTrait&tid={1}" method="post">""".format(HOMEPAGE, trialId)
        out += """
Caption: <input type="text" name="caption">
<p>Description: <input type="text" name="description">
<p><div id="traitDiv">Trait Type: <select name='type' onchange="SetTraitFormElements('traitDiv',this.options[selectedIndex].value)">"""
        for typ in TRAIT_TYPE_NAMES:
            out += """<option value="{0}" name={1}>{1}</option>""".format(TRAIT_TYPE_TYPE_IDS[typ], typ)
        out += """
</select></div>
<p><input type="submit" value="Create Trait">
</form>
"""
        return out

    ShowHtml(sess, "New Trait", newTrait)


def CreateTrait(sess, form, successCall):
#-----------------------------------------------------------------------
    tid = GetFormKey(form, "tid")
    sysTrait = True if tid == "sys" else False
    caption = GetFormKey(form, "caption")
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.

    description = GetFormKey(form, "description")
    type = GetFormKey(form, "type")
    min = GetFormKey(form, "min")
    max = GetFormKey(form, "max")
    dbsess = sess.DB()

    ntrt = Trait()
    ntrt.caption = caption
    ntrt.description = description

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    if not sysTrait: # If local, check there's no other trait local to the trial with the same caption:
        trial = GetTrialFromDBsess(sess, tid)
        for x in trial.traits:
            if x.caption == caption:
                # NB SHOULD BE error message and stop
                successCall(sess, tid)
        ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        ntrt.sysType = SYSTYPE_TRIAL
    else:  # If system trait, check there's no other system trait with same caption:
        sysTraits = dbUtil.GetSysTraits(sess)
        for x in sysTraits:
            if x.caption == caption:
                # NB SHOULD BE error message and stop
                 FrontPage(sess)
        ntrt.sysType = SYSTYPE_SYSTEM

    ntrt.type = type
    if min:
        ntrt.min = min
    if max:
        ntrt.max = max
    dbsess.add(ntrt)
    dbsess.commit()
    # Finished, go somewhere:
    if sysTrait:
        FrontPage(sess)
    else:
        successCall(sess, tid)  # Or could this just be called on return (if we return)
 

def CreateTrait2(dbsess, caption, description, vtype, sysType, vmin, vmax):
#--------------------------------------------------------------------------
# Returns a list [ <new trait> | None, ErrorMessage | None ]
# NB doesn't add to trialTrait table
# Currently only written with adhoc traits in mind..
#
    # We need to check that caption is unique within the trial - for local anyway, or is this at the add to trialTrait stage?
    # For creation of a system trait, there is not an automatic adding to a trial, so the uniqueness-within-trial test
    # can wait til the adding stage.
    ntrt = Trait()
    ntrt.caption = caption
    ntrt.description = description
    ntrt.sysType = sysType

    # Check for duplicate captions, probably needs to use transactions or something, but this will usually work:
    # and add to trialTrait?
    if sysType == SYSTYPE_TRIAL: # If local, check there's no other trait local to the trial with the same caption:
        # trial = GetTrialFromDBsess(sess, tid)
        # for x in trial.traits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        # ntrt.trials = [trial]      # Add the trait to the trial (table trialTrait)
        pass
    elif sysType == SYSTYPE_SYSTEM:  # If system trait, check there's no other system trait with same caption:
        # sysTraits = dbUtil.GetSysTraits(sess)
        # for x in sysTraits:
        #     if x.caption == caption:
        #         return (None, "Duplicate caption")
        pass
    elif sysType == SYSTYPE_ADHOC:
        # Check no trait with same caption that's not an adhoc trait for another device
        # Do adhoc traits go into trialTrait?
        # Perhaps not at the moment, but perhaps they should be..
        pass
    else:
        return (None, "Invalid sysType")

    ntrt.type = vtype
    if vmin:
        ntrt.min = vmin
    if vmax:
        ntrt.max = vmax
    dbsess.add(ntrt)
    dbsess.commit()
    return ntrt, None
 
