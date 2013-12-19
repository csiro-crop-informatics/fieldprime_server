#
# const.py
# Michael Kirk 2013
#
# Constants (eg database table and field names).
#

###  Constants:  ##################################################################################################

# Values for trait sysType field:
SYSTYPE_TRIAL = 0
SYSTYPE_SYSTEM = 1;
SYSTYPE_ADHOC = 2;

# Names and values for trait type field:
T_INTEGER = 0
T_DECIMAL = 1
T_STRING = 2
T_CATEGORICAL = 3
T_DATE = 4
T_PHOTO = 5
T_LOCATION = 6
TRAIT_TYPE_NAMES = ["Integer", "Decimal", "Text", "Categorical", "Date", "Photo"]
TRAIT_TYPE_TYPE_IDS = {"Integer":0, "Decimal":1, "Text":2, "Categorical":3, "Date":4, "Photo":5}


# Table trialUnitAttribute:
TABLE_TUA = "trialUnitAttribute"
TUA_ID = "id"
TUA_TRIAL_ID = "trial_id"
TUA_NAME = "name"
TUA_DATATYPE = "datatype"
TUA_FUNC = "func"


# Table attributeValue:
TABLE_ATTRIBUTE_VALUES = "attributeValue"
AV_TUA_ID = "trialUnitAttribute_id"
AV_TRIAL_UNIT = "trialUnit_id"
AV_VALUE = "value"
