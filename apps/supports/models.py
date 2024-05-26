from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Support(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=255, blank=False)
	email = models.CharField(max_length=255, blank=False)
	subject = models.CharField(max_length=255, blank=False)
	message = models.TextField(blank=False)
	phone_number = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'supports'
