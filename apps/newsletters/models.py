# languages/models.py
from django.db import models
from django.utils import timezone
from apps.api.models import User

class Newsletter(models.Model):
	id = models.AutoField(primary_key=True)
	subject = models.CharField(max_length=100, blank=False)
	body = models.TextField(blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'newsletters'

class NewsletterSubscriber(models.Model):
	id = models.AutoField(primary_key=True)
	email = models.CharField(max_length=200, blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	user= models.ForeignKey(User, models.PROTECT,related_name='+',null=True,blank=True)

	class Meta:
		db_table = 'newsletter_subscribers'


class ScheduledNewsletter(models.Model):
	id = models.AutoField(primary_key=True)
	subject = models.CharField(max_length=100, blank=False)
	body = models.TextField(blank=False)
	scheduled_date = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	is_send = models.IntegerField(default=0)
	
	class Meta:
		db_table = 'scheduled_newsletters'

class ScheduledNewsletterSubscriber(models.Model):
	id = models.AutoField(primary_key=True)
	scheduled_newsletter = models.ForeignKey(ScheduledNewsletter, on_delete=models.CASCADE)
	email = models.CharField(max_length=200, blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	status = models.BooleanField(default = False)
	mail_on = models.DateTimeField(null=True,blank=True)

	class Meta:
		db_table = 'scheduled_newsletter_subscribers'
