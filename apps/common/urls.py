from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.commonMail, name='common.mail'),
    path("check-notifications", views.check_notification_enable, name='common.notifications'),
	
]
