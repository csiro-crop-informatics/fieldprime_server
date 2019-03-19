from django.db import models
from django.conf import settings
from .userproject import Project
from .trialtrait import Node, TraitInstance

class Datum(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        )
    trait_instance = models.ForeignKey(
        TraitInstance,
        on_delete=models.CASCADE,
        db_column='traitInstance_id'
        )
    
    user_id = models.TextField(db_column='userid', blank=True, null=True)

    timestamp = models.BigIntegerField()
    gps_long = models.FloatField(blank=True, null=True)
    gps_lat = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    num_value = models.DecimalField(db_column='numValue', max_digits=11, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    txt_value = models.TextField(db_column='txtValue', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'datum'