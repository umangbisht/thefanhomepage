from django.db import models
from django.utils import timezone

# Create your models here.
class SliderImage(models.Model):
    title = models.CharField(max_length=255,blank=True, null=True)
    slider = models.CharField(max_length=255,blank=True, null=True)
    description = models.CharField(max_length=255,blank=True, null=True)
    order = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.IntegerField(default=1)
    class Meta:
        db_table='slider_image'
