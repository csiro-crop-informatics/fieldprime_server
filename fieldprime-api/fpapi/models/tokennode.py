
from django.db import models
from .userproject import Project
from .trialtrait import Token, Node

class TokenNode(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
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

    class Meta:
        db_table = 'tokenNode'