# fpAppConfig.py
# Michael Kirk 2013
# 
# for use by flask: app.config.from_object()
#


# Flask config params:
MAX_CONTENT_LENGTH = 16 * 1024 * 1024             # Limit the size of file uploads

# Our app config params:
PHOTO_UPLOAD_FOLDER = '***REMOVED***/photos/'
DATA_ACCESS_MODULE = 'fp_common.models'      # Name of the py file providing the data access layer.

# DEBUG = True
