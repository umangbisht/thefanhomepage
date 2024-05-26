from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.indexTransaction, name='transaction.listing'),
    # path("upload-pay-slip/<id>", views.uploadPaySlip, name='payout.payslip.upload'),
    path("export/xls", views.export_transactions_xls, name='export_transactions_xls'),
    path("refund-transaction/<id>", views.refundtransaction, name='refund-transaction'),
]
