# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class EmailAction(models.Model):
	id = models.AutoField(primary_key=True )
	action = models.CharField(max_length=255, blank=True)
	option = models.CharField(max_length=255, blank=True)
	is_active = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'email_actions'
		
class EmailTemplates(models.Model):
	id = models.AutoField(primary_key=True )
	name = models.CharField(db_index=True, max_length=255, blank=False)
	subject= models.TextField( blank=True)
	action= models.CharField(max_length=255,blank=True,null=True)
	body= models.TextField(max_length=200, blank=True)
	is_active = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'email_templates'



