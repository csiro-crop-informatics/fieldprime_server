from rest_framework import serializers
from fpapi import models as fpmodels
from fpapi import const as fpconst

import logging
logger = logging.getLogger(__name__)

class TrialSerializer(serializers.HyperlinkedModelSerializer):

    #traits = serializers.SerializerMethodField('get_alternate_name')
    #nodes = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Node.objects.all())
    
    nodes = serializers.HyperlinkedRelatedField(
        view_name='node-detail-id',
        lookup_field='barcode',
        many=True,
        read_only=True
    )
    
    _traits = serializers.HyperlinkedRelatedField(
        view_name='trait-detail-uuid',
        lookup_field='uuid',
        many=True,
        read_only=True
    )
    
    
    class Meta:
        model = fpmodels.Trial
        fields = ("url", "name", "site", "year", "acronym", "uuid", "project", "nodes", "_traits")
        extra_kwargs = {
            'url': {'view_name': 'trial-detail-uuid', 'lookup_field': 'uuid'}
        }


"""

"""