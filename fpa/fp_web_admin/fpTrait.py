#
# fpTrait.py
# Michael Kirk 2013
#

#from fpUtil import *
#from fp_common.models import *
from fp_common.models import SYSTYPE_TRIAL, SYSTYPE_SYSTEM, SYSTYPE_ADHOC, TRAIT_TYPE_NAMES, TRAIT_TYPE_TYPE_IDS


#-- CONSTANTS: ---------------------------------------------------------------------

# Trait type values:
TRAIT_NONE = -1
TRAIT_INTEGER = 0
TRAIT_DECIMAL = 1
TRAIT_STRING = 2
TRAIT_CATEGORICAL = 3
TRAIT_DATE = 4
TRAIT_PHOTO = 5


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



 
