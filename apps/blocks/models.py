from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db import models

class Block(models.Model):
	id = models.AutoField(primary_key=True)
	page_name = models.CharField(db_index=True, max_length=255, blank=False)
	page_slug = models.CharField(max_length=255,blank=True)
	block_name= models.CharField(max_length=255,blank=False)
	slug= models.CharField(db_index=True,max_length=255,blank=False)
	description=models.TextField(blank=False)
	image = models.CharField(max_length=255, blank=True)
	block_order = models.IntegerField(default=0,blank=False)
	is_active = models.IntegerField(default=1,blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'blocks'
		verbose_name_plural = 'Block'

class BlockDescription(models.Model):
	id = models.AutoField(primary_key=True)
	block = models.ForeignKey(Block, on_delete=models.CASCADE)
	language_code = models.CharField(db_index=True, max_length=20,blank=False)
	block_name = models.CharField(max_length=255,blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'block_descriptions'
		verbose_name_plural = 'BlockDescription'
