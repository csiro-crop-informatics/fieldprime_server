from rest_framework import serializers
from fpapi import models as fpmodels

class NodeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.Node
        fields = ('url','row', 'col', 'description', 'barcode', 'latitude', 'longitude')

class ProjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.Project
        fields = ('url', 'name', 'contact_name', 'contact_email', 'uuid')

class TraitSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.Trait
        fields = ('url','caption', 'description', 'data_type', 'uuid')

class TrialSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.Trial
        fields = ('url', 'name', 'site', 'year', 'acronym', 'uuid')

class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.User
        fields = ('url', 'login', 'name',)

