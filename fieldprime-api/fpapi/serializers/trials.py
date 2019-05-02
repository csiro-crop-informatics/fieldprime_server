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
    
    def get_alternate_name(self, obj):
        return obj._traits

"""
class TraitListSerializer(serializers.ModelSerializer):

    traits = TraitNestedSerializer(many=True, required=False)

    def create(self, validated_data):


        if "traits" in validated_data:
            logger.debug("trial data contains traits")
            traits = validated_data.pop("traits")
        else:
            traits = []

        # Assume traits are not modified and modified traits will
        # have own unique uuid. Add new traits to db.
        for trait_data in traits:
            print("TRAIT ", trait_data)

            trait_serializer = TraitNestedSerializer(data = trait_data)
            if trait_serializer.is_valid():
                trait = trait_serializer.save()
                print("TRAITSAVED ",trait)
                # .add() should make use of Trial model many-to-many Traits through TrialTraits
                
            else:
                logger.debug("trial data is not valid")

        # Save nodes
        for node_data in nodes:
            node = fpmodels.Node.objects.create(project=trial.project,trial=trial,**node_data)

        return trial
"""