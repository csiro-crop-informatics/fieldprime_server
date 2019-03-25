import json

from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Project
from ..serializers import ProjectSerializer

import logging
logger = logging.getLogger(__name__)

# initialize the APIClient app
client = Client()
factory = APIRequestFactory()

class TestProjectSetup(TestCase):

    def setUp(self):
        self.proj1 = Project.objects.create(
            name='Project1', 
            contact_name='Joe Bloggs', 
            contact_email='joe.bloggs@noreply.com')
        self.proj2 = Project.objects.create(
            name='Project2', 
            contact_name='Fred Bloggs',
            contact_email='Fred.Bloggs@noreply.com')
        self.proj3 = Project.objects.create(
            name='Project3',
            contact_name='George Bloggs',
            contact_email='gbloggs@noreply.com')

        self.valid_payload = {
            'name': 'Test Project Creation',
            'contact_name': 'Test Runner',
            'contact_email': 'test.noreply.com',
        }
        self.invalid_payload = {
            'name': '',
        }

class GetAllProjectsTest(TestProjectSetup):
    """ Test module for GET all Projects API """

    def test_get_all_projects(self):
        # get API response
        response = client.get(reverse('project-list'))
        # get data from db
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetSingleProjectTest(TestProjectSetup):
    """ Test module for GET single Project API """

    def test_get_valid_single_project(self):
        response = client.get(
            reverse('project-detail',
            kwargs={'pk': self.proj1.pk})
        )
        project = Project.objects.get(pk=self.proj1.pk)
        serializer = ProjectSerializer(project, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_single_project(self):
        response = client.get(
            reverse('project-detail', kwargs={'pk': 9999999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreateNewProjectTest(TestProjectSetup):
    """ Test module for inserting a new project """

    def test_create_valid_project(self):
        response = client.post(
            reverse('project-list'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_project(self):
        response = client.post(
            reverse('project-list'),
            data=json.dumps(self.invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateSingleProjectTest(TestProjectSetup):
    """ Test module for updating an existing project record """

    def test_valid_update_project(self):
        response = client.put(
            reverse('project-detail', kwargs={'pk': self.proj1.pk}),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_project(self):
        response = client.put(
            reverse('project-detail', kwargs={'pk': self.proj1.pk}),
            data=json.dumps(self.invalid_payload),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteSingleProjectTest(TestProjectSetup):
    """ Test module for deleting an existing project record """

    def test_valid_delete_project(self):
        response = client.delete(
            reverse('project-detail', kwargs={'pk': self.proj1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(pk=self.proj1.pk)
            

    def test_invalid_delete_project(self):
        response = client.delete(
            reverse('project-detail', kwargs={'pk': -1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)