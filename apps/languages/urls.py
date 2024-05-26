from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name="languages.index"),
	path('add', views.add, name="languages.add"),
	path("edit/<id>", views.edit, name='languages.edit'),
	path("status/<id>/<status>", views.changeStatus, name='languages.status'),	
]
