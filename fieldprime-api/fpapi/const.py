from django.utils.translation import gettext as _
from model_utils import Choices


"""
"""
INTEGER = 0
DECIMAL = 1
STRING = 2
CATEGORICAL = 3
DATE = 4
PHOTO = 5
LOCATION = 6

DATA_TYPES = Choices(
    (INTEGER, "INTEGER", _("INTEGER")),
    (DECIMAL, "DECIMAL", _("DECIMAL")),
    (STRING, "STRING", _("STRING")),
    (CATEGORICAL, "CATEGORICAL", _("CATEGORICAL")),
    (DATE, "DATE",_("DATE")),
    (PHOTO, "PHOTO", _("PHOTO")),
    (LOCATION, "LOCATION", _("LOCATION")),
)