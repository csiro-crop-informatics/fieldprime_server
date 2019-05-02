from rest_framework import serializers
from fpapi import models as fpmodels
from fpapi import const as fpconst

import logging
logger = logging.getLogger(__name__)


class DatumSerializer(serializers.ModelSerializer):
    """
    Fields from model
        timestamp
        notes
        num_value
        txt_value
        user_id
        node (FK)
    Other Required fields
        trait_uuid
    """

    trait = serializers.SerializerMethodField('get_alternate_name')

    class Meta:
        model = fpmodels.Datum
        fields = ("node_id", "trait", "timestamp", "user_id", "num_value", "txt_value", "notes")

    def get_alternate_name(self, obj):
        return obj.get_trait_id
