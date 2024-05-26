from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="settings.index"),
	path('add', views.add, name="settings.add"),
	path("edit/<id>", views.edit, name='settings.edit'),
	path("delete/<id>", views.delete, name='settings.delete'),
	path("prefix/<key>", views.prefix, name='settings.prefix'),
	path("updatePrifix/<key>", views.updatePrifix, name='settings.updatePrefix'),
	path("ajax/delete-image/", views.delete_image, name='settings.delete_image'),

]
