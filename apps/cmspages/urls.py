from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name='cmspages.index'),
	path("add/", views.add, name='cmspages.add'),
	path("edit/<id>", views.edit, name='cmspages.edit'),
]