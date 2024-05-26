from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db import models

class Faq(models.Model):
	id = models.AutoField(primary_key=True)
	question = models.TextField(blank=False)
	pagename = models.TextField(blank=True, null=True)
	answer = models.TextField(blank=False)
	is_active = models.IntegerField(default=1,blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'faqs'
		verbose_name_plural = 'Faqs'
		
		
class FaqDescription(models.Model):
	id = models.AutoField(primary_key=True)
	faq = models.ForeignKey(Faq, on_delete=models.CASCADE)
	language_code = models.CharField(db_index=True, max_length=20,blank=False)
	question = models.TextField(blank=True, null=True)
	answer = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'faq_description'
		verbose_name_plural = 'FaqDescription'
