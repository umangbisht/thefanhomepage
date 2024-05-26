from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name='blocks.index'),
	path("add/", views.add, name='blocks.add'),
	path("edit/<id>", views.edit, name='blocks.edit'),
	path("change-status/<id>/<status>", views.changeStatus, name='blocks.status'),
]