from rest_framework import serializers
from fpapi import models as fpmodels
from fpapi import const as fpconst

import logging
logger = logging.getLogger(__name__)

class ChoicesField(serializers.Field):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ChoicesField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self._choices[obj]

    def to_internal_value(self, data):

        try:
            attr = getattr(self._choices, data)
        except:
            # Also allow integer choice value
            if data in self._choices:
                attr = data
            else:
                raise serializers.ValidationError
        return attr
        
class StringListField(serializers.ListField):
    child = serializers.CharField()

class NodeSerializer(serializers.ModelSerializer):

    # Project is a required field (it is a foreign key) but when it is used inside a nested
    # model creation this will be set when parent project is saved.
    # project = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Project.objects.all())
    # trial = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Trial.objects.all())

    class Meta:
        model = fpmodels.Node
        fields = ("url","row", "col", "description", "barcode", "latitude", "longitude")
        extra_kwargs = {
            'url': {'view_name': 'node-detail-uuid'}
        }

class NodeNestedSerializer(serializers.ModelSerializer):

    # Project is a required field (it is a foreign key) but when it is used inside a nested
    # model creation this will be set when parent project is saved.
    project = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Project.objects.all())
    trial = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Trial.objects.all())

    class Meta:
        model = fpmodels.Node
        fields = ("url","row", "col", "description", "barcode", "latitude", "longitude", "project", "trial")

class TrialSerializer(serializers.ModelSerializer):

    #traits = serializers.SerializerMethodField('get_alternate_name')
    #nodes = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Node.objects.all())
    """
    nodes = serializers.HyperlinkedRelatedField(
        view_name='node-detail-uuid',
        lookup_field='id',
        many=True,
        read_only=True
    )

    _traits = serializers.HyperlinkedRelatedField(
        view_name='trait-detail-uuid',
        lookup_field='uuid',
        many=True,
        read_only=True
    )
    """
    class Meta:
        model = fpmodels.Trial
        fields = ("url", "name", "site", "year", "acronym", "uuid", "project", "nodes", "_traits")
        extra_kwargs = {
            'url': {'view_name': 'trial-detail-uuid', 'lookup_field': 'uuid'}
        }
    
    def get_alternate_name(self, obj):
        return obj._traits

class TraitSerializer(serializers.ModelSerializer):

    class Meta:
        model = fpmodels.Trait
        fields = ("url", "uuid", "caption", "description", "data_type")
        extra_kwargs = {
            'url': {'view_name': 'trait-detail-uuid', 'lookup_field': 'uuid'}
        }

class DataTypeSerializer(serializers.Serializer):
    """
        This serializer must be used with TraitNestedSerializer
    """

    # Investigate ChoiceField for data_type
    data_type = ChoicesField(choices=fpconst.DATA_TYPES)
    min_value = serializers.FloatField(required=False)
    max_value = serializers.FloatField(required=False)
    #TODO may need to add a custom serializer for accepted values
    # as we are not handling the field url in TraitCategory
    accepted_values = StringListField(required=False)

    def validate(self, data):
        """
        Check that categorical data also has accepted_values
        """
        data = super(DataTypeSerializer, self).validate(data)
        print("Data ", data)
        if data['data_type'] == fpconst.CATEGORICAL:
            if "accepted_values" not in data.keys():
                raise serializers.ValidationError("Categorical data must provide accepted_values")
        return data

    def create(self, validated_data):
        """
        This serializer is only used to validate data, it does not
        have enough information by itself to save data to tables.
        """
        raise NotImplementedError


