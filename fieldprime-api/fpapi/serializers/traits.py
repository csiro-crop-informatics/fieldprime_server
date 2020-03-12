from rest_framework import serializers
from fpapi import models as fpmodels
from fpapi import const as fpconst

from .serializers import TraitNestedSerializer

import logging
logger = logging.getLogger('fpapi')

class TraitListSerializer(serializers.Serializer):

    traits = TraitNestedSerializer(many=True, required=False)
    trial = serializers.IntegerField(required=False)

    class Meta:
        fields = ("traits","trial")

    def create(self, validated_data):

        created_traits = []

        trial = validated_data.pop("trial")

        if "traits" in validated_data:
            logger.debug("TraitListSerializer: create: trial data contains traits")
            traits = validated_data.pop("traits")
        else:
            traits = []

        # Assume traits are not modified and modified traits will
        # have own unique uuid. Add new traits to db.
        for trait_data in traits:
            trait_data['trial'] = trial
            print("TraitListSerializer: create: trait_data: %s" % trait_data)

            trait_serializer = TraitNestedSerializer(data = trait_data)
            if trait_serializer.is_valid():
                trait = trait_serializer.save()
                created_traits.append(trait)
            else:
                logger.debug(trait_serializer.errors)
                logger.debug("trial data is not valid")

        return created_traits