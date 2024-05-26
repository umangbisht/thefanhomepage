from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("<dropdown_type>", views.index, name='dropdown-managers.index'),
	path("<dropdown_type>/add/", views.add, name='dropdown-managers.add'),
	path("<dropdown_type>/edit/<id>", views.edit, name='dropdown-managers.edit'),
	path("<dropdown_type>/change-status/<id>/<status>/", views.changeStatus, name='dropdown-managers-change-status'),
	path("<dropdown_type>/delete/<id>", views.deleteDropDown, name='dropdown-managers.delete'),
 
]