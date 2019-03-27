from django.db import models
from .userproject import Project

class System(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )

    name = models.CharField(unique=True, max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'system'