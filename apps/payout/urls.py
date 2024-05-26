from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.indexPayout, name='payout.listing'),
	path("edit-payout/<id>", views.editPayout, name='editpayout'),
    path("upload-pay-slip", views.uploadPaySlip, name='payout.payslip.upload'),
]
