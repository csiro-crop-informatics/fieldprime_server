from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _

from fpapi.managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):

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

class Project(models.Model):

    uuid = models.CharField(
        max_length=64,
        # For backwards compatibility
        blank = True,
        null=True,
        unique=True,
        )
    parent_project = models.ForeignKey(
        "Project",
        on_delete = models.SET_NULL,
        db_column='up_id',
        blank=True,
        null=True,
        )
    members = models.ManyToManyField(User, through='UserProject')

    name = models.CharField(unique=True, max_length=255)
    contact_name = models.CharField(
        db_column='contactName', 
        max_length=255, 
        blank=True, 
        null=True
        ) 
    contact_email = models.CharField(
        db_column='contactEmail', 
        max_length=255, 
        blank=True, 
        null=True
        )

    class Meta:

        db_table = 'project'
 
class UserProject(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        )

    permissions = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'userProject'
        unique_together = (('user', 'project'),)