class TraitNestedSerializer(serializers.ModelSerializer):

    data_type = DataTypeSerializer(required=True)
    trial = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Trial.objects.all())

    class Meta:
        model = fpmodels.Trait
        fields = ("url", "caption", "description", "uuid", "data_type", "trial")

    def create(self, validated_data):

        data_type_data = validated_data.pop("data_type")
        print("Data TYPE DATA", data_type_data)
        trial_id = validated_data.pop("trial")

        # For V2 api, all traits are public and reused with uuid
        # with legacy 'public mode' trail_id of -1
        # But real trial_id still needs to get passed down to TrialTraitNumeric

        trait, created = fpmodels.Trait.objects.get_or_create(
            **validated_data, 
            trial_id = -1, 
            _data_type=data_type_data["data_type"])
        print("TRAITSAVED ",trait,trait.id,created)

        self._create_data_type(trial_id, trait, data_type_data)
        return trait

    def _create_data_type(self, trial_id, trait, data):
        
        data_type = data.pop("data_type")
        print("DATATYPE",data_type)

        # Handle numeric types
        if data_type in [fpconst.INTEGER, fpconst.DECIMAL]:
            trial_extra_data, created = fpmodels.TrialTraitNumeric.objects.get_or_create(
                trial = trial_id,
                trait = trait,
                **data
            )
            #trial_extra_data.save()
            logger.debug("saved numeric info")
        # Handle categorical type
        elif data_type in [fpconst.CATEGORICAL]:        
            for i,category in enumerate(data["accepted_values"]):
                trial_extra_data, created = fpmodels.TraitCategory.objects.get_or_create(
                    trait = trait,
                    value = i,
                    caption = category,
                    #TODO url...
                )
                #trial_extra_data.save()
                logger.debug("saved cat info: %s" % trial_extra_data)
        #TODO: Handle other types (date/photo/string)


class TrialNestedSerializer(serializers.ModelSerializer):

    nodes = NodeNestedSerializer(many=True, required=False)
    traits = TraitNestedSerializer(many=True, required=False)
    # Project is a required field (it is a foreign key) but when it is used inside a nested
    # model creation this will be set when parent project is saved.
    project = serializers.PrimaryKeyRelatedField(required=False, queryset=fpmodels.Project.objects.all())

    class Meta:
        model = fpmodels.Trial
        fields = ("url", "name", "site", "year", "acronym", "uuid", "project", "traits", "nodes")
        #extra_kwargs = {
        #    'url': {'view_name': 'trial-detail-uuid', 'lookup_field': 'uuid'}
        #}

    def create(self, validated_data):
        
        if "nodes" in validated_data:
            logger.debug("trial data contains nodes")
            nodes = validated_data.pop("nodes")
        else:
            nodes = []

        if "traits" in validated_data:
            logger.debug("trial data contains traits")
            traits = validated_data.pop("traits")
        else:
            traits = []
        
        trial = fpmodels.Trial.objects.create(**validated_data)
        logger.debug("TRIAL %s %d" % (str(trial),trial.id))

        # Save traits
        for trait_data in traits:
            print("TRAIT ", trait_data)
            # Add project association to trial
            trait_data['trial'] = trial.id
            trait_serializer = TraitNestedSerializer(data = trait_data)
            if trait_serializer.is_valid():
                trait = trait_serializer.save()
                print("TRAITSAVED ",trait)
                # .add() should make use of Trial model many-to-many Traits through TrialTraits
                trialtrait = fpmodels.TrialTrait.objects.create(trial=trial,trait=trait)
            else:
                logger.debug("trial data is not valid")

        # Save nodes
        for node_data in nodes:
            node = fpmodels.Node.objects.create(project=trial.project,trial=trial,**node_data)

        return trial

    def update(self, instance, validated_data):
        
        instance.uuid = validated_data.get('uuid', instance.uuid)
        return instance

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = fpmodels.Project
        fields = ("url", "name", "contact_name", "contact_email", "uuid")
        extra_kwargs = {
            'url': {'view_name': 'project-detail-uuid', 'lookup_field': 'uuid'}
        }


class ProjectNestedSerializer(serializers.ModelSerializer):

    trials = TrialNestedSerializer(many=True, required=False)

    class Meta:
        model = fpmodels.Project
        fields = ("url", "name", "contact_name", "contact_email", "uuid", "trials")

    def create(self, validated_data):
    
        logger.debug("ProjectNestedSerializer: creating project")

        if "trials" in validated_data:
            logger.debug("ProjectNestedSerializer: project data contains trials")
            trials = validated_data.pop("trials")
        else:
            trials = []

        # Save project and add project_id to trials/nodes
        project = fpmodels.Project.objects.create(**validated_data)
        logger.debug('ProjectNestedSerializer: created project: %s\n' % project)

        for trial_data in trials:
            # Add project association to trial
            trial_data['project'] = project.id
            trial_serializer = TrialNestedSerializer(data = trial_data)
            logger.debug("ProjectNestedSerializer: trial data: %s" % str(trial_data))
            if trial_serializer.is_valid():
                trial_serializer.save()
            else:
                logger.debug("ProjectNestedSerializer: trial is not valid")
       
        return project

class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = fpmodels.User
        fields = ("url", "login", "name",)

