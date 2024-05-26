from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name="emailtemplates.index"),
	path('add', views.add, name="emailtemplates.add"),
	path("edit/<id>", views.edit, name='emailtemplates.edit'),
	path('ajax/get-constant/', views.get_constant, name='get_constant'),
	
	
]
