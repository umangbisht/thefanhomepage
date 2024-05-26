from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name="newsletters.index"),
	path('add', views.add, name="newsletters.add"),
	path("edit/<id>", views.edit, name='newsletters.edit'),
	path("delete/<id>", views.deleteNewsletter, name='newsletters.delete_newsletter'),
	path("newsletters-subscribers", views.subscribers, name='newsletters.subscribers'),
	path("delete-subscriber/<id>", views.deleteSubscriber, name='newsletters.delete_subscriber'),
	path('add-newsletter-subscriber', views.add_newsletter_subscriber, name="newsletters.add_newsletter_subscriber"),
	path('scheduled-newsletters/', views.scheduled_newsletter, name="newsletters.scheduled_newsletter"),
	path('schedule-newsletter/<id>', views.sendScheduledNewsletter, name="newsletters.sendScheduledNewsletter"),
	path('edit-schedule-newsletter/<id>', views.editScheduledNewsletter, name="newsletters.editScheduledNewsletter"),
	path('schedule-newsletter-delete/<id>', views.deleteScheduledNewsletter, name="newsletters.deleteScheduledNewsletter"),
	path('scheduled-newsletters/status/<id>', views.statusScheduledEmail, name="newsletters.statusScheduledEmail"),
	path("delete-status-email/<scheduled_newsletter_id>/<id>", views.deleteStatusEmailScheduledNewsletter, name='newsletters.delete_status_email_scheduled_newsletter'),

]
