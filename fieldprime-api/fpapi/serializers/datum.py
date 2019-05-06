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

    node_uuid = serializers.SerializerMethodField()
    trait_uuid = serializers.SerializerMethodField()

    class Meta:
        model = fpmodels.Datum
        fields = ("node_uuid", "trait_uuid", "timestamp", "user_id", "num_value", "txt_value", "notes")

    def get_node_uuid(self, obj):
        return obj.get_node_uuid

    def get_trait_uuid(self, obj):
        return obj.get_trait_uuid