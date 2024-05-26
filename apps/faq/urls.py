from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name='faq.index'),
	path("add/", views.add, name='faq.add'),
	path("edit/<id>", views.edit, name='faq.edit'),
	path("change-status/<id>/<status>", views.changeStatus, name='faq.status'),
]