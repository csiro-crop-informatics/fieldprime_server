from django.db import models
from .userproject import Project

class DeviceName(models.Model):

    android_id = models.CharField(
        db_column = 'androidId',
        max_length = 16
    )

    nickname = models.CharField(
        db_column = 'nickName',
        max_length = 63,
        blank = True,
        null = True
    )

    class Meta:
        db_table = 'deviceName'