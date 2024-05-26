from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.indexSubscriber, name='users.subscribers'),
	path("deleted/", views.indexDeletedSubscriber, name='users.deleted_subscribers'),
	path("add-subscriber/", views.addSubscriber, name='users.add_subscriber'),
	path("edit-subscriber/<id>", views.editSubscriber, name='users.edit_subscriber'),
	path("change-status/<id>/<status>", views.changeStatusSubscriber, name='users.change_status_subscriber'),
	path("delete/<id>", views.deleteSubscriber, name='users.delete_subscriber'),
	path("view/<id>", views.viewSubscriber, name='users.view_subscriber'),
	path("change-approve-status/<id>/<status>", views.changeApproveStatus, name='users.changeApproveStatus'),
	path("view-model-history/<id>", views.viewModelHistory, name='users.view_model_history'),
	path("view-transaction-history/<id>", views.viewTransactionHistory, name='users.view_transaction_history'),
	path("active-subscription-plans/<id>", views.viewActiveSubscriptionPlans, name='users.view_active_subscription_plan'),
	path("expired-subscription-plans/<id>", views.viewExpiredSubscriptionPlans, name='users.view_expired_subscription_plan'),
	path("export/xls", views.export_subscribers_xls, name='export_subscribers_xls'),
	
	
]
