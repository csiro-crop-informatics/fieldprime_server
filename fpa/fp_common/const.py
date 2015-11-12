#
# const.py
# Michael Kirk 2013
#
# Constants (eg database table and field names).
#

###  Constants:  ##################################################################################################

# Values for trait sysType field:
SYSTYPE_TRIAL = 0
SYSTYPE_SYSTEM = 1
SYSTYPE_ADHOC = 2

# Login stuff:
LOGIN_TIMEOUT = 900          # Idle time before requiring web user to login again
LOGIN_TYPE_SYSTEM = 1
LOGIN_TYPE_***REMOVED*** = 2

# Names and values for trait datatype field:
T_INTEGER = 0
T_DECIMAL = 1
T_STRING = 2
T_CATEGORICAL = 3
T_DATE = 4
T_PHOTO = 5
T_LOCATION = 6
TRAIT_TYPE_NAMES = ["Integer", "Decimal", "Text", "Categorical", "Date", "Photo"]
TRAIT_TYPE_TYPE_IDS = {"Integer":0, "Decimal":1, "Text":2, "Categorical":3, "Date":4, "Photo":5}


# Table nodeAttribute:
TABLE_TUA = "nodeAttribute"
TUA_ID = "id"
TUA_TRIAL_ID = "trial_id"
TUA_NAME = "name"
TUA_DATATYPE = "datatype"
TUA_FUNC = "func"


# Table attributeValue:
TABLE_ATTRIBUTE_VALUES = "attributeValue"
AV_TUA_ID = "nodeAttribute_id"
AV_TRIAL_UNIT = "node_id"
AV_VALUE = "value"

TI_SEQNUM = "seqNum"
TI_SAMPNUM = "sampleNum"
TI_DAYCREATED = "dayCreated"
DM_TIMESTAMP = "timestamp"
DM_USERID = "userid"
DM_GPS_LAT = "gps_lat"
DM_GPS_LONG = "gps_long"
DM_NODE_ID = "node_id"
DM_NODE_ID_CLIENT_VERSION = "node_id"
DM_NODE_ID_SERVER_VERSION = "trialUnit_id"
DM_TRAITINSTANCE_ID = "traitInstance_id"

#
# JSON names:
# Having the values here will allow firstly the ability to change a json name for all references
# in a single place, and secondly a single place (here) to find json names (rather than scattered
# through the code.
#
# NOTE they are not all here yet (just the one I was bitten by!)

JTRL_TRIAL_PROPERTIES = 'trialProperties'

JTRL_NODES_ARRAY = 'nodes'

# Trial Uploads:
jTrialUpload = {'serverToken':'serverToken',
                'notes':'notes'
                }

# Notes:
jNotesUpload = {
    'node_id':'node_id',
    'timestamp':'timestamp',
    'userid':'userid',
    'note':'note'
}

# Data upload:
jDataUpload = {
    'node_id':'node_id',
    'timestamp':'timestamp',
    'userid':'userid',
    'gps_long':'gps_long',
    'gps_lat':'gps_lat',
    'value':'value'
}


# Trial Property keys:
INDEX_NAME_1 = 'indexName1'
INDEX_NAME_2 = 'indexName2'

