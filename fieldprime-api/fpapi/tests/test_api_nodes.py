import json

from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Project, Trial, Node
from ..serializers import NodeSerializer

import logging
logger = logging.getLogger(__name__)

# initialize the APIClient app
client = Client()
factory = APIRequestFactory()

class TestNodeSetup(TestCase):

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
        self.node1 = Node.objects.create(
            row=1, 
            col=1, 
            description='Node 1',
            barcode='ST50PKT001',
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node2 = Node.objects.create(
            row=1, 
            col=2, 
            barcode='ST50PKT002',
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node3 = Node.objects.create(
            row=2, 
            col=1, 
            description='Node 3',
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node4 = Node.objects.create(
            row=2, 
            col=2, 
            description='Node 4',
            barcode='ST50PKT004',
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        self.node5 = Node.objects.create(
            row=3, 
            col=1, 
            description='Node 5',
            barcode='ST50PKT005',
            latitude=-36.25,
            project=self.proj1,
            trial=self.trial1,
        )
        """
        Can row/col be null?
        self.node6 = Node.objects.create(
            description='Node 6',
            barcode='ST50PKT006',
            latitude=-36.25,
            longitude=143.22,
            project=self.proj1,
            trial=self.trial1,
        )
        """
        self.valid_payload = {
            "row" : 3, 
            "col" : 2, 
            "description" : 'Node 6',
            "barcode" : 'ST50PKT006',
            "latitude" : -36.25,
            "project" : self.proj1.pk,
            "trial" : self.trial1.pk,
        }
        self.invalid_payload = {
            "row" : 3, 
            "col" : 2, 
            "description" : 'Node 6',
            "barcode" : 'ST50PKT006',
            "latitude" : -36.25,
        }

class GetAllNodesTest(TestNodeSetup):
    """ Test module for GET all Nodes API """

    def test_get_all_nodes(self):
        # get API response
        response = client.get(reverse('node-list'))
        # get data from db
        nodes = Node.objects.all()
        serializer = NodeSerializer(nodes, many=True, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetSingleNodeTest(TestNodeSetup):
    """ Test module for GET single Node API """

    def test_get_valid_single_node(self):
        response = client.get(
            reverse('node-detail',
            kwargs={'pk': self.node1.pk})
        )
        node = Node.objects.get(pk=self.node1.pk)
        serializer = NodeSerializer(node, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_single_node(self):
        response = client.get(
            reverse('node-detail', kwargs={'pk': -1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreateNewNodeTest(TestNodeSetup):
    """ Test module for inserting a new node """

    def test_create_valid_node(self):
        response = client.post(
            reverse('node-list'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Project should contain an extra node.
        count = Node.objects.filter(project=self.proj1.pk).count()
        self.assertEqual(count,6)

    def test_create_invalid_node(self):
        response = client.post(
            reverse('node-list'),
            data=json.dumps(self.invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateSingleNodeTest(TestNodeSetup):
    """ Test module for updating an existing node record """

    def test_valid_update_node(self):
        response = client.put(
            reverse('node-detail', kwargs={'pk': self.node1.pk}),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_node(self):
        response = client.put(
            reverse('node-detail', kwargs={'pk': self.node1.pk}),
            data=json.dumps(self.invalid_payload),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteSingleNodeTest(TestNodeSetup):
    """ Test module for deleting an existing node record """

    def test_valid_delete_node(self):
        response = client.delete(
            reverse('node-detail', kwargs={'pk': self.node1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(pk=self.node1.pk)
            

    def test_invalid_delete_node(self):
        response = client.delete(
            reverse('node-detail', kwargs={'pk': -1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)