from django.db import models
from .userproject import Project

class Trial(models.Model):
    """
    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )

    name = models.CharField(max_length=255)
    site = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    acronym = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'trial'

class Trait(models.Model):
    """
    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    caption = models.CharField(max_length=255)
    description = models.TextField()
    data_type = models.IntegerField(db_column='datatype')

    # Not it FieldPrime SQL init but exists in database schema.
    #t_id = models.TextField(db_column='tid', blank=True, null=True)
    #unit = models.TextField(blank=True, null=True)
    #min_val = models.DecimalField(db_column='min', max_digits=10, decimal_places=0, blank=True, null=True)
    #max_val = models.DecimalField(db_column='max', max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        db_table = 'trait'

class Token(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    token = models.CharField(max_length=31)

    class Meta:
        db_table = 'token'

class Node(models.Model):
    """
    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    row = models.IntegerField()
    col = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # Not it FieldPrime SQL init but exists in database schema.
    #xGenotype = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'node'

class NodeAttribute(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    name = models.CharField(max_length=255)
    data_type = models.IntegerField(db_column='datatype')
    func = models.IntegerField()

    class Meta:
        db_table = 'nodeAttribute'

class NodeNote(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE
        )
    token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE
        )

    note = models.TextField(blank=True, null=True)
    timestamp = models.BigIntegerField()
    user_id = models.TextField(db_column='userid', blank=True, null=True)

    class Meta:
        db_table = 'nodeNote'


class TrialProperty(models.Model):

    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )

    name = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'trialProperty'

class TrialTrait(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )
    node_attribute = models.ForeignKey(
        NodeAttribute,
        on_delete=models.SET_NULL,
        db_column='barcodeAtt_id', 
        blank=True, 
        null=True
    )

    class Meta:
        db_table = 'trialTrait'

class TrialTraitNumeric(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )

    min_val = models.DecimalField(db_column='min', max_digits=18, decimal_places=9, blank=True, null=True)
    max_val = models.DecimalField(db_column='max', max_digits=18, decimal_places=9, blank=True, null=True)
    validation = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'trialTraitNumeric'

class TraitCategory(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )
    value = models.IntegerField()
    caption = models.TextField()
    image_url = models.TextField(db_column='imageURL', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'traitCategory'

class TraitInstance(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )
    token = models.ForeignKey(
        Token,
        on_delete=models.CASCADE
        )
   
    day_created = models.IntegerField(db_column='dayCreated')  # Field name made lowercase.
    sequence_number = models.IntegerField(db_column='seqNum')  # Field name made lowercase.
    sample_number = models.IntegerField(db_column='sampleNum')  # Field name made lowercase.

    class Meta:
        db_table = 'traitInstance'

class TraitString(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )

    pattern = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'traitString'