
from django.db import models
from django.utils import timezone

class Setting(models.Model):
	id = models.AutoField(primary_key=True)
	key = models.CharField(db_index=True, max_length=255, blank=False)
	value = models.TextField(max_length=255, blank=True)
	title= models.CharField(blank=False,max_length=255)
	description=models.TextField(max_length=200)
	input_type=models.CharField(db_index=True, max_length=255, blank=False)
	editable = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'settings'
