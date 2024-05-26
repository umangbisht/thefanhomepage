from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
	path("", views.indexModel, name='users.models'),
	path("deleted", views.indexDeletedModel, name='users.deleted_models'),
	path("add-model-validation/", views.addModelValidation, name='addModelValidation'),
	path("add-model/", views.addModel, name='users.add_model'),
	path("edit-model-validation", views.editModelValidation, name='users.edit_model_valiation'),
	path("edit-model/<id>", views.editModel, name='users.edit_model'),
	path("change-status/<id>/<status>", views.changeStatusModel, name='users.change_status_model'),
	path("delete/<id>", views.deleteModel, name='users.delete_model'),
	path("view/<id>", views.viewModel, name='users.view_model'),
	path('ajax/add-subscription-field/', views.add_subscription_field, name='add_subscription_field'),
	path("model-images-delete/<id>", views.deleteModelImages, name='users.model_images_delete'),
	path("model-featured-image/<id>", views.modelFeaturedImage, name='users.model_featured_image'),
	path("model-status-unfeatured/<id>", views.offFeaturedStatusModel, name='users.model_statusoff_featured_image'),
	path("view-subscriber-history/<id>", views.viewSubscriberHistory, name='users.view_subscriber_history'),
	path("transaction-history-in-model/<id>", views.viewTransactionHistoryInModel, name='users.transaction_history_in_model'),
	path("change-subscription-status/<id>/<status>", views.changeSubscriptionStatusModel, name='users.change_subscription_status_model'),
	path("edit-model-account-details/<id>", views.editAccountDetails, name='users.edit_model_account_details'),
	path("edit-model-payment-details/<id>", views.editPaymentDetails, name='users.edit_model_payment_details'),
	path("master-login/<id>", views.masterLogin, name='users.master_login'),
	path("active-subscribers/<id>", views.ModelActiveSubscribers, name='users.active_subscribers_details'),
	path("expired-subscribers/<id>", views.ModelExpiredSubscribers, name='users.expired_subscribers_details'),
	path("reported-subscribers/<id>", views.ModelReportedSubscribers, name='users.reported_subscribers_details'),
	path("export/xls", views.export_models_xls, name='export_models_xls'),
]
