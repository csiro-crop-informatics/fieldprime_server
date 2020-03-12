from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _

from fpapi.managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    """
        fpsys.user table
    """

    login = models.CharField(unique=True, max_length=63)
    name = models.CharField(max_length=255, blank=True, null=True)
    passhash = models.CharField(max_length=255, blank=True, null=True)
    login_type = models.IntegerField(blank=True, null=True)
    permissions = models.IntegerField(blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        db_table = 'user'
        verbose_name_plural = _('users')

class ProjectPermissions(models.Model):
    """
        fpsys.project table
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )

    dbname = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    migrated_dbname = models.CharField(
        db_column = "old_dbname",
        max_length = 255,
        blank = True,
        null = True
    )

    members = models.ManyToManyField(User, through='UserProject')

class UserProject(models.Model):
    """
        fpsys
    """

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
    )
    project = models.ForeignKey(
        ProjectPermissions,
        on_delete = models.CASCADE,
    )

    permissions = models.IntegerField(
        blank = True,
        null = True
    )

    class Meta:
        db_table = 'userProject'
        unique_together = (('user', 'project'),)

class Project(models.Model):

    uuid = models.UUIDField(
        # For backwards compatibility
        blank = True,
        null = True,
        unique = True,
    )

    parent_project = models.ForeignKey(
        "Project",
        on_delete = models.SET_NULL,
        db_column = 'up_id',
        blank = True,
        null = True,
    )

    name = models.CharField(
        unique = True,
        max_length = 63
    )
    contact_name = models.TextField(
        db_column = 'contactName',
    )

    contact_email = models.TextField(
        db_column = 'contactEmail',
    )

    migrated_project = models.CharField(
        db_column = 'old_project_db',
        max_length = 63,
        blank = True,
        null = True
    )

    class Meta:
        db_table = 'project'