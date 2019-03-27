from django.test import TestCase
from ..models import Project

class ProjectTest(TestCase):

    def setUp(self):
        Project.objects.create(
            name = 'Test'
        )

    def test_fields(self):
        project = Project.objects.get(name='Test')
        self.assertEqual(
            project.name, "Test"
        )