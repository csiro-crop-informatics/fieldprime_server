from django.db import models

from .trialtrait import Node, NodeAttribute
from .userproject import Project

class AttributeValue(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        )

    node_attribute = models.ForeignKey(
        NodeAttribute,
        on_delete=models.CASCADE,
        db_column = 'nodeAttribute_id'
        )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        )
    
    value = models.TextField()

    class Meta:
        db_table = 'attributeValue'