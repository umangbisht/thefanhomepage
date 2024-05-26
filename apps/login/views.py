from django.shortcuts import render, redirect,HttpResponse
from django.contrib.auth import authenticate, login as dj_login
from django.contrib.auth import logout
from apps.users.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import re
# Create your views here.
def login(request):
	#return  HttpResponse("ds")
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']

		user = authenticate(username=username, password=password)
		if user is not None:
			if user.user_role_id == 1:
				dj_login(request, user)
				messages.success(request, "Congratulations, you have successfully sign in!")
				return redirect("/dashboard/")
				
				
			messages.error(request, "Invalid username and password.")
			return redirect("/login/")
				
		messages.error(request, "Invalid username and password.")	
		return redirect("/login/")
		
	return render(request,"login/login.html")
	
	

	
def forget_password(request):
	return render(request,"login/forget_password.html")
	
def reset_password(request):
	return render(request,"login/reset_password.html")
	
def logout_user(request):
	logout(request)
	messages.success(request, "You have loggout successfully")
	return redirect("/admin/login/") 

def profile_user(request):
	#return HttpResponse("fdf")
	userDetail	=User.objects.filter(user_role_id=1).first()
		
	if not userDetail:
		return redirect('/dashboard/')

	form				=	userDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST["username"] == "":
			validationErrors["username"]	=	"The username field is required."
		
		
	
		if request.POST["first_name"].strip() == "":
			validationErrors["first_name"]	=	"The first name field is required."

		# if request.POST["password"] == "":
			# validationErrors["password"]	=	"The password field is required."

		if request.POST["password"] != "" and  request.POST["confirm_password"] == "":
			validationErrors["confirm_password"]	=	"The confirm password field is required."
		else:
			if request.POST["password"] != "" and request.POST["confirm_password"] != request.POST["password"]:
				validationErrors["confirm_password"]	=	"The confirm password and password field is does not match."

		

		if not validationErrors:

			users				=	User.objects.filter(user_role_id=1).first()
			users.first_name	=	request.POST["first_name"]
			users.last_name		=	request.POST["last_name"]
			users.username		=	request.POST["username"]
			
			if request.POST["password"]:
				users.password		=	make_password(request.POST["password"])
			users.save()
			messages.success(request,"User  profile has been  updated successfully.")
			return redirect('/dashboard/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"userDetail":userDetail
	}
	return render(request,"login/profile.html",context)