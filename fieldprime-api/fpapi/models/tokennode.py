
from django.db import models
from .userproject import Project
from .trialtrait import Token, Node

class TokenNode(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE
        )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE
        )

    local_id = models.IntegerField(db_column='localId')  # Field name made lowercase.

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

    class Meta:
        db_table = 'tokenNode'
        unique_together = (('token', 'local_id'),)