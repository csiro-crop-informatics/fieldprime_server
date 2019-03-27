from django.db import models
from .userproject import Project

class DeviceName(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )

    android_id = models.CharField(db_column='androidId', max_length=64)  # Field name made lowercase.
    nickname = models.CharField(db_column='nickName', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'deviceName'