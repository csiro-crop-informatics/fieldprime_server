from django.db import models

from .trialtrait import Node, NodeAttribute
from .userproject import Project

class AttributeValue(models.Model):

    node_attribute = models.ForeignKey(
        NodeAttribute,
        on_delete = models.CASCADE,
        db_column = 'nodeAttribute_id'
    )
    node = models.ForeignKey(
        Node,
        on_delete = models.CASCADE,
    )
    
    value = models.TextField()

    """
    # Historical data was contained in separate
    # databases, here we store their old ids.
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
    migrated_node_attribute = models.IntegerField(
        null=True,
        blank=True,
        db_column = 'old_nodeAttribute_id',
    )
    """

    class Meta:
        db_table = 'attributeValue'
        unique_together = (('node_attribute', 'node'),)