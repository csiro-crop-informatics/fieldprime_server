
from django.db import models
from .userproject import Project
from .trialtrait import Token, Node

class TokenNode(models.Model):

    token = models.ForeignKey(
        Token,
        on_delete = models.CASCADE
        )
    node = models.ForeignKey(
        Node,
        on_delete = models.CASCADE
        )

    local_id = models.IntegerField(
        db_column = 'localId'
    )

    """
    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_token = models.IntegerField(
        null=True, 
        blank=True,
        db_column = 'old_token_id',
    )
    migrated_node = models.IntegerField(
        null=True, 
        blank=True,
        db_column = 'old_node_id',
    )
    """

    class Meta:
        db_table = 'tokenNode'
        unique_together = (('token', 'local_id'),)