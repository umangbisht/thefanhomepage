
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db import models

class DropDownManager(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(db_index=True, max_length=255,blank=False)
	slug = models.CharField(max_length=255,blank=True, null=True)
	dropdown_type = models.CharField(db_index=True, max_length=255,blank=False)
	is_active = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'dropdown_managers'
		verbose_name_plural = 'DropDownManager'

class DropDownManagerDescription(models.Model):
	id = models.AutoField(primary_key=True)
	dropdown_manger = models.ForeignKey(DropDownManager, on_delete=models.CASCADE)
	language_code = models.CharField(db_index=True, max_length=20,blank=False)
	name = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'dropdown_manager_descriptions'
		verbose_name_plural = 'DropDownManagerDescription'