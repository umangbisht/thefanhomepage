# languages/models.py
from django.db import models
from django.utils import timezone

class Language(models.Model):
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=100, blank=False)
	lang_code = models.CharField(db_index=True, max_length=100, blank=False)
	folder_code = models.CharField(db_index=True, max_length=100, blank=False)
	is_active = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'languages'

class LanguageSetting(models.Model):
	id = models.AutoField(primary_key=True)
	msgid = models.CharField(db_index=True, max_length=255, blank=False)
	locale = models.CharField(db_index=True, max_length=255, blank=False)
	msgstr = models.CharField(max_length=255, blank=False)
	is_active = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'language_settings'



