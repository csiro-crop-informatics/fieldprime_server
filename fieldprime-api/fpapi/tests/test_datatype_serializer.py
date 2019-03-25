import json

from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Project, Trial, Trait
from ..serializers import DataTypeSerializer

import logging
logger = logging.getLogger(__name__)

# initialize the APIClient app
client = Client()
factory = APIRequestFactory()

class TestTrialSetup(TestCase):

    def setUp(self):
        self.proj1 = Project.objects.create(
            name='Project1', 
            contact_name='Joe Bloggs', 
            contact_email='joe.bloggs@noreply.com'
        )
        self.trial1 = Trial.objects.create(
            name='Trial1', 
            site='Boorowa', 
            year='2019',
            acronym='T1',
            project=self.proj1,
        )
        self.trait1 = Trait.objects.create(
            caption='Trait1', 
            description='TraitDescription', 
            trial=self.trial1,
            project=self.proj1,
            _data_type=1,
        )

        self.valid_payloads = [
            {
                "data_type" : "INTEGER",
            },
            {
                "data_type" : "DECIMAL",
                "min_value" : 0,
                "max_value" : 10
            },
            {
                "data_type" : "STRING",
            },
            {
                "data_type" : "CATEGORICAL",
                "accepted_values": ["HIGH","MEDIUM","LOW"]
            }
        ]
        self.invalid_payloads = [
            {
                "data_type" : "UNKNOWN"
            },
        ]

class CreateNewDataType(TestTrialSetup):
    """ Test module for inserting a new trial """

    def test_data_type_serializer(self):
        for payload in self.valid_payloads:
            data_type_serializer = DataTypeSerializer(data = payload)
            self.assertEqual(data_type_serializer.is_valid(),True)
        for payload in self.invalid_payloads:
            data_type_serializer = DataTypeSerializer(data = payload)
            self.assertEqual(data_type_serializer.is_valid(),False)

        