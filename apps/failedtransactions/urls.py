from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.indexTransaction, name='failed_transaction.listing'),
    # path("upload-pay-slip/<id>", views.uploadPaySlip, name='payout.payslip.upload'),
]
