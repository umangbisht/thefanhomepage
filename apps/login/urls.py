from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name="login"),
    path('', views.logout_user, name="logout_user"),
    path('profile_user', views.profile_user, name="login.profile_user"),
  

]