import json

from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Project, Trial, Node
from ..serializers import ProjectSerializer

import logging
logger = logging.getLogger(__name__)

# initialize the APIClient app
client = Client()
factory = APIRequestFactory()

class TestNodeSetup(TestCase):

    def setUp(self):
        self.proj1 = Project.objects.create(
            name="Project1", 
            contact_name="Joe Bloggs", 
            contact_email="joe.bloggs@noreply.com"
        )
        self.trial1 = Trial.objects.create(
            name="Trial1", 
            site="Boorowa", 
            year="2019",
            acronym="T1",
            project=self.proj1,
        )
        self.node1 = Node.objects.create(
            row=1, 
            col=1, 
            description="Node 1",
            barcode="ST50PKT001",
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node2 = Node.objects.create(
            row=1, 
            col=2,
            description="Node 2", 
            barcode="ST50PKT002",
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node3 = Node.objects.create(
            row=2, 
            col=1, 
            description="Node 3",
            barcode="ST50PKT003",
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node4 = Node.objects.create(
            row=2, 
            col=2, 
            description="Node 4",
            barcode="ST50PKT004",
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )

        self.valid_payload = {
            "name" : "Project:Nested Model Test", 
            "contact_name" : "Test Runner", 
            "contact_email" : "test@noreply.com",
            "uuid" : "1234567890",
            "trials" : [{
                "name" : "Trial1", 
                "site" : "Boorowa", 
                "year" : "2019",
                "acronym" : "B-T1",
                "nodes" : [{
                    "row" : 1, 
                    "col" : 1, 
                    "description" : "Node 1",
                    "barcode" : "ST50PLT001",
                    "latitude" : -35.25,
                    "longitude" : 142.22
                },
                {
                    "row" : 2, 
                    "col" : 1, 
                    "description" : "Node 2",
                    "barcode" : "ST50PLT002",
                    "latitude" : -35.25,
                    "longitude" : 142.22
                }],
                "traits" : [{
                    "caption": "IntegerTest",
                    "description": "TestDescription",
                    "data_type": {
                        "data_type" : "INTEGER",
                        "min_value" : 0,
                        "max_value" : 10
                    }
                },
                {
                    "caption" : "DecimalTest",
                    "description": "TestDescription",
                    "data_type": {
                        "data_type" : "DECIMAL",
                        "min_value" : 1.0,
                        "max_value" : 10.0
                    }
                },
                {
                    "caption" : "CategoricalTest",
                    "description": "TestCategorical",
                    "data_type": {
                        "data_type" : "CATEGORICAL",
                        "accepted_values": ["HIGH","MEDIUM","LOW"]
                    }
                }]

            }],
        }
        
        self.invalid_payload = {

        }

        """
                "traits" : [{
                    "name": "IntegerTest",
                    "description": "TestDescription",
                    "method": "TestIntegerMethod",
                    "data_type": {
                        "data_type" : "Integer",
                        "min_value" : 0,
                        "max_value" : 10
                    }
                },
                {
                    "name" : "DecimalTest",
                    "description": "TestDescription",
                    "method": "TestDecimalMethod",
                    "data_type": {
                        "data_type" : "Decimal",
                        "min_value" : 0,
                        "max_value" : 2
                    }
                },
                {
                    "name": "TextTest",
                    "description": "TestTextDescription",
                    "method": "TestTextMethod",
                    "data_type": {
                        "data_type" : "Text"
                    }
                },
                {
                    "name" : "TestDate",
                    "description": "TestDateDescription",
                    "method": "TestDateMethod",
                    "data_type": {
                        "data_type" : "Date"

                    }
                },
                {
                    "name": "TestImage",
                    "description": "TestImageDescription",
                    "method": "TestImageDescription",
                    "data_type": {
                        "data_type" : "Image"
                    }
                },
                {
                    "name": "TestCategorical",
                    "description": "TestCategoricalDescription",
                    "method": "TestCategoricalMethod",
                    "data_type": {
                        "data_type" : "Categorical",
                        "accepted_values": ["High","Medium","Low"]
                    }
                }]
        """

class GetProjectWithNestedModelTest(TestNodeSetup):
    """ Test module for GET all Nodes API """

    def test_get_project_trials_nodes(self):
        # get API response
        response = client.get(
            reverse("project-detail",
            kwargs={"pk": self.proj1.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # get data from db
        project = Project.objects.get(pk=self.proj1.pk)
        serializer = ProjectSerializer(project, context={"request": factory.get("/")})
        self.assertEqual(response.data, serializer.data)



class CreateNewProjectWithNestedModes(TestNodeSetup):

    def test_create_valid_node(self):

        response = client.post(
            reverse("project-list"),
            data=json.dumps(self.valid_payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check trial is saved
        project = Project.objects.get(uuid=response.data["uuid"])
        trials = Trial.objects.filter(project=project)
        self.assertEqual(trials.count(), 1)
        # Check node is saved
        trial = trials[0]
        self.assertEqual(trial.nodes.count(), 2)


    """    
    def test_create_invalid_node(self):
        response = client.post(
            reverse("node-list"),
            data=json.dumps(self.invalid_payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    """

# UPDATE/DELETE not defined