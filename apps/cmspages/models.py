from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db import models

class CmsPage(models.Model):
	id = models.AutoField(primary_key=True)
	page_name = models.CharField(max_length=255,blank=False)
	page_title = models.CharField(max_length=255,blank=False)
	slug = models.CharField(db_index=True, max_length=255,blank=False)
	description = models.TextField(blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'cmspages'
		verbose_name_plural = 'CmsPage'

class CmsPageDescription(models.Model):
	id = models.AutoField(primary_key=True)
	cms_page = models.ForeignKey(CmsPage, on_delete=models.CASCADE)
	language_code = models.CharField(db_index=True, max_length=20,blank=False)
	page_title = models.CharField(max_length=255,blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'cmspage_descriptions'
		verbose_name_plural = 'CmsPageDescription'