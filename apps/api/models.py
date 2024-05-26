from django.db import models
from apps.users.models import User
from apps.dropdownmanger.models import DropDownManager 
from django.utils import timezone

class ReportReasonModel(models.Model):
    user = models.ForeignKey(User, models.PROTECT,related_name='+')
    model_user = models.ForeignKey(User, models.PROTECT,related_name='+')
    dropdown_manager = models.ForeignKey(DropDownManager,  models.PROTECT,related_name='+')
    reason_description = models.TextField(blank=True, null=True) 
    created_at = models.DateTimeField(default=timezone.now, null=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True)
    class Meta:
        db_table = "report_reasons"
        
class currencyRate(models.Model):
    from_currency 	= models.CharField(max_length=255, blank=True, null=True) 
    to_currency 	= models.CharField(max_length=255, blank=True, null=True)
    price 			= models.CharField(max_length=255, blank=True, null=True) 
    created_at 		= models.DateTimeField(default=timezone.now, null=True)
    updated_at 		= models.DateTimeField(default=timezone.now, null=True)
    class Meta:
        db_table = "currency_rate"   
