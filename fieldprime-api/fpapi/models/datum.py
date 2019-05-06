from django.db import models
from django.conf import settings
from .userproject import Project
from .trialtrait import Node, TraitInstance

class Datum(models.Model):

    node = models.ForeignKey(
        Node,
        on_delete = models.CASCADE,
    )
    trait_instance = models.ForeignKey(
        TraitInstance,
        on_delete = models.CASCADE,
        db_column ='traitInstance_id'
    )
    
    user_id = models.TextField(
        db_column = 'userid',
        blank = True,
        null = True
    )

    timestamp = models.BigIntegerField()
    gps_long = models.FloatField(
        blank = True,
        null = True
    )
    gps_lat = models.FloatField(
        blank = True,
        null = True
    )
    notes = models.TextField(
        blank = True,
        null= True
    )
    num_value = models.DecimalField(
        db_column = 'numValue',
        max_digits = 11,
        decimal_places = 3,
        blank = True,
        null = True
    )
    txt_value = models.TextField(
        db_column = 'txtValue',
        blank = True,
        null = True
    )

    """
    # Historical data was contained in separate
    # databases, here we store their old ids
    # No longer used this was from a previous merge attempt.
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    migrated_node = models.IntegerField(
        null=True, 
        blank=True,
        db_column = 'old_node_id',
    )
    migrated_trait_instance = models.IntegerField(
        null=True, 
        blank=True,
        db_column = 'old_traitInstance_id',
    )
    """

    @property
    def get_node_uuid(self):
        """
        Used in datum serializer
        """
        return self.node.barcode
    
    @property
    def get_trait_uuid(self):
        """
        Used in datum serializer
        """
        return self.trait_instance.trait.uuid

    class Meta:
        db_table = 'datum'
        unique_together = (('node', 'trait_instance', 'timestamp'),)