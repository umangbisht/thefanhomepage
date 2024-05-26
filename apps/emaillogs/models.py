from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class EmailLog(models.Model):
	id = models.AutoField(primary_key=True)
	email_to = models.CharField(max_length=100, blank=False)
	email_from = models.CharField(max_length=100, blank=False)
	subject = models.CharField(max_length=255, blank=False)
	message = models.TextField(blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'email_logs'

