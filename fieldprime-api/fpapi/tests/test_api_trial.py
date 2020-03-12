import json

from rest_framework import status
from rest_framework.test import APIRequestFactory
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Project, Trial
from ..serializers import TrialSerializer

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
        self.trial2 = Trial.objects.create(
            name='Trial2', 
            site='Boorowa', 
            year='2019',
            project=self.proj1,
        )
        self.trial3 = Trial.objects.create(
            name='Trial3', 
            site='Boorowa', 
            acronym='T3',
            project=self.proj1,
        )
        self.trial4 = Trial.objects.create(
            name='Trial4', 
            year='2019',
            acronym='T4',
            project=self.proj1,
        )
        self.trial5 = Trial.objects.create(
            name='Trial5', 
            year='2019',
            acronym='T5',
            uuid='1234-1234-1234-1234',
            project=self.proj1,
        )

        self.valid_payload = {
            'name' : 'Trial6', 
            'site' : 'Boorowa', 
            'year' : '2019',
            'acronym' : 'T6',
            'project' : self.proj1.pk
        }
        self.invalid_payload = {
            'name' : '',
        }

class GetAllTrialsTest(TestTrialSetup):
    """ Test module for GET all Trials API """

    def test_get_all_trials(self):
        # get API response
        response = client.get(reverse('trial-list'))
        # get data from db
        trials = Trial.objects.all()
        serializer = TrialSerializer(trials, many=True, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GetSingleTrialTest(TestTrialSetup):
    """ Test module for GET single Trial API """

    def test_get_valid_single_trial(self):
        response = client.get(
            reverse('trial-detail',
            kwargs={'pk': self.trial1.pk})
        )
        trial = Trial.objects.get(pk=self.trial1.pk)
        serializer = TrialSerializer(trial, context={'request': factory.get('/')})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_single_trial(self):
        response = client.get(
            reverse('trial-detail', kwargs={'pk': -1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class CreateNewTrialTest(TestTrialSetup):
    """ Test module for inserting a new trial """

    def test_create_valid_trial(self):
        response = client.post(
            reverse('trial-list'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Project should contain an extra trial.
        count = Trial.objects.filter(project=self.proj1.pk).count()
        self.assertEqual(count,6)

    def test_create_invalid_trial(self):
        response = client.post(
            reverse('trial-list'),
            data=json.dumps(self.invalid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateSingleTrialTest(TestTrialSetup):
    """ Test module for updating an existing trial record """

    def test_valid_update_trial(self):
        response = client.put(
            reverse('trial-detail', kwargs={'pk': self.trial1.pk}),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_update_trial(self):
        response = client.put(
            reverse('trial-detail', kwargs={'pk': self.trial1.pk}),
            data=json.dumps(self.invalid_payload),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class DeleteSingleTrialTest(TestTrialSetup):
    """ Test module for deleting an existing trial record """

    def test_valid_delete_trial(self):
        response = client.delete(
            reverse('trial-detail', kwargs={'pk': self.trial1.pk}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Trial.DoesNotExist):
            Trial.objects.get(pk=self.trial1.pk)
            

    def test_invalid_delete_trial(self):
        response = client.delete(
            reverse('trial-detail', kwargs={'pk': -1}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)