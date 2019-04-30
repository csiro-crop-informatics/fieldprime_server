from django.db import models
from django.utils.translation import gettext as _
from .userproject import Project
from ..const import DATA_TYPES

class Trait(models.Model):

    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    ## trial column is present, but won't be using it
    ## Using TrialTraits instead
    # trial = models.ForeignKey(
    #     Trial,
    #     on_delete=models.CASCADE,
    #     blank=True, 
    #     null=True,
    #     )
    trial_id = models.IntegerField(db_column="trial_id", blank=True, null=True)

    caption = models.CharField(max_length=255)
    description = models.TextField()

    # 
    _data_type = models.IntegerField(
        db_column="datatype", 
        choices=DATA_TYPES
    )
    @property
    def data_type(self):
        return self._data_type

    # Not it FieldPrime SQL init but exists in database schema.
    t_id = models.TextField(db_column="tid", blank=True, null=True)
    unit = models.TextField(blank=True, null=True)
    min_val = models.DecimalField(db_column="min", max_digits=10, decimal_places=0, blank=True, null=True)
    max_val = models.DecimalField(db_column="max", max_digits=10, decimal_places=0, blank=True, null=True)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "trait"


class Trial(models.Model):

    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    project = models.ForeignKey(
        Project,
        related_name="trials",
        on_delete=models.CASCADE,
        )

    name = models.CharField(max_length=255)
    site = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    acronym = models.CharField(max_length=255, blank=True, null=True)

    traits = models.ManyToManyField(
        Trait,
        through='TrialTrait',
        through_fields=('trial', 'trait')
    )

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )

    class Meta:
        db_table = "trial"


class DataType(models.Model):


    data_type = models.IntegerField(max_length=1, choices=DATA_TYPES)
    unit = models.TextField(blank=True, null=True)
    min_value = models.DecimalField(db_column="min", max_digits=18, decimal_places=9, blank=True, null=True)
    max_val = models.DecimalField(db_column="max", max_digits=18, decimal_places=9, blank=True, null=True)

    class Meta:
        abstract = True


class Token(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    token = models.CharField(max_length=31)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "token"

class Node(models.Model):

    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    trial = models.ForeignKey(
        Trial,
        related_name="nodes",
        on_delete=models.CASCADE
        )

    row = models.IntegerField()
    col = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # Not it FieldPrime code base but exists in database schema.
    xGenotype = models.TextField(blank=True, null=True)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "node"

class NodeAttribute(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )

    name = models.CharField(max_length=255)
    data_type = models.IntegerField(db_column="datatype")
    func = models.IntegerField()

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "nodeAttribute"
        unique_together = (("trial", "name"),)

class NodeNote(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
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
    user_id = models.TextField(db_column="userid", blank=True, null=True)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_node = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_node_id",
    )
    migrated_token = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_token_id",
    )

    class Meta:
        db_table = "nodeNote"
        # Django cannot create a unique contraint for note (mysql) as this requires a length
        #unique_together = (("node", "timestamp", "note"),)


class TrialProperty(models.Model):

    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )

    name = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "trialProperty"
        unique_together = (("trial", "name"),)

class TrialTrait(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
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
        db_column="barcodeAtt_id", 
        blank=True, 
        null=True,
    )

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_node_attribute = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_barcodeAtt_id",
    )
    migrated_trait = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trait_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "trialTrait"
        unique_together = (("trait", "trial"),)
        

class TrialTraitNumeric(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )

    min_value = models.DecimalField(db_column="min", max_digits=18, decimal_places=9, blank=True, null=True)
    max_value = models.DecimalField(db_column="max", max_digits=18, decimal_places=9, blank=True, null=True)
    validation = models.TextField(blank=True, null=True)

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_trait = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trait_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "trialTraitNumeric"
        unique_together = (("trial", "trait"),)

class TraitCategory(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
        )
    trait = models.ForeignKey(
        Trait,
        on_delete=models.CASCADE
        )
    value = models.IntegerField()
    caption = models.TextField()
    image_url = models.TextField(db_column="imageURL", blank=True, null=True)  # Field name made lowercase.

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_trait = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trait_id",
    )

    class Meta:
        db_table = "traitCategory"
        unique_together = (("trait", "value"),)
        

class TraitInstance(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
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
   
    day_created = models.IntegerField(db_column="dayCreated")  # Field name made lowercase.
    sequence_number = models.IntegerField(db_column="seqNum")  # Field name made lowercase.
    sample_number = models.IntegerField(db_column="sampleNum")  # Field name made lowercase.

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_id = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_id",
    )
    migrated_trait = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trait_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )
    migrated_token = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_token_id",
    )

    class Meta:
        db_table = "traitInstance"
        unique_together = (("trial", "trait", "token", "sequence_number", "sample_number"),)

class TraitString(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=True, 
        null=True,
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

    # Historical data was contained in separate
    # databases, here we store their old ids
    migrated_trait = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trait_id",
    )
    migrated_trial = models.IntegerField(
        null=True, 
        blank=True,
        db_column = "old_trial_id",
    )

    class Meta:
        db_table = "traitString"
        unique_together = (("trial", "trait"),)
