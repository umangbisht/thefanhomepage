from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,AccountDetails,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,LastPayoutDate,UserSubscriptionPlan, TransactionHistory, ModelNotificationSetting, AdditionalLinks,Upload
from apps.newsletters.models import NewsletterSubscriber
from apps.dropdownmanger.models import DropDownManager 
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
from django.template.loader import get_template
import os
import datetime
from django.db.models import Count,Sum
import json
from datetime import  date,timedelta
from django.core.mail import send_mail, BadHeaderError,EmailMessage,EmailMultiAlternatives
from django.core.files.storage import FileSystemStorage
import re
from django.utils.html import strip_tags
from django.template import Context
#from django.shortcuts import render_to_response
from django.conf import settings
from PIL import Image
import decimal
from decimal import Decimal
import random
from django.db.models import Q
from django.http import JsonResponse
import xlwt
from django.http import HttpResponse
# from django.contrib.auth.models import User
import time

# Create your views here.
VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

@login_required(login_url='/login')
def indexSubscriber(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = User.objects.filter(is_deleted=0)
	totalModels = User.objects.filter(is_deleted=0).filter(user_role_id=3)
	# if request.GET.get('model_name'):
	# 	model_name= request.GET.get('model_name').strip()
	# 	DB = DB.filter(model_name__icontains= model_name)
	countSignupFromHome	=	User.objects.filter(is_deleted=0).filter(user_role_id=2).filter(signup_from_id=None).count()
	countSignupFromProfile	=	User.objects.filter(is_deleted=0).filter(user_role_id=2).filter(~Q(signup_from_id=None)).count()

	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	if request.GET.get("model_name") == "homepage":
		DB = DB.filter(signup_from_id=None)

	if request.GET.get('model_name') and request.GET.get('model_name') !='homepage':
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(signup_from_id=model_name)

	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")	

	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=2).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=2).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)

	context		=	{
		'results': results,
		'totalModels':totalModels,
		'page': page,
		'countSignupFromHome':countSignupFromHome,
		'countSignupFromProfile':countSignupFromProfile,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat,
	}
	return render(request, "subscribers/index.html",context)

@login_required(login_url='/login')
def indexDeletedSubscriber(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = User.objects.filter(is_deleted=1)
	totalModels = User.objects.filter(is_deleted=0).filter(user_role_id=3)
	# if request.GET.get('model_name'):
	# 	model_name= request.GET.get('model_name').strip()
	# 	DB = DB.filter(model_name__icontains= model_name) 
	# countSignupFromHome	=	User.objects.filter(is_deleted=0).filter(user_role_id=2).filter(signup_from_id=None).count()
	# countSignupFromProfile	=	User.objects.filter(is_deleted=0).filter(user_role_id=2).filter(~Q(signup_from_id=None)).count()

	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	if request.GET.get("model_name") == "homepage":
		DB = DB.filter(signup_from_id=None)

	if request.GET.get('model_name') and request.GET.get('model_name') !='homepage':
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(signup_from_id=model_name)

	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")	

	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=2).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=2).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)

	context		=	{
		'results': results,
		'totalModels':totalModels,
		'page': page,
		# 'countSignupFromHome':countSignupFromHome,
		# 'countSignupFromProfile':countSignupFromProfile,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat,
	}
	return render(request, "subscribers/index_deleted.html",context)

# add client
@login_required(login_url='/login/')
def addSubscriber(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST

		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required"
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid"

		if request.POST["account_name"].strip() == "":
			validationErrors["account_name"]	=	"The account name field is required."
			
		if request.POST["password"] == "" or  request.POST["password"] == None:
			validationErrors["password"]	=	"The password field is required."
		else:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."

		if request.POST["confirm_password"] == "" and  request.POST["confirm_password"] == "":
			validationErrors["confirm_password"]	=	"The confirm password field is required."
		else:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["password"] != "" and request.POST["confirm_password"] != request.POST["password"]:
			validationErrors["confirm_password"]	=	"The confirm password and password field does not match."
				
		if not validationErrors:
			users						=	User()
			users.model_name			=	request.POST["account_name"]
			users.username				=	request.POST["email"]
			users.email					=	request.POST["email"]
			users.password				=	make_password(request.POST["password"])
			users.user_role_id			=	2
			
			users.save()

			user_id = users.id
			if user_id:
				ModelNotificationInfo									=	ModelNotificationSetting()
				ModelNotificationInfo.user_id 							= 	user_id
				ModelNotificationInfo.new_subscription_purchased 		= 	1
				ModelNotificationInfo.subscription_expires 				= 	1
				ModelNotificationInfo.received_tip 						= 	1
				ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
				ModelNotificationInfo.detects_login_unverified_device 	= 	1
				ModelNotificationInfo.detects_unsuccessful_login 		= 	1
				ModelNotificationInfo.save()
			
			messages.success(request,"Subscriber has been added successfully.")
			return redirect('/subscribers/')

	context		=	{
		"form":form,
		"errors":validationErrors
	}
	return render(request,"subscribers/add.html",context)
	
# edit client
@login_required(login_url='/login/')
def editSubscriber(request,id):
	userDetail	 = User.objects.filter(id=id).first()
	if not userDetail:
		return redirect('/dashboard/')

	form				=	userDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required"
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid"
				
		# if request.POST["account_name"].strip() == "":
		# 	validationErrors["account_name"]	=	"The account name field is required."

		if request.POST["password"] != "" or request.POST["password"] != None:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."
		if request.POST["confirm_password"] != "" or request.POST["confirm_password"] != None:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["password"] != "" and request.POST["confirm_password"] != request.POST["password"]:
			validationErrors["confirm_password"]	=	"The confirm password and password field does not match."

		if not validationErrors:

			users						=	User.objects.filter(id=id).first()
			users.model_name			=	request.POST["account_name"]
			users.username				=	request.POST["email"]
			users.email					=	request.POST["email"]
			if request.POST["password"]:
				users.password		=	make_password(request.POST["password"])
			users.save()
			messages.success(request,"Subscriber has been updated successfully.")
			return redirect('/subscribers/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"userDetail":userDetail
	}
	return render(request,"subscribers/edit.html",context)

@login_required(login_url='/login/')
def viewSubscriber(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	userDetail	 = User.objects.filter(id=id).first()
	contaxt={
	"userDetail":userDetail,
	"datetimeFormat":datetimeFormat
	}
	return render(request,"subscribers/view.html",contaxt)


@login_required(login_url='/login/')
def changeStatusSubscriber(request,id,status):
    userDetail = User.objects.filter(id=id).first()
    if status=="1":
        userDetail.is_active= 1
        userDetail.save()
        message = 'Subscriber has been Activated successfully.' 
    else:
        userDetail.is_active= 0
        userDetail.save()
        message = 'Subscriber has been Deactivated successfully.' 
    messages.success(request,message) 
    return redirect('/subscribers/')

@login_required(login_url='/login/')
def changeApproveStatus(request,id,status):
    userDetail = User.objects.filter(id=id).first()
    if status=="1":
        userDetail.is_approved= 1
        userDetail.save()
        message = 'Model has been approved successfully.' 
    else:
        userDetail.is_approved= 2
        userDetail.save()
        message = 'Model has been rejected successfully.' 
    messages.success(request,message) 
    return redirect('/models/')



	
@login_required(login_url='/login/')
def deleteSubscriber(request,id):
	newsletterSubscriber = NewsletterSubscriber.objects.filter(user_id=id).first()
	if newsletterSubscriber:
		newsletterSubscriber.delete()
	users = User.objects.filter(id=id).first()
	users.email			=	users.email+'_deleted_'+id
	users.username		=	users.username+'_deleted_'+id
	users.is_deleted	=	1
	users.save()
	messages.success(request,"Subscriber has been deleted successfully.")
	return redirect('/subscribers/')
	
	
	
#model functions start 	

@login_required(login_url='/login')
def indexModel(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = User.objects.filter(is_deleted=0).filter(user_role_id=3)
	categories = ''
	if request.GET.get('first_name'):
		first_name= request.GET.get('first_name').strip()
		DB = DB.filter(first_name__icontains= first_name)
		
	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model_name__icontains= model_name)
		
	if request.GET.get('last_name'):
		last_name= request.GET.get('last_name').strip()
		DB = DB.filter(last_name__icontains= last_name)
	
	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	
	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('gender'):
		DB = DB.filter(gender=request.GET.get('gender'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
		
	if request.GET.getlist('categories'):
		categories 			= request.GET.getlist('categories')
		categoriesModelId 	= ModelCategories.objects.filter(dropdown_manager_id__in=categories).values("user_id");
		DB 		= DB.filter(id__in=categoriesModelId)		

	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=3).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=3).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")

	
	context		=	{
		'results': results,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "models/index.html",context)

@login_required(login_url='/login')
def indexDeletedModel(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = User.objects.filter(is_deleted=1).filter(user_role_id=3)
	categories = ''
	if request.GET.get('first_name'):
		first_name= request.GET.get('first_name').strip()
		DB = DB.filter(first_name__icontains= first_name)
		
	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model_name__icontains= model_name)
		
	if request.GET.get('last_name'):
		last_name= request.GET.get('last_name').strip()
		DB = DB.filter(last_name__icontains= last_name)
	
	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	
	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('gender'):
		DB = DB.filter(gender=request.GET.get('gender'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
		
	if request.GET.getlist('categories'):
		categories 			= request.GET.getlist('categories')
		categoriesModelId 	= ModelCategories.objects.filter(dropdown_manager_id__in=categories).values("user_id");
		DB 		= DB.filter(id__in=categoriesModelId)		

	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=3).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=3).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")

	
	context		=	{
		'results': results,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "models/index_deleted.html",context)

# add client
@login_required(login_url='/login/')
def addModelValidation(request):		
	form				=	{}
	validationErrors	=	{}
	sub_type_list	=	["snapchat","private_feed","whatsapp","instagram","tips"]
	is_required_validation	=	1
	if request.method	==	"POST":				
		if request.POST["email"] != "":
			form['email'] 			= request.POST['email']
			
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST["email"] and not re.match(EMAIL_REGEX, request.POST["email"]):
				validationErrors["email"]	=	"This email is not valid."
				
			if User.objects.filter(email=request.POST["email"]).exists():
				validationErrors["email"]	=	"This email is already exists."	
		else:
			validationErrors["email"]	=	"The email field is required."

		if request.POST["first_name"].strip() == "":
			validationErrors["first_name"]	=	"The first name field is required."
		else:
			form['first_name'] 			= request.POST['first_name']
			
		if request.POST["last_name"].strip() == "":
			validationErrors["last_name"]	=	"The last name field is required."
		else:
			form['last_name'] 			= request.POST['last_name']
		
		if request.POST["password"] == "":
			validationErrors["password"]	=	"The password field is required."
		else:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."

		if request.POST["confirm_password"] == "":
			validationErrors["confirm_password"]	=	"The confirm password field is required."
		else:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["password"] != "" and request.POST["confirm_password"] != request.POST["password"]:
			validationErrors["confirm_password"]	=	"The confirm password and password field does not match."

				
		if request.POST["gender"].strip() == "":
			validationErrors["gender"]	=	"The gender field is required."	
		else:
			form['gender'] 			= request.POST['gender']		
			
		if request.POST["date_of_birth"].strip() == "":
			validationErrors["date_of_birth"]	=	"The DOB field is required."
		else:
			form['date_of_birth'] 			= request.POST['date_of_birth']	
			
				
		if request.POST["country"].strip() == "":
			validationErrors["country"]	=	"The country field is required."
		else:
			form['country'] 			= request.POST['country']	
				
		if request.POST["address_line_1"].strip() == "":
			validationErrors["address_line_1"]	=	"The Address Line 1 field is required."
		else:
			form['address_line_1'] 			= request.POST['address_line_1']		
			
		if request.POST["city"].strip() == "":
			validationErrors["city"]	=	"The city field is required."
		else:
			form['city'] 			= request.POST['city']	
				
		if request.POST["postal_code"].strip() == "":
			validationErrors["postal_code"]	=	"The postal code field is required."
		else:
			form['postal_code'] 			= request.POST['postal_code']	
					
				
		if request.POST["model_name"].strip() == "":
			validationErrors["model_name"]	=	"The modal name field is required."
		else:
			form['model_name'] 			= request.POST['model_name']	
				
		if request.POST["bio"].strip() == "":
			validationErrors["bio"]	=	"The bio field is required."
		else:
			form['bio'] 			= request.POST['bio']		

		if request.POST.getlist('categories'):
			categories 					=   request.POST.getlist('categories')
			form['categories'] 			=   request.POST.getlist('categories')
		else:
			validationErrors["categories"]	=	"Please select Categories"
			
		if len(request.FILES) == 0:
			validationErrors["images"]	=	"Please select Image"
		# else:
			# images = request.FILES.getlist("images")
			# for imge in images:
				# file = imge.name
				# extension = file.split(".")[-1].lower()
				# if not extension in VALID_IMAGE_EXTENSIONS:
					# validationErrors["images"]	=	"This is not a valid image. Please upload a valid image."

		# if request.FILES.get("government_id_front_image") == None:
			# validationErrors["gifi"]	=	"Please select government id front image"

		# if request.FILES.get("government_id_back_image") == None:
			# validationErrors["gibi"]	=	"Please select government id back image"

		# if request.FILES.get("photo_next_to_id") == None:
			# validationErrors["pnti"]	=	"Please select photo next to id"

		# if request.FILES.get("photo_next_to_id_with_dated_paper") == None:
			# validationErrors["pntiwdp"]	=	"Please select photo next to id with dated paper"

		# if request.FILES.get('featured_image') ==None or request.FILES.get("featured_image") == "":
		# 	validationErrors["featured_image"]	=	"Please select featured image"
		# else:
		# 	featured_image = request.FILES.get("featured_image")
		# 	file = featured_image.name
		# 	extension = file.split(".")[-1].lower()
		# 	if not extension in VALID_IMAGE_EXTENSIONS:
		# 		validationErrors["featured_image"]	=	"This is not a valid image. Please upload a valid featured image."

	
		regex = re.compile(r'https?://(?:www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*|(www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*')
			
		if request.POST["private_snapchat_link"] !='' and not re.match(regex, request.POST["private_snapchat_link"].strip()):
			validationErrors["private_snapchat_link"]	=	"Please enter valid url."
		form['private_snapchat_link'] 			= request.POST['private_snapchat_link']	
				
		if request.POST["public_snapchat_link"] !='' and not re.match(regex, request.POST["public_snapchat_link"].strip()):
			validationErrors["public_snapchat_link"]	=	"Please enter valid url."
		form['public_snapchat_link'] 			= request.POST['public_snapchat_link']
					
		if request.POST["public_instagram_link"] !='' and not re.match(regex, request.POST["public_instagram_link"].strip()):
			validationErrors["public_instagram_link"]	=	"Please enter valid url."
		form['public_instagram_link'] 			= request.POST['public_instagram_link']
			
		if request.POST["twitter_link"] !='' and not re.match(regex, request.POST["twitter_link"].strip()):
			validationErrors["twitter_link"]	=	"Please enter valid url."
		form['twitter_link'] 			= request.POST['twitter_link']
			
		if request.POST["youtube_link"] !='' and not re.match(regex, request.POST["youtube_link"].strip()):
			validationErrors["youtube_link"]	=	"Please enter valid url."
		form['youtube_link'] 			= request.POST['youtube_link']
			
		if request.POST["amazon_wishlist_link"] !='' and not re.match(regex, request.POST["amazon_wishlist_link"].strip()):
			validationErrors["amazon_wishlist_link"]	=	"Please enter valid url."
		form['amazon_wishlist_link'] 			= request.POST['amazon_wishlist_link']
		
		if request.POST["youtube_video_url"] !='' and not re.match(regex, request.POST["youtube_video_url"].strip()):
			validationErrors["youtube_video_url"]	=	"Please enter valid url."
		form['youtube_video_url'] 			= request.POST['youtube_video_url']

		# if request.POST.get('subscription[snapchat][is_enabled]') == '0' and request.POST.get('subscription[private_feed][is_enabled]') == '0' and request.POST.get('subscription[whatsapp][is_enabled]') =='0' and request.POST.get('subscription[instagram][is_enabled]') == '0' and request.POST.get('subscription[tips][is_enabled]') == '0':
		# 	validationErrors["subscription_offer"]	=	"Please Select any one subscription offer."
			
		
		
		form['previous_first_name'] 			= request.POST['previous_first_name']
		form['previous_last_name'] 				= request.POST['previous_last_name']
		form['address_line_2'] 					= request.POST['address_line_2']
					
			
		if not validationErrors:
			is_required_validation	=	0
			
	context		=	{
		"is_required_validation":is_required_validation,
		"errors":validationErrors,
	}
	return JsonResponse(context)

	
@login_required(login_url='/login/')
def editModelValidation(request):
	multi_orientation = []
	is_required_validation	=	1
	id	=	request.POST["model_id"];
	userDetail	 = User.objects.filter(id=id).first()
	if not userDetail:
		return redirect('/dashboard/')
		
	form				=	userDetail
	validationErrors	=	{}
	sub_type_list	=	["snapchat","private_feed","whatsapp","instagram","tips"]
	data				=	request.POST
	if request.method	==	"POST":
		form				=	{}
		if request.POST["email"] != "":
			form['email'] 			= request.POST['email']
			
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST["email"] and not re.match(EMAIL_REGEX, request.POST["email"]):
				validationErrors["email"]	=	"This email is not valid."
				
			if User.objects.filter(email=request.POST["email"]).exclude(id=id).exists():
				validationErrors["email"]	=	"This email is already exists."	
		else:
			validationErrors["email"]	=	"The email field is required."
		if request.POST["first_name"].strip() == "":
			validationErrors["first_name"]	=	"The first name field is required."
		else:
			form['first_name'] 			= request.POST['first_name']
			
		if request.POST["last_name"].strip() == "":
			validationErrors["last_name"]	=	"The last name field is required."
		else:
			form['last_name'] 			= request.POST['last_name']
		
		if request.POST["password"] != "" or request.POST["password"] != None:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."
		if request.POST["confirm_password"] != "" or request.POST["confirm_password"] != None:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["confirm_password"] != "":
			if request.POST["confirm_password"] != request.POST["password"]:
				validationErrors["confirm_password"]	=	"The confirm password and password field does not match."
			
				
		if request.POST["gender"].strip() == "":
			validationErrors["gender"]	=	"The gender field is required."	
		else:
			form['gender'] 			= request.POST['gender']		
			
		if request.POST["date_of_birth"].strip() == "":
			validationErrors["date_of_birth"]	=	"The DOB field is required."
		else:
			form['date_of_birth'] 			= request.POST['date_of_birth']	

		if request.POST["country"].strip() == "":
			validationErrors["country"]	=	"The country field is required."
		else:
			form['country'] 			= request.POST['country']	
				
		if request.POST["address_line_1"].strip() == "":
			validationErrors["address_line_1"]	=	"The Address Line 1 field is required."
		else:
			form['address_line_1'] 			= request.POST['address_line_1']		
			
		if request.POST["city"].strip() == "":
			validationErrors["city"]	=	"The city field is required."
		else:
			form['city'] 			= request.POST['city']	
				
		if request.POST["postal_code"].strip() == "":
			validationErrors["postal_code"]	=	"The postal code field is required."
		else:
			form['postal_code'] 			= request.POST['postal_code']	
					
				
		if request.POST["model_name"].strip() == "":
			validationErrors["model_name"]	=	"The modal name field is required."
		else:
			form['model_name'] 			= request.POST['model_name']	
				
		if request.POST["bio"].strip() == "":
			validationErrors["bio"]	=	"The bio field is required."
		else:
			form['bio'] 			= request.POST['bio']		

				
		# if request.POST["government_id_number"].strip() == "":
			# validationErrors["government_id_number"]	=	"The Government Id Number field is required."
		# else:
			# form['government_id_number'] 			= request.POST['government_id_number']	
			
			
		# if request.POST["government_id_expiration_date"].strip() == "":
			# validationErrors["government_id_expiration_date"]	=	"The Government Id Expiration Date field is required."
		# else:
			# form['government_id_expiration_date'] 			= request.POST['government_id_expiration_date']	
			

			
		if request.POST.getlist('categories'):
			categories 					=   request.POST.getlist('categories')
			form['categories'] 			=   request.POST.getlist('categories')
			selectedCategories 			=   request.POST.getlist('categories')
		else:
			validationErrors["categories"]	=	"Please select Categories"
			
		if len(request.FILES) != 0:
			images = request.FILES.getlist("images")
			
			for imge in images:
				file = imge.name
				extension = file.split(".")[-1].lower()
				if not extension in VALID_IMAGE_EXTENSIONS:
					validationErrors["images"]	=	"This is not an valid image. Please upload a valid image."
		else:
			images = ''

			
				
		regex = re.compile(r'https?://(?:www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*|(www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*')
			
		if request.POST["private_snapchat_link"] !='' and not re.match(regex, request.POST["private_snapchat_link"].strip()):
			validationErrors["private_snapchat_link"]	=	"Please enter valid url."
		form['private_snapchat_link'] 			= request.POST['private_snapchat_link']	
				
		if request.POST["public_snapchat_link"] !='' and not re.match(regex, request.POST["public_snapchat_link"].strip()):
			validationErrors["public_snapchat_link"]	=	"Please enter valid url."
		form['public_snapchat_link'] 			= request.POST['public_snapchat_link']
					
		if request.POST["public_instagram_link"] !='' and not re.match(regex, request.POST["public_instagram_link"].strip()):
			validationErrors["public_instagram_link"]	=	"Please enter valid url."
		form['public_instagram_link'] 			= request.POST['public_instagram_link']
			
		if request.POST["twitter_link"] !='' and not re.match(regex, request.POST["twitter_link"].strip()):
			validationErrors["twitter_link"]	=	"Please enter valid url."
		form['twitter_link'] 			= request.POST['twitter_link']
			
		if request.POST["youtube_link"] !='' and not re.match(regex, request.POST["youtube_link"].strip()):
			validationErrors["youtube_link"]	=	"Please enter valid url."
		form['youtube_link'] 			= request.POST['youtube_link']
			
		if request.POST["amazon_wishlist_link"] !='' and not re.match(regex, request.POST["amazon_wishlist_link"].strip()):
			validationErrors["amazon_wishlist_link"]	=	"Please enter valid url."
		form['amazon_wishlist_link'] 			= request.POST['amazon_wishlist_link']
		


		if request.POST["youtube_video_url"] !='' and not re.match(regex, request.POST["youtube_video_url"].strip()):
			validationErrors["youtube_video_url"]	=	"Please enter valid url."
		form['youtube_video_url'] 			= request.POST['youtube_video_url']	

		

		if not validationErrors:
			is_required_validation	=	0
			
	context		=	{
		"is_required_validation":is_required_validation,
		"errors":validationErrors,
	}
	return JsonResponse(context)
	
@login_required(login_url='/login/')
def addModel(request):		
	form				=	{}
	validationErrors	=	{}
	sub_type_list	=	["snapchat","private_feed","whatsapp","instagram","tips"]
	if request.method	==	"POST":				
		if request.POST["email"] != "":
			form['email'] 			= request.POST['email']
			
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST["email"] and not re.match(EMAIL_REGEX, request.POST["email"]):
				validationErrors["email"]	=	"This email is not valid."
				
			if User.objects.filter(email=request.POST["email"]).exists():
				validationErrors["email"]	=	"This email is already exists."	
		else:
			validationErrors["email"]	=	"The email field is required."

		if request.POST["first_name"].strip() == "":
			validationErrors["first_name"]	=	"The first name field is required."
		else:
			form['first_name'] 			= request.POST['first_name']
			
		if request.POST["last_name"].strip() == "":
			validationErrors["last_name"]	=	"The last name field is required."
		else:
			form['last_name'] 			= request.POST['last_name']
		
		if request.POST["password"] == "":
			validationErrors["password"]	=	"The password field is required."
		else:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."

		if request.POST["confirm_password"] == "":
			validationErrors["confirm_password"]	=	"The confirm password field is required."
		else:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["password"] != "" and request.POST["confirm_password"] != request.POST["password"]:
			validationErrors["confirm_password"]	=	"The confirm password and password field does not match."

				
		if request.POST["gender"].strip() == "":
			validationErrors["gender"]	=	"The gender field is required."	
		else:
			form['gender'] 			= request.POST['gender']		
			
		if request.POST["date_of_birth"].strip() == "":
			validationErrors["date_of_birth"]	=	"The DOB field is required."
		else:
			form['date_of_birth'] 			= request.POST['date_of_birth']	
			
				
		if request.POST["country"].strip() == "":
			validationErrors["country"]	=	"The country field is required."
		else:
			form['country'] 			= request.POST['country']	
				
		if request.POST["address_line_1"].strip() == "":
			validationErrors["address_line_1"]	=	"The Address Line 1 field is required."
		else:
			form['address_line_1'] 			= request.POST['address_line_1']		
			
		if request.POST["city"].strip() == "":
			validationErrors["city"]	=	"The city field is required."
		else:
			form['city'] 			= request.POST['city']	
				
		if request.POST["postal_code"].strip() == "":
			validationErrors["postal_code"]	=	"The postal code field is required."
		else:
			form['postal_code'] 			= request.POST['postal_code']	
						
				
		if request.POST["model_name"].strip() == "":
			validationErrors["model_name"]	=	"The modal name field is required."
		else:
			form['model_name'] 			= request.POST['model_name']	
				
		if request.POST["bio"].strip() == "":
			validationErrors["bio"]	=	"The bio field is required."
		else:
			form['bio'] 			= request.POST['bio']		

		if request.POST.getlist('categories'):
			categories 					=   request.POST.getlist('categories')
			form['categories'] 			=   request.POST.getlist('categories')
		else:
			validationErrors["categories"]	=	"Please select Categories"
			
		if len(request.FILES) == 0:
			validationErrors["images"]	=	"Please select Image"
		# else:
			# images = request.FILES.getlist("images")
			# for imge in images:
				# file = imge.name
				# extension = file.split(".")[-1].lower()
				# if not extension in VALID_IMAGE_EXTENSIONS:
					# validationErrors["images"]	=	"This is not a valid image. Please upload a valid image."

		# if request.FILES.get("government_id_front_image") == None:
			# validationErrors["gifi"]	=	"Please select government id front image"

		# if request.FILES.get("government_id_back_image") == None:
			# validationErrors["gibi"]	=	"Please select government id back image"

		# if request.FILES.get("photo_next_to_id") == None:
			# validationErrors["pnti"]	=	"Please select photo next to id"

		# if request.FILES.get("photo_next_to_id_with_dated_paper") == None:
			# validationErrors["pntiwdp"]	=	"Please select photo next to id with dated paper"

		# if request.FILES.get('featured_image') ==None or request.FILES.get("featured_image") == "":
		# 	validationErrors["featured_image"]	=	"Please select featured image"
		# else:
		# 	featured_image = request.FILES.get("featured_image")
		# 	file = featured_image.name
		# 	extension = file.split(".")[-1].lower()
		# 	if not extension in VALID_IMAGE_EXTENSIONS:
		# 		validationErrors["featured_image"]	=	"This is not a valid image. Please upload a valid featured image."

	
		regex = re.compile(r'https?://(?:www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*|(www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*')
			
		if request.POST["private_snapchat_link"] !='' and not re.match(regex, request.POST["private_snapchat_link"].strip()):
			validationErrors["private_snapchat_link"]	=	"Please enter valid url."
		form['private_snapchat_link'] 			= request.POST['private_snapchat_link']	
				
		if request.POST["public_snapchat_link"] !='' and not re.match(regex, request.POST["public_snapchat_link"].strip()):
			validationErrors["public_snapchat_link"]	=	"Please enter valid url."
		form['public_snapchat_link'] 			= request.POST['public_snapchat_link']
					
		if request.POST["public_instagram_link"] !='' and not re.match(regex, request.POST["public_instagram_link"].strip()):
			validationErrors["public_instagram_link"]	=	"Please enter valid url."
		form['public_instagram_link'] 			= request.POST['public_instagram_link']
			
		if request.POST["twitter_link"] !='' and not re.match(regex, request.POST["twitter_link"].strip()):
			validationErrors["twitter_link"]	=	"Please enter valid url."
		form['twitter_link'] 			= request.POST['twitter_link']
			
		if request.POST["youtube_link"] !='' and not re.match(regex, request.POST["youtube_link"].strip()):
			validationErrors["youtube_link"]	=	"Please enter valid url."
		form['youtube_link'] 			= request.POST['youtube_link']
			
		if request.POST["amazon_wishlist_link"] !='' and not re.match(regex, request.POST["amazon_wishlist_link"].strip()):
			validationErrors["amazon_wishlist_link"]	=	"Please enter valid url."
		form['amazon_wishlist_link'] 			= request.POST['amazon_wishlist_link']
		
		if request.POST["youtube_video_url"] !='' and not re.match(regex, request.POST["youtube_video_url"].strip()):
			validationErrors["youtube_video_url"]	=	"Please enter valid url."
		form['youtube_video_url'] 			= request.POST['youtube_video_url']

		# if request.POST.get('subscription[snapchat][is_enabled]') == '0' and request.POST.get('subscription[private_feed][is_enabled]') == '0' and request.POST.get('subscription[whatsapp][is_enabled]') =='0' and request.POST.get('subscription[instagram][is_enabled]') == '0' and request.POST.get('subscription[tips][is_enabled]') == '0':
		# 	validationErrors["subscription_offer"]	=	"Please Select any one subscription offer."
			
		
		
		form['previous_first_name'] 			= request.POST['previous_first_name']
		form['previous_last_name'] 				= request.POST['previous_last_name']
		form['address_line_2'] 					= request.POST['address_line_2']
					
				
		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year
			
			gifi_image  = ''
			gibi_image  = ''
			pnti_image	= ''
			pntiwdp_image = ''
			if request.FILES.get("government_id_front_image") != "" and request.FILES.get("government_id_front_image"):
				gifiFile = request.FILES.get("government_id_front_image")
				filename = gifiFile.name.split(".")[0].lower()
				extension = gifiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gifiFile, "model_images/"+gifi_image)
				
			if request.FILES.get("government_id_back_image") != "" and request.FILES.get("government_id_back_image"):
				gibiFile = request.FILES.get("government_id_back_image")
				filename = gibiFile.name.split(".")[0].lower()
				extension = gibiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gibiFile, "model_images/"+gibi_image)
				
			if request.FILES.get("photo_next_to_id") != "" and request.FILES.get("photo_next_to_id"):
				pntiFile = request.FILES.get("photo_next_to_id")
				filename = pntiFile.name.split(".")[0].lower()
				extension = pntiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiFile, "model_images/"+pnti_image)
				
			if request.FILES.get("photo_next_to_id_with_dated_paper") != "" and request.FILES.get("photo_next_to_id_with_dated_paper"):
				pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
				filename = pntiwdpFile.name.split(".")[0].lower()
				extension = pntiwdpFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension	
				pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiwdpFile, "model_images/"+pntiwdp_image)
			
			
			totelModels = User.objects.filter(is_approved=1).filter(is_verified=1).count()
			
			slug = (request.POST.get("last_name","")).lower()
			users								=	User()
			users.first_name					=	request.POST.get("first_name","")
			users.last_name						=	request.POST.get("last_name","")
			users.slug							=	slug
			users.username						=	request.POST.get("email","")
			users.email							=	request.POST.get("email","")
			users.previous_first_name			=	request.POST.get("previous_first_name","")
			users.previous_last_name			=	request.POST.get("previous_last_name","")
			users.date_of_birth					=	request.POST.get("date_of_birth","")
			users.gender						=	request.POST.get("gender","")
			users.country						=	request.POST.get("country","")
			users.address_line_1				=	request.POST.get("address_line_1","")
			users.address_line_2				=	request.POST.get("address_line_2","")
			users.city							=	request.POST.get("city","")
			users.postal_code					=	request.POST.get("postal_code","")
			users.skype_number					=	request.POST.get("skype_number","")
			users.model_name					=	request.POST.get("model_name","")
			users.bio							=	request.POST.get("bio","")
			users.private_snapchat_link			=	request.POST.get("private_snapchat_link","")
			users.public_snapchat_link			=	request.POST.get("public_snapchat_link","")
			users.public_instagram_link			=	request.POST.get("public_instagram_link","")
			users.twitter_link					=	request.POST.get("twitter_link","")
			users.youtube_link					=	request.POST.get("youtube_link","")
			users.amazon_wishlist_link			=	request.POST.get("amazon_wishlist_link","")
			users.age							=	request.POST.get("age","")
			users.from_date						=	request.POST.get("from_date","")
			users.height						=	request.POST.get("height","")
			users.weight						=	request.POST.get("weight","")
			users.hair							=	request.POST.get("hair","")
			users.eyes							=	request.POST.get("eyes","")
			users.youtube_video_url				=	request.POST.get("youtube_video_url","")
			users.password						=	make_password(request.POST.get("password",""))
			users.user_role_id					=	3
			users.government_id_number			=	request.POST.get("government_id_number","")
			users.government_id_expiration_date	=	request.POST.get("government_id_expiration_date","")
			users.government_id_front_image		=	gifi_image
			users.government_id_back_image		=	gibi_image
			users.photo_next_to_id				=	pnti_image
			users.photo_next_to_id_with_dated_paper	=	pntiwdp_image
			users.default_currency				=	request.POST.get('default_currency')
			users.rank							=	totelModels
			users.rank_status					=	'stable'
			# users.featured_image				=	feat_image
			
			users.save()
			user_id = users.id
			if user_id:
				categories 					=   request.POST.getlist('categories')
				for category in categories:
					ModelCategoriesInfo							=	ModelCategories()
					ModelCategoriesInfo.dropdown_manager_id 		= 	category
					ModelCategoriesInfo.user_id 				= 	user_id
					ModelCategoriesInfo.save()

				ModelNotificationInfo									=	ModelNotificationSetting()
				ModelNotificationInfo.user_id 							= 	user_id
				ModelNotificationInfo.new_subscription_purchased 		= 	1
				ModelNotificationInfo.subscription_expires 				= 	1
				ModelNotificationInfo.received_tip 						= 	1
				ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
				ModelNotificationInfo.detects_login_unverified_device 	= 	1
				ModelNotificationInfo.detects_unsuccessful_login 		= 	1
				ModelNotificationInfo.save()

				images = request.FILES.getlist("images")
				for imge in images:	
					myfile = imge
					filename = myfile.name.split(".")[0].lower()
					extension = myfile.name.split(".")[-1].lower()
					newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
					model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
					
					ModelImagesInfo							=	ModelImages()
					ModelImagesInfo.image_url 				= 	model_image
					ModelImagesInfo.user_id 				= 	user_id
					ModelImagesInfo.save()

				discount_arr = []	
				for key in sub_type_list :
					if request.POST.get('subscription['+key+'][username]') :
						subUsername = request.POST.get('subscription['+key+'][username]')
					else:
						subUsername = ''
						
					if request.POST.get('subscription['+key+'][is_enabled]') :
						subIsEnabled = request.POST.get('subscription['+key+'][is_enabled]')
					else:
						subIsEnabled = 0
					
					lastUserId = user_id	
					subObj 					= ModelSubscriptions()
					subObj.user_id 			= lastUserId
					subObj.social_account 	= key
					subObj.username 		= subUsername
					subObj.is_enabled 		= subIsEnabled
					subObj.save()	
					subId = subObj.id
					today_date = str(datetime.datetime.today().date())+" 00:00:00"
					if int(subIsEnabled) == int(1):
						subPlanCount = request.POST.get('addmoreCount_'+key)
						if subPlanCount:
							if int(subPlanCount) > 0:
								for i in range(0, int(subPlanCount)):
									index = i+1;
									if request.POST.get('subscription['+key+'][plans]['+str(index)+'][plan_type]'):
										plan_type 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][plan_type]',"")
										offer_period_time 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_period_time]',"") 
										offer_period_type 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_period_type]',1) 
										price 					= request.POST.get('subscription['+key+'][plans]['+str(index)+'][price]',"") 
										currency 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][currency]',"") 
										offer_name 			= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_name]',"")
										description 			= request.POST.get('subscription['+key+'][plans]['+str(index)+'][description]',"")
										is_discount_enabled 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_discount_enabled]',0)
										discount 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][discount]',0) 
										is_permanent_discount 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_permanent_discount]',"") 
										from_discount_date 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][from_discount_date]',"") 
										to_discount_date 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][to_discount_date]',"") 
										is_apply_to_rebills 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_apply_to_rebills]',"") 
										
										if(is_discount_enabled == "on"):
											is_discount_enabled	=	1
										else:
											is_discount_enabled	=	0;
											
										if(is_permanent_discount == "on"):
											is_permanent_discount	=	1
										else:
											is_permanent_discount	=	0;
											
										if(is_apply_to_rebills == "on"):
											is_apply_to_rebills	=	1
										else:
											is_apply_to_rebills	=	0;
										
										
										price = isDecimal(price)
										discount = isDecimal(discount)
										is_discount_enabled = isNum(is_discount_enabled)
										is_permanent_discount = isNum(is_permanent_discount)
										is_apply_to_rebills = isNum(is_apply_to_rebills)
										
										if is_discount_enabled and decimal.Decimal(discount) > 0:
											discounted_price = decimal.Decimal(price)-((decimal.Decimal(price)*decimal.Decimal(discount))/100)
											discounted_price = round(float(discounted_price),2)
											is_discount_enabled = 1
											discount_arr.append(discount)
											discount_arr = [Decimal(x) for x in discount_arr]
										else:
											is_discount_enabled = 0
											discounted_price = price

											
										if is_permanent_discount:
											is_permanent_discount = 1
										else:
											is_permanent_discount = 0
											
										if is_apply_to_rebills:
											is_apply_to_rebills = 1
										else:
											is_apply_to_rebills = 0
											
										if plan_type == "recurring":	
											if from_discount_date != "" and from_discount_date > today_date:
												is_discount_enabled = 0	
										
										plansObj 									= ModelSubscriptionPlans()
										plansObj.user_id 							= lastUserId
										plansObj.model_subscription_id 				= subId
										plansObj.plan_type 							= plan_type
										plansObj.offer_period_time 					= offer_period_time
										plansObj.offer_period_type 					= offer_period_type
										plansObj.price 								= price
											
										plansObj.discounted_price 					= discounted_price
										plansObj.currency 							= request.POST.get('default_currency')
										plansObj.description 						= description
										plansObj.offer_name 						= offer_name
										plansObj.is_discount_enabled 				= is_discount_enabled
										
										plansObj.discount 						= discount
										plansObj.from_discount_date 			= from_discount_date
										
										if to_discount_date:
											plansObj.to_discount_date 					= to_discount_date
											
										plansObj.is_permanent_discount 				= is_permanent_discount
										plansObj.is_apply_to_rebills 				= is_apply_to_rebills
										plansObj.save()
										
										
										
										
				if len(discount_arr)!=0:
					high_discount	=	max(discount_arr)
					User.objects.filter(id=lastUserId).update(highest_discount=high_discount)
				else:
					discount_arr = []
					
				d = datetime.date.today()
				next_monday = next_weekday(d, 0)
				
				payObj 					= LastPayoutDate()
				payObj.model_id 		= lastUserId
				payObj.last_payout_date = next_monday+timedelta(days=14)
				payObj.save()
					
										
			#return HttpResponse(users)
			# email send 
			messages.success(request,"Model has been added successfully.")
			return redirect('/models/')
			
	defaultCurrency = settings.GLOBAL_CONSTANT_CURRENCY
	countriesArray	=	[]
	topRatedCountries1 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United Kingdom").values('id',"name")
	for country in topRatedCountries1:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	topRatedCountries2 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United States of America").values("name",'id')
	for country in topRatedCountries2:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	topRatedCountries3 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="Australia").values("name",'id')
	for country in topRatedCountries3:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	countryList	 = DropDownManager.objects.filter(dropdown_type='country').filter(is_active=1).exclude(name="Australia").exclude(name="United States of America").exclude(name="United Kingdom").all()
	for country in countryList:
		sub_data			=	{}
		sub_data['id']		=	country.id
		sub_data['name']	=	country.name
		countriesArray.append(sub_data)
	
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all()

	context		=	{
		"form":form,
		"errors":validationErrors,
		"countriesArray":countriesArray,
		"topRatedCountries1":topRatedCountries1,
		"topRatedCountries2":topRatedCountries2,
		"topRatedCountries3":topRatedCountries3,
		"categoryList":categoryList,
		"defaultCurrency":defaultCurrency
	}
	return render(request,"models/add.html",context)
	
def isNum(value):
	try:
		int(value)
		return value
	except ValueError:
		return 0
	
def isDecimal(value):
	try:
		decimal.Decimal(value)
		return round(decimal.Decimal(value),2)
	except:
		return 0
	
# edit client
@login_required(login_url='/login/')
def editModel(request,id):
	multi_orientation = []

	userDetail	 = User.objects.filter(id=id).first()
	if not userDetail:
		return redirect('/dashboard/')
	additionalLinks	=	AdditionalLinks.objects.filter(model_id = id).all()
	selectedCategories 	= ModelCategories.objects.filter(user_id=id).values_list('dropdown_manager_id',flat=True)
	selectedIamge 		= ModelImages.objects.filter(user_id=id).all().values('image_url','id')
	userImageDetail		= User.objects.filter(id=id).all().values('id','government_id_front_image','government_id_back_image','photo_next_to_id','photo_next_to_id_with_dated_paper','featured_image','is_featured')
	
	subcriptionDataSanpchat       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='snapchat').filter(is_deleted=0).first()
	if subcriptionDataSanpchat:
		planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcriptionDataSanpchat.id).filter(is_deleted=0).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","id");
		subcriptionDataSanpchat.plans = planData
		
	#print(subcriptionDataSanpchat.is_enabled)
	subcriptionDataPrivateFeed       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='private_feed').filter(is_deleted=0).first()
	if subcriptionDataPrivateFeed:
		planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcriptionDataPrivateFeed.id).filter(is_deleted=0).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","id");
		subcriptionDataPrivateFeed.plans = planData
			
	subcriptionDataWhatsapp       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='whatsapp').filter(is_deleted=0).first()
	if subcriptionDataWhatsapp:
		planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcriptionDataWhatsapp.id).filter(is_deleted=0).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","id");
		subcriptionDataWhatsapp.plans = planData	
		
	subcriptionDataInstagram       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='instagram').filter(is_deleted=0).first()
	if subcriptionDataInstagram:
		planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcriptionDataInstagram.id).filter(is_deleted=0).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","id");
		subcriptionDataInstagram.plans = planData
			
	subcriptionDataTips       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='tips').filter(is_deleted=0).first()
	
	
	form				=	userDetail
	validationErrors	=	{}
	sub_type_list	=	["snapchat","private_feed","whatsapp","instagram","tips"]
	data				=	request.POST

	if request.method	==	"POST":
		form				=	{}
		if request.POST["email"] != "":
			form['email'] 			= request.POST['email']
			
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST["email"] and not re.match(EMAIL_REGEX, request.POST["email"]):
				validationErrors["email"]	=	"This email is not valid."
				
			if User.objects.filter(email=request.POST["email"]).exclude(id=id).exists():
				validationErrors["email"]	=	"This email is already exists."	
		else:
			validationErrors["email"]	=	"The email field is required."
		if request.POST["first_name"].strip() == "":
			validationErrors["first_name"]	=	"The first name field is required."
		else:
			form['first_name'] 			= request.POST['first_name']
			
		if request.POST["last_name"].strip() == "":
			validationErrors["last_name"]	=	"The last name field is required."
		else:
			form['last_name'] 			= request.POST['last_name']
		
		if request.POST["password"] != "" or request.POST["password"] != None:
			lengthPass	=	len(request.POST["password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["password"]	=	"The password should contains atleast 8 digits."
		if request.POST["confirm_password"] != "" or request.POST["confirm_password"] != None:
			lengthPass	=	len(request.POST["confirm_password"])
			if lengthPass < 8 and lengthPass > 0:
				validationErrors["confirm_password"]	=	"The confirm password should contains atleast 8 digits."

		if request.POST["confirm_password"] != "":
			if request.POST["confirm_password"] != request.POST["password"]:
				validationErrors["confirm_password"]	=	"The confirm password and password field does not match."
			
				
		if request.POST["gender"].strip() == "":
			validationErrors["gender"]	=	"The gender field is required."	
		else:
			form['gender'] 			= request.POST['gender']		
			
		if request.POST["date_of_birth"].strip() == "":
			validationErrors["date_of_birth"]	=	"The DOB field is required."
		else:
			form['date_of_birth'] 			= request.POST['date_of_birth']	

		if request.POST["country"].strip() == "":
			validationErrors["country"]	=	"The country field is required."
		else:
			form['country'] 			= request.POST['country']	
				
		if request.POST["address_line_1"].strip() == "":
			validationErrors["address_line_1"]	=	"The Address Line 1 field is required."
		else:
			form['address_line_1'] 			= request.POST['address_line_1']		
			
		if request.POST["city"].strip() == "":
			validationErrors["city"]	=	"The city field is required."
		else:
			form['city'] 			= request.POST['city']	
				
		if request.POST["postal_code"].strip() == "":
			validationErrors["postal_code"]	=	"The postal code field is required."
		else:
			form['postal_code'] 			= request.POST['postal_code']	
					
				
		if request.POST["model_name"].strip() == "":
			validationErrors["model_name"]	=	"The modal name field is required."
		else:
			form['model_name'] 			= request.POST['model_name']	
				
		if request.POST["bio"].strip() == "":
			validationErrors["bio"]	=	"The bio field is required."
		else:
			form['bio'] 			= request.POST['bio']

		# regex = re.compile(r'https?://(?:www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*|(www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*')
			
		# if not re.match(regex, request.POST["link"].strip()):
		# 	validationErrors["link"]	=	"Please enter valid url."

				
		# if request.POST["government_id_number"].strip() == "":
			# validationErrors["government_id_number"]	=	"The Government Id Number field is required."
		# else:
			# form['government_id_number'] 			= request.POST['government_id_number']	
			
			
		# if request.POST["government_id_expiration_date"].strip() == "":
			# validationErrors["government_id_expiration_date"]	=	"The Government Id Expiration Date field is required."
		# else:
			# form['government_id_expiration_date'] 			= request.POST['government_id_expiration_date']	
			

			
		if request.POST.getlist('categories'):
			categories 					=   request.POST.getlist('categories')
			form['categories'] 			=   request.POST.getlist('categories')
			selectedCategories 			=   request.POST.getlist('categories')
		else:
			validationErrors["categories"]	=	"Please select Categories"
			
		if len(request.FILES) != 0:
			images = request.FILES.getlist("images")
			
			for imge in images:
				file = imge.name
				extension = file.split(".")[-1].lower()
				if not extension in VALID_IMAGE_EXTENSIONS:
					validationErrors["images"]	=	"This is not an valid image. Please upload a valid image."
		else:
			images = ''

			
				
		regex = re.compile(r'https?://(?:www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*|(www)?(?:[\w.-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{0,300})*')
			
		if request.POST["private_snapchat_link"] !='' and not re.match(regex, request.POST["private_snapchat_link"].strip()):
			validationErrors["private_snapchat_link"]	=	"Please enter valid url."
		form['private_snapchat_link'] 			= request.POST['private_snapchat_link']	
				
		if request.POST["public_snapchat_link"] !='' and not re.match(regex, request.POST["public_snapchat_link"].strip()):
			validationErrors["public_snapchat_link"]	=	"Please enter valid url."
		form['public_snapchat_link'] 			= request.POST['public_snapchat_link']
					
		if request.POST["public_instagram_link"] !='' and not re.match(regex, request.POST["public_instagram_link"].strip()):
			validationErrors["public_instagram_link"]	=	"Please enter valid url."
		form['public_instagram_link'] 			= request.POST['public_instagram_link']
			
		if request.POST["twitter_link"] !='' and not re.match(regex, request.POST["twitter_link"].strip()):
			validationErrors["twitter_link"]	=	"Please enter valid url."
		form['twitter_link'] 			= request.POST['twitter_link']
			
		if request.POST["youtube_link"] !='' and not re.match(regex, request.POST["youtube_link"].strip()):
			validationErrors["youtube_link"]	=	"Please enter valid url."
		form['youtube_link'] 			= request.POST['youtube_link']
			
		if request.POST["amazon_wishlist_link"] !='' and not re.match(regex, request.POST["amazon_wishlist_link"].strip()):
			validationErrors["amazon_wishlist_link"]	=	"Please enter valid url."
		form['amazon_wishlist_link'] 			= request.POST['amazon_wishlist_link']
		


		if request.POST["youtube_video_url"] !='' and not re.match(regex, request.POST["youtube_video_url"].strip()):
			validationErrors["youtube_video_url"]	=	"Please enter valid url."
		form['youtube_video_url'] 			= request.POST['youtube_video_url']

		
		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year

			myLinks								=	AdditionalLinks()
			myLinks.name						=	request.POST.get("link_name")
			myLinks.link						=	request.POST.get("link")
			if request.POST.get("link_name") and request.POST.get("link"):
				myLinks.model_id					=	id
				myLinks.save()


			users								=	User.objects.filter(id=id).first()
			users.first_name					=	request.POST.get("first_name","")
			users.last_name						=	request.POST.get("last_name","")
			users.username						=	request.POST.get("email","")
			users.email							=	request.POST.get("email","")
			users.previous_first_name			=	request.POST.get("previous_first_name","")
			users.previous_last_name			=	request.POST.get("previous_last_name","")
			users.date_of_birth					=	request.POST.get("date_of_birth","")
			users.gender						=	request.POST.get("gender","")
			users.country						=	request.POST.get("country","")
			users.address_line_1				=	request.POST.get("address_line_1","")
			users.address_line_2				=	request.POST.get("address_line_2","")
			users.city							=	request.POST.get("city","")
			users.postal_code					=	request.POST.get("postal_code","")
			users.skype_number					=	request.POST.get("skype_number","")
			users.model_name					=	request.POST.get("model_name","")
			users.bio							=	request.POST.get("bio","")
			users.private_snapchat_link			=	request.POST.get("private_snapchat_link","")
			users.public_snapchat_link			=	request.POST.get("public_snapchat_link","")
			users.public_instagram_link			=	request.POST.get("public_instagram_link","")
			users.twitter_link					=	request.POST.get("twitter_link","")
			users.youtube_link					=	request.POST.get("youtube_link","")
			users.amazon_wishlist_link			=	request.POST.get("amazon_wishlist_link","")
			users.age							=	request.POST.get("age","")
			users.from_date						=	request.POST.get("from_date","")
			users.height						=	request.POST.get("height","")
			users.weight						=	request.POST.get("weight","")
			users.hair							=	request.POST.get("hair","")
			users.eyes							=	request.POST.get("eyes","")
			users.youtube_video_url				=	request.POST.get("youtube_video_url","")
			if request.POST["password"]:
				users.password					=	make_password(request.POST["password"])
				
			users.government_id_number			=	request.POST.get("government_id_number","")
			users.government_id_expiration_date	=	request.POST.get("government_id_expiration_date","")


			if request.FILES.get("government_id_front_image") != "" and request.FILES.get("government_id_front_image"):
				gifiFile = request.FILES.get("government_id_front_image")
				
				filename = gifiFile.name.split(".")[0].lower()
				extension = gifiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				
				gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gifiFile, "model_images/"+gifi_image)
				users.government_id_front_image		=	gifi_image
				
				
			if request.FILES.get("government_id_back_image") != "" and request.FILES.get("government_id_back_image"):
				gibiFile = request.FILES.get("government_id_back_image")
				filename = gibiFile.name.split(".")[0].lower()
				extension = gibiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gibiFile, "model_images/"+gibi_image)
				users.government_id_back_image		=	gibi_image
				
			if request.FILES.get("photo_next_to_id") != "" and request.FILES.get("photo_next_to_id"):
				pntiFile = request.FILES.get("photo_next_to_id")
				filename = pntiFile.name.split(".")[0].lower()
				extension = pntiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiFile, "model_images/"+pnti_image)	
				users.photo_next_to_id				=	pnti_image
				
			if request.FILES.get("photo_next_to_id_with_dated_paper") != "" and request.FILES.get("photo_next_to_id_with_dated_paper"):
				pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
				filename = pntiwdpFile.name.split(".")[0].lower()
				extension = pntiwdpFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiwdpFile, "model_images/"+pntiwdp_image)
				users.photo_next_to_id_with_dated_paper	=	pntiwdp_image

			if request.FILES.get("featured_image") != "" and request.FILES.get("featured_image"):
				featFile = request.FILES.get("featured_image")
				filename = featFile.name.split(".")[0].lower()
				extension = featFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
					
				feat_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(featFile, "model_images/"+feat_image)
				users.featured_image	=	feat_image
				
			users.save()
			
			user_id = users.id
			#save category data
			categories 					=   request.POST.getlist('categories')
			if categories:
				ModelCategories.objects.filter(user_id=id).all().delete()
				for category in categories:
					ModelCategoriesInfo							=	ModelCategories()
					ModelCategoriesInfo.dropdown_manager_id 	= 	category
					ModelCategoriesInfo.user_id 				= 	id
					ModelCategoriesInfo.save()
				
				
			#save images data	
			
			images = request.FILES.getlist("images")
			selectedplanids	=	[]
			if images:
				# ModelImages.objects.filter(user_id=id).all().delete()
				for imge in images:	
					myfile = imge
					filename = myfile.name.split(".")[0].lower()
					extension = myfile.name.split(".")[-1].lower()
					newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
					model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
					
					ModelImagesInfo							=	ModelImages()
					ModelImagesInfo.image_url 				= 	model_image
					ModelImagesInfo.user_id 				= 	user_id
					ModelImagesInfo.save()

			lastUserId = user_id
			
			discount_arr = []
			for key in sub_type_list :
				
				if request.POST.get('subscription['+key+'][username]') :
					subUsername = request.POST.get('subscription['+key+'][username]')
				else:
					subUsername = ''
					
				if request.POST.get('subscription['+key+'][is_enabled]') :
					subIsEnabled = request.POST.get('subscription['+key+'][is_enabled]')
				else:
					subIsEnabled = 0
					
				ModelSubscriptionsde 					= ModelSubscriptions.objects.filter(user_id=id).filter(social_account=key).filter(is_deleted=0).first()
				
				if ModelSubscriptionsde:
					subObj 					= ModelSubscriptions.objects.filter(user_id=id).filter(social_account=key).filter(is_deleted=0).first()
					subObj.user_id 			= lastUserId
					subObj.social_account 	= key
					subObj.username 		= subUsername
					subObj.is_enabled 		= subIsEnabled
					subObj.save()	
					subId = subObj.id
					
				else:
					subObj 					= ModelSubscriptions()
					subObj.user_id 			= lastUserId
					subObj.social_account 	= key
					subObj.username 		= subUsername
					subObj.is_enabled 		= subIsEnabled
					subObj.save()	
					subId = subObj.id
					
					
				today_date = str(datetime.datetime.today().date())+" 00:00:00"
				
				
				if int(subIsEnabled) == int(1):
					subPlanCount = request.POST.get('addmoreCount_'+key)
					if subPlanCount :
						if int(subPlanCount) > 0:
							for i in range(0, int(subPlanCount)):
								index = i+1
								if request.POST.get('subscription['+key+'][plans]['+str(index)+'][plan_type]'):
									subscription_plan_id 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][subscription_plan_id]',0) 
									
									plan_type 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][plan_type]',"")
									offer_period_time 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_period_time]',"") 
									offer_period_type 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_period_type]',1) 
									price 					= request.POST.get('subscription['+key+'][plans]['+str(index)+'][price]',"") 
									currency 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][currency]',"") 
									offer_name 			= request.POST.get('subscription['+key+'][plans]['+str(index)+'][offer_name]',"")
									description 			= request.POST.get('subscription['+key+'][plans]['+str(index)+'][description]',"")
									is_discount_enabled 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_discount_enabled]',0)
									discount 				= request.POST.get('subscription['+key+'][plans]['+str(index)+'][discount]',0) 
									is_permanent_discount 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_permanent_discount]',"") 
									from_discount_date 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][from_discount_date]',"") 
									to_discount_date 		= request.POST.get('subscription['+key+'][plans]['+str(index)+'][to_discount_date]',"") 
									is_apply_to_rebills 	= request.POST.get('subscription['+key+'][plans]['+str(index)+'][is_apply_to_rebills]',"") 
									#print(is_discount_enabled)
									#print(is_discount_enabled)
									if(is_discount_enabled == "on"):
										is_discount_enabled	=	1
									else:
										is_discount_enabled	=	0;
										
									if(is_permanent_discount == "on"):
										is_permanent_discount	=	1
									else:
										is_permanent_discount	=	0;
										
									if(is_apply_to_rebills == "on"):
										is_apply_to_rebills	=	1
									else:
										is_apply_to_rebills	=	0;
									
									price = isDecimal(price)
									discount = isDecimal(discount)
									is_discount_enabled = isNum(is_discount_enabled)
									is_permanent_discount = isNum(is_permanent_discount)
									is_apply_to_rebills = isNum(is_apply_to_rebills)
									
									if is_discount_enabled and decimal.Decimal(discount) > 0:
										discounted_price = decimal.Decimal(price)-((decimal.Decimal(price)*decimal.Decimal(discount))/100)
										discounted_price = round(float(discounted_price),2)
										is_discount_enabled = 1
										discount_arr.append(discount)
										discount_arr = [Decimal(x) for x in discount_arr]
									else:
										is_discount_enabled = 0
										discounted_price = price
										
									
									if is_permanent_discount:
										is_permanent_discount = 1
									else:
										is_permanent_discount = 0
										
									if is_apply_to_rebills:
										is_apply_to_rebills = 1
									else:
										is_apply_to_rebills = 0
										
									if plan_type == "recurring":	
										if from_discount_date != "" and from_discount_date > today_date:
											is_discount_enabled = 0	
											
											
									if subscription_plan_id  != 0:
										plansObj = ModelSubscriptionPlans.objects.filter(id=subscription_plan_id).filter(model_subscription_id=subObj.id).filter(is_deleted=0).first()
										plansObj.user_id 							= lastUserId
										plansObj.model_subscription_id 				= subId
										plansObj.plan_type 							= plan_type
										plansObj.offer_period_time 					= offer_period_time
										plansObj.offer_period_type 					= offer_period_type
										plansObj.price 								= price
											
										plansObj.discounted_price 					= discounted_price
										plansObj.currency 							= userDetail.default_currency
										plansObj.offer_name 						= offer_name
										plansObj.description 						= description
										plansObj.is_discount_enabled 				= is_discount_enabled
										
										plansObj.discount 						= discount
										plansObj.from_discount_date 			= from_discount_date
										
										if to_discount_date:
											plansObj.to_discount_date 					= to_discount_date
											
										plansObj.is_permanent_discount 				= is_permanent_discount
										plansObj.is_apply_to_rebills 				= is_apply_to_rebills
										plansObj.save()
										selectedplanids.append(plansObj.id)
										selectedplanids = [Decimal(x) for x in selectedplanids]
									else:
										plansObj = ModelSubscriptionPlans()
										plansObj.user_id 							= lastUserId
										plansObj.model_subscription_id 				= subId
										plansObj.plan_type 							= plan_type
										plansObj.offer_period_time 					= offer_period_time
										plansObj.offer_period_type 					= offer_period_type
										plansObj.price 								= price
											
										plansObj.discounted_price 					= discounted_price
										plansObj.currency 							= userDetail.default_currency
										plansObj.description 						= description
										plansObj.offer_name 						= offer_name
										plansObj.is_discount_enabled 				= is_discount_enabled
										
										plansObj.discount 						= discount
										plansObj.from_discount_date 			= from_discount_date
										
										if to_discount_date:
											plansObj.to_discount_date 					= to_discount_date
											
										plansObj.is_permanent_discount 				= is_permanent_discount
										plansObj.is_apply_to_rebills 				= is_apply_to_rebills
										plansObj.save()
										
										selectedplanids.append(plansObj.id)
										selectedplanids = [Decimal(x) for x in selectedplanids]

			if len(discount_arr)!=0:
				high_discount	=	max(discount_arr)
				User.objects.filter(id=lastUserId).update(highest_discount=high_discount)
			else:
				discount_arr = []
				
			if len(selectedplanids)!=0:
				ModelSubscriptionPlans.objects.exclude(id__in=selectedplanids).filter(user_id=user_id).update(is_deleted=1)

			messages.success(request,"Model has been updated successfully.")
			return redirect('/models/')
	countriesArray	=	[]
	topRatedCountries1 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United Kingdom").values('id',"name")
	for country in topRatedCountries1:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	topRatedCountries2 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United States of America").values("name",'id')
	for country in topRatedCountries2:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	topRatedCountries3 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="Australia").values("name",'id')
	for country in topRatedCountries3:
		sub_data			=	{}
		sub_data['id']		=	country['id']
		sub_data['name']	=	country['name']
		countriesArray.append(sub_data)
	countryList	 = DropDownManager.objects.filter(dropdown_type='country').filter(is_active=1).exclude(name="Australia").exclude(name="United States of America").exclude(name="United Kingdom").all()
	for country in countryList:
		sub_data			=	{}
		sub_data['id']		=	country.id
		sub_data['name']	=	country.name
		countriesArray.append(sub_data)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all()

	context		=	{
		"form":form,
		"errors":validationErrors,
		"userDetail":userDetail,
		"additionalLinks":additionalLinks,
		"countriesArray":countriesArray,
		"categoryList":categoryList,
		"selectedCategories":selectedCategories,
		"selectedIamge":selectedIamge,
		"userImageDetail":userImageDetail,
		"subcriptionDataSanpchat":subcriptionDataSanpchat,	
		"subcriptionDataInstagram":subcriptionDataInstagram,	
		"subcriptionDataWhatsapp":subcriptionDataWhatsapp,	
		"subcriptionDataPrivateFeed":subcriptionDataPrivateFeed,	
		"subcriptionDataTips":subcriptionDataTips,
	}
	return render(request,"models/edit.html",context)

@login_required(login_url='/login/')
def viewModel(request,id):
	form	 = User.objects.filter(id=id).first()
	paymentDetails	=	AccountDetails.objects.filter(model_id = id).first()
	additionalLinks	=	AdditionalLinks.objects.filter(model_id = id).all()
	
	if not form:
		return redirect('/dashboard/')
	selectedCategories 	= ModelCategories.objects.filter(user_id=id).values_list('dropdown_manager_id',flat=True)
	
	selectedCategoriesName 	= DropDownManager.objects.filter(id__in=selectedCategories).values_list('name',flat=True)
	
	
	selectedIamge 		= ModelImages.objects.filter(user_id=id).values_list('image_url',flat=True)
	if form.country :
		country 	 = DropDownManager.objects.filter(id=form.country).first()
		if country :
			countryName = country.name
		else:
			countryName	 = ''
	else:
		countryName	 = ''
	
	planDataSnap	=	[]
	planDataPrivate	=	[]
	planDataWhatsapp	=	[]
	planDataInsta	=	[]
	subcriptionDataSanpchat       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='snapchat').first()
	if subcriptionDataSanpchat:
		planDataSnap = ModelSubscriptionPlans.objects.filter(is_deleted=0).filter(model_subscription_id=subcriptionDataSanpchat.id).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
		subcriptionDataSanpchat.plans = planDataSnap


	subcriptionDataPrivateFeed       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='private_feed').first()
	if subcriptionDataPrivateFeed:
		planDataPrivate = ModelSubscriptionPlans.objects.filter(is_deleted=0).filter(model_subscription_id=subcriptionDataPrivateFeed.id).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
		subcriptionDataPrivateFeed.plans = planDataPrivate
			
	subcriptionDataWhatsapp       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='whatsapp').first()
	if subcriptionDataWhatsapp:
		planDataWhatsapp = ModelSubscriptionPlans.objects.filter(is_deleted=0).filter(model_subscription_id=subcriptionDataWhatsapp.id).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
		subcriptionDataWhatsapp.plans = planDataWhatsapp	
		
	subcriptionDataInstagram       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='instagram').first()
	if subcriptionDataInstagram:
		planDataInsta = ModelSubscriptionPlans.objects.filter(is_deleted=0).filter(model_subscription_id=subcriptionDataInstagram.id).all().values('offer_name','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
		subcriptionDataInstagram.plans = planDataInsta
			
	subcriptionDataTips       	= ModelSubscriptions.objects.filter(user_id=id).filter(social_account='tips').first()
	contaxt={
	"form":form,
	"paymentDetails":paymentDetails,
	 "additionalLinks":additionalLinks,
	"selectedIamge":selectedIamge,
	"countryName":countryName,
	"selectedCategoriesName":selectedCategoriesName,
	"subcriptionDataSanpchat":subcriptionDataSanpchat,
	"planDataSnap":planDataSnap,
	"subcriptionDataPrivateFeed":subcriptionDataPrivateFeed,
	"planDataPrivate":planDataPrivate,
	"subcriptionDataWhatsapp":subcriptionDataWhatsapp,
	"planDataWhatsapp":planDataWhatsapp,
	"subcriptionDataInstagram":subcriptionDataInstagram,
	"planDataInsta":planDataInsta,
	"subcriptionDataTips":subcriptionDataTips,
	}
	return render(request,"models/view.html",contaxt)


@login_required(login_url='/login/')
def changeStatusModel(request,id,status):
    userDetail = User.objects.filter(id=id).first()
    if status=="1":
        userDetail.is_active= 1
        userDetail.save()
        message = 'Model has been Activated successfully.' 
    else:
        userDetail.is_active= 0
        userDetail.save()
        message = 'Model has been Deactivated successfully.' 
    messages.success(request,message) 
    return redirect('/models/')

@login_required(login_url='/login/')
def changeSubscriptionStatusModel(request,id,status):
    userDetail = User.objects.filter(id=id).first()
    if status=="1":
        userDetail.is_subscription_enabled= 1
        userDetail.save()
        message = 'Subscription has been Enabled successfully.' 
    else:
        userDetail.is_subscription_enabled= 0
        userDetail.save()
        message = 'Subscription has been Disabled successfully.' 
    messages.success(request,message) 
    return redirect('/models/')

@login_required(login_url='/login/')
def masterLogin(request,id):
	site_url = settings.FRONT_SITE_URL
	userDetail = User.objects.filter(id=id).first()
	slug = userDetail.slug
	if userDetail:
		userDetail.login_with_model = 1
		userDetail.save()
		return redirect(site_url+'model_login/'+slug)
    
# @login_required(login_url='/login/')
# def changeFeaturedStatusModel(request,id,status):
#     userDetail = User.objects.filter(id=id).first()
#     if status=="1":
#         userDetail.is_featured= 1
#         userDetail.save()
#         message = 'Model has been marked as featured successfully.' 
#     else:
#         userDetail.is_featured= 0
#         userDetail.save()
#         message = 'Model has been marked as unfeatured successfully.' 
#     messages.success(request,message) 
#     return redirect('/models/')


@login_required(login_url='/login/')
def offFeaturedStatusModel(request,id):
	status=""
	userDetail = User.objects.filter(id=id).filter(is_featured=1).first()
	if status=="":
		userDetail.is_featured= 0
		userDetail.save()
		message = 'Model has been marked as unfeatured successfully.'
	else:
		userDetail.is_featured= 1
		userDetail.save()
		message = 'Model has been marked as featured successfully.' 
	messages.success(request,message) 
	return redirect('/models/')


@login_required(login_url='/login/')
def modelFeaturedImage(request,id):
	userFeatImg			=	User.objects.filter(id=id).filter(is_featured=0).first()
	if not userFeatImg:
		return redirect('/dashboard/')
	form				=	{}
	validationErrors	=	{}
	if request.method	==	"POST":
		if request.FILES.get('featured_image') ==None or request.FILES.get("featured_image") == "":
			validationErrors["featured_image"]	=	"Please select featured image"
		else:
			featured_image = request.FILES.get("featured_image")
			file = featured_image.name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["featured_image"]	=	"This is not a valid image. Please upload a valid featured image."

		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year

			if request.FILES.get("featured_image"):
				orientation 					=   request.POST.get('ftimg_img_orientation')
				featFile = request.FILES.get("featured_image")
				filename = featFile.name.split(".")[0].lower()
				extension = featFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension

				feat_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(featFile, "model_images/"+feat_image)
				
				userFeatImg1						=	userFeatImg
				userFeatImg1.featured_image		=	feat_image
				userFeatImg1.is_featured= 1
				userFeatImg1.save()
				message = 'Model has been marked as featured successfully.' 


				messages.success(request,message) 
				return redirect('/models/')

	context = {"userFeatImg":userFeatImg,
				"errors":validationErrors
			}
	return render(request,"models/featured_img.html",context)



	
@login_required(login_url='/login/')
def deleteModel(request,id):
	newsletterSubscriber = NewsletterSubscriber.objects.filter(user_id=id).first()
	if newsletterSubscriber:
		newsletterSubscriber.delete()
	ModelCategories.objects.filter(user_id=id).all().delete()
	ModelImages.objects.filter(user_id=id).all().delete()
	users = User.objects.filter(id=id).first()
	users.email			=	users.email+'_deleted_'+id
	users.username		=	users.username+'_deleted_'+id
	users.is_deleted	=	1
	users.save()
	messages.success(request,"Model has been deleted successfully.")
	return redirect('/models/')



@login_required(login_url='/login/')
def deleteModelImages(request,id):
	instance	= ModelImages.objects.filter(id=id).get()
	model_id	=	instance.user_id
	if os.path.isfile(settings.MEDIA_ROOT+"/"'uploads'+"/"'model_images'+str(instance.image_url)):
		image_path = os.path.join(settings.MEDIA_ROOT+"/"'uploads'+"/"'model_images', str(instance.image_url))
		os.remove(image_path)
		
	ModelImages.objects.filter(id=id).all().delete()
	messages.success(request,"Model Image has been deleted successfully.")

	return redirect('/models/edit-model/'+str(model_id))


	
@login_required(login_url='/login/')
def add_subscription_field(request):
	sub_type 				= request.GET.get('sub_type', None)
	section 				= request.GET.get('section', None)
	
	if section and sub_type:
		context		=	{
			"sub_type":sub_type,
			"section":section,
		}
	return render(None, "models/add_sub_field.html",context)

def remove_subscription_field(request):
	sub_type 				= request.GET.get('sub_type', None)
	section 				= request.GET.get('section', None)
	
	if section and sub_type:
		context		=	{
			"sub_type":sub_type,
			"section":section,
		}
	return render(None, "models/add_sub_field.html",context)


@login_required(login_url='/login')
def viewSubscriberHistory(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = User.objects.filter(is_deleted=0).filter(signup_from=id)

	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model_name__icontains= model_name)
	
	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	
	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")	

	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=2).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=2).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "subscribers/viewsubscriber_history.html",context)


@login_required(login_url='/login')
def viewModelHistory(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	modelSubscriptionId = UserSubscriptionPlan.objects.filter(user_id=id).values('model_user_id')
	DB = User.objects.filter(is_deleted=0).filter(user_role_id=3).filter(id__in=modelSubscriptionId)
	categories = ''
	if request.GET.get('first_name'):
		first_name= request.GET.get('first_name').strip()
		DB = DB.filter(first_name__icontains= first_name)
		
	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model_name__icontains= model_name)
		
	if request.GET.get('last_name'):
		last_name= request.GET.get('last_name').strip()
		DB = DB.filter(last_name__icontains= last_name)
	
	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	
	if request.GET.get('is_active'):
		DB = DB.filter(is_active=request.GET.get('is_active'))
		
	if request.GET.get('gender'):
		DB = DB.filter(gender=request.GET.get('gender'))
		
	if request.GET.get('registered_from') and request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
	elif request.GET.get('registered_from'):
		DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
	elif request.GET.get('registered_to'):
		DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
		
	if request.GET.getlist('categories'):
		categories 			= request.GET.getlist('categories')
		categoriesModelId 	= ModelCategories.objects.filter(dropdown_manager_id__in=categories).values("user_id");
		DB 		= DB.filter(id__in=categoriesModelId)		

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(user_role_id=3).all()
	else:
		DB = DB.order_by(order_by).filter(user_role_id=3).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")
	# myModelDict = {}
	# model_user_id = []
	for result in results:
		amountPaid	=	UserSubscriptionPlan.objects.filter(user_id=id).filter(model_user_id=result.id).all().aggregate(Sum('amount'))
		result.amountPaid = amountPaid['amount__sum']
		
		
	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "models/viewmodel_history.html",context)


@login_required(login_url='/login')
def viewTransactionHistory(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	userDetail = User.objects.filter(is_deleted=0).filter(user_role_id=3).all().values('id')
	DB = TransactionHistory.objects.filter(status='success').filter(model_id__in=userDetail).filter(user_id=id)

	categories = ''
	if request.GET.get('transaction_type'):
		transaction_type= request.GET.get('transaction_type').strip()
		DB = DB.filter(transaction_type__icontains= transaction_type)
	if request.GET.get('username'):
		DB 			= DB.filter(Q(model__model_name__icontains=request.GET.get('username')) | Q(model__username__icontains=request.GET.get('username')) | Q(model__email__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')))
		
	if request.GET.get('transaction_from') and request.GET.get('transaction_to'):
		DB 			= DB.filter(transaction_date__gte=request.GET.get('transaction_from')+" 00:00:00")
		DB 			= DB.filter(transaction_date__lte=request.GET.get('transaction_to')+" 23:59:59")
	elif request.GET.get('transaction_from'):
		DB 			= DB.filter(transaction_date__gte=request.GET.get('transaction_from')+" 00:00:00")
	elif request.GET.get('transaction_to'):
		DB 			= DB.filter(transaction_date__lte=request.GET.get('transaction_to')+" 23:59:59")	

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(status='success').all()
	else:
		DB = DB.order_by(order_by).filter(status='success').all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")
	for result in results:
		if result.transaction_type=="subscription":
			if(result.user_subscription.plan_type == "recurring"):
				if(str(result.user_subscription.offer_period_type) == "week"):
					billed	=	"Weekly"
				if(str(result.user_subscription.offer_period_type) == "month"):
					billed	=	"Monthly"
				if(str(result.user_subscription.offer_period_type) == "year"):
					billed	=	"Yearly"
			else:
				billed	=	"One Time"
		else:
			billed						=	"Tips"
		result.billed	=	billed
			

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "subscribers/viewtransaction_history.html",context)



@login_required(login_url='/login')
def viewActiveSubscriptionPlans(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT

	userDetail = User.objects.filter(is_deleted=0).filter(user_role_id=3).all().values('id')
	DB 			= UserSubscriptionPlan.objects.filter(user_id=id).filter(plan_status='active').filter(is_subscription_cancelled=0).filter(model_user_id__in=userDetail)

	categories = ''

	if request.GET.get('username'):
		DB 			= DB.filter(Q(model_user__model_name__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')))
		
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")
	for result in results:
		if result.plan_type=="recurring":
			if(str(result.offer_period_type) == "week"):
				billed	=	"Weekly"
			if(str(result.offer_period_type) == "month"):
				billed	=	"Monthly"
			if(str(result.offer_period_type) == "year"):
				billed	=	"Yearly"
		else:
			billed	=	"One Time"
		result.billed	=	billed
			

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "subscribers/view_active_subscription_plan.html",context)



@login_required(login_url='/login')
def viewExpiredSubscriptionPlans(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT

	userDetail = User.objects.filter(is_deleted=0).filter(user_role_id=3).all().values('id')
	DB 			= UserSubscriptionPlan.objects.filter(user_id=id).filter(plan_status='expire').filter(model_user_id__in=userDetail)

	categories = ''

	if request.GET.get('username'):
		DB 			= DB.filter(Q(model_user__model_name__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')))
		
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")
	for result in results:
		if result.plan_type=="recurring":
			if(str(result.offer_period_type) == "week"):
				billed	=	"Weekly"
			if(str(result.offer_period_type) == "month"):
				billed	=	"Monthly"
			if(str(result.offer_period_type) == "year"):
				billed	=	"Yearly"
		else:
			billed	=	"One Time"
		result.billed	=	billed
			

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "subscribers/view_expired_subscription_plan.html",context)


@login_required(login_url='/login')
def viewTransactionHistoryInModel(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	userDetail = User.objects.filter(is_deleted=0).filter(user_role_id=2).all().values('id')
	DB = TransactionHistory.objects.filter(status='success').filter(user_id__in=userDetail).filter(model_id=id)

	categories = ''
	if request.GET.get('transaction_type'):
		transaction_type= request.GET.get('transaction_type').strip()
		DB = DB.filter(transaction_type__icontains= transaction_type)
	
	if request.GET.get('email'):
		email= request.GET.get('email').strip()
		DB = DB.filter(user_subscription__username__icontains=email)
		
	if request.GET.get('transaction_from') and request.GET.get('transaction_to'):
		DB 			= DB.filter(transaction_date__gte=request.GET.get('transaction_from')+" 00:00:00")
		DB 			= DB.filter(transaction_date__lte=request.GET.get('transaction_to')+" 23:59:59")
	elif request.GET.get('transaction_from'):
		DB 			= DB.filter(transaction_date__gte=request.GET.get('transaction_from')+" 00:00:00")
	elif request.GET.get('transaction_to'):
		DB 			= DB.filter(transaction_date__lte=request.GET.get('transaction_to')+" 23:59:59")	

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).filter(status='success').all()
	else:
		DB = DB.order_by(order_by).filter(status='success').all()

	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
		
	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	categoryList	 = DropDownManager.objects.filter(dropdown_type='category').all().values('name',"id")
	web_commission 		= settings.SITEWEBSITECOMMISSION
	billed = ''
	for result in results:
		amount = result.amount
		#commission_amount 	= (decimal.Decimal(amount)*decimal.Decimal(web_commission))/decimal.Decimal(100)
		net_amount 			= decimal.Decimal(amount)-decimal.Decimal(result.commission)
		result.net_revenue = net_amount


		if result.transaction_type=="subscription":
			if(result.user_subscription.plan_type == "recurring"):
				if(str(result.user_subscription.offer_period_type) == "week"):
					billed	=	"Weekly"
				if(str(result.user_subscription.offer_period_type) == "month"):
					billed	=	"Monthly"
				if(str(result.user_subscription.offer_period_type) == "year"):
					billed	=	"Yearly"
			else:
				billed	=	"One Time"
			
		else:
			billed						=	"Tips"
		result.billed	=	billed

		if result.transaction_type !="tips":
			if(result.payment_type == "rebills"):
				descriptions				=	"Rebills"
			elif(result.payment_type == "tips"):
				descriptions				=	"Tips"
			elif(result.payment_type == "joins"):
				descriptions				=	"Joins"
		elif result.transaction_type=="tips":
			descriptions				=	"Tips"
		result.descriptions	=	descriptions

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'billed':billed,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'categoryList': categoryList,
		'categories': categories,
		'datetimeFormat':datetimeFormat
	}
	return render(request, "models/viewtransaction_history_in_model.html",context)
	
	
@login_required(login_url='/login')
def editAccountDetails(request, id):

	userDetail	 = User.objects.filter(id=id).first()
	if not userDetail:
		return redirect('/dashboard/')

	form				=	userDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST.get("account_name") == None or request.POST.get("account_name") == "":
			validationErrors["account_name"]	=	"The account name field is required"

		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required"
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid"
				
		# if request.POST["account_name"].strip() == "":
		# 	validationErrors["account_name"]	=	"The account name field is required."

		if request.POST["skype"] == "" or request.POST["skype"] == None:
			validationErrors["skype"]	=	"The skype field is required."
				
		if request.POST["phone_number"] == "" or request.POST["phone_number"] == None:
			validationErrors["phone_number"]	=	"The phone number field is required."

		if not validationErrors:
			users						=	User.objects.filter(id=id).first()
			users.model_name			=	request.POST["account_name"]
			users.username				=	request.POST["email"]
			users.phone_number			=	request.POST["phone_number"]
			users.skype_number			=	request.POST["skype"]
			users.save()
			messages.success(request,"Account Details has been updated successfully.")
			return redirect('/models/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"userDetail":userDetail
	}
	return render(request, "models/edit_account_details.html",context)
	
	
def editPaymentDetails(request, id):
	userDetail	 	=	User.objects.filter(id=id).first()
	accountDetail	=	AccountDetails.objects.filter(model_id=id).first()
	if not userDetail:
		return redirect('/dashboard/')
	validationErrors	=	{}
	form				=	accountDetail
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST.get("payment_method") == None or request.POST.get("payment_method") == "":
			validationErrors["payment_method"]	=	"The payment method field is required"
		else:
			if request.POST.get("payment_method") == "wire":
				if request.POST.get("bank_name_wire") == None or request.POST.get("bank_name_wire") == "":
					validationErrors["bank_name_wire"]	=	"The bank name field is required."
				if request.POST.get("bank_address_wire") == None or request.POST.get("bank_address_wire") == "":
					validationErrors["bank_address_wire"]	=	"The bank address field is required."
				if request.POST.get("swift_code_wire") == None or request.POST.get("swift_code_wire") == "":
					validationErrors["swift_code_wire"]	=	"The swift code field is required."
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."
				if request.POST.get("pay_to") == None or request.POST.get("pay_to") == "":
					validationErrors["pay_to"]	=	"The pay to field is required."
				if request.POST.get("country") == None or request.POST.get("country") == "":
					validationErrors["country"]	=	"The country field is required."
				if request.POST.get("iban_wire") == None or request.POST.get("iban_wire") == "":
					validationErrors["iban_wire"]	=	"The iban field is required."
			if request.POST.get("payment_method") == "cheque":
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."
				if request.POST.get("name") == None or request.POST.get("name") == "":
					validationErrors["name"]	=	"The name field is required."
				if request.POST.get("cheque_email") == None or request.POST.get("cheque_email") == "":
					validationErrors["cheque_email"]	=	"The email field is required."
				if request.POST.get("address") == None or request.POST.get("address") == "":
					validationErrors["address"]	=	"The address field is required."
				if request.POST.get("contact_number") == None or request.POST.get("contact_number") == "":
					validationErrors["contact_number"]	=	"The contact number field is required."
			if request.POST.get("payment_method") == "paypal":
				if request.POST.get("paypal_email") == None or request.POST.get("paypal_email") == "":
					validationErrors["paypal_email"]	=	"The paypal email field is required."
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."

			if not validationErrors:
				if request.POST.get("payment_method")	==	"wire":
					if accountDetail:
						wireMethod							=	accountDetail
						wireMethod.bank_name				=	request.POST.get("bank_name_wire")
						wireMethod.bank_address				=	request.POST.get("bank_address_wire")
						wireMethod.swift_bic				=	request.POST.get("swift_code_wire")
						wireMethod.minimum_payout 			=	request.POST.get("minimum_payout")
						wireMethod.pay_to		 			= 	request.POST.get("pay_to")
						wireMethod.country					=	request.POST.get("country")
						wireMethod.iban						=	request.POST.get("iban_wire")
						wireMethod.payment_method			=	request.POST.get("payment_method")
						wireMethod.save()
					else:
						wireMethod							=	AccountDetails()
						wireMethod.bank_name				=	request.POST.get("bank_name_wire")
						wireMethod.bank_address				=	request.POST.get("bank_address_wire")
						wireMethod.swift_bic				=	request.POST.get("swift_code_wire")
						wireMethod.minimum_payout 			=	request.POST.get("minimum_payout")
						wireMethod.pay_to		 			= 	request.POST.get("pay_to")
						wireMethod.country					=	request.POST.get("country")
						wireMethod.iban						=	request.POST.get("iban_wire")
						wireMethod.model_id					=	id
						wireMethod.payment_method			=	request.POST.get("payment_method")
						wireMethod.save()
				if request.POST.get("payment_method")	==	"cheque":
					if accountDetail:
						chequeMethod							=	accountDetail
						chequeMethod.minimum_payout				=	request.POST.get("minimum_payout")
						chequeMethod.name						=	request.POST.get("name")
						chequeMethod.address					=	request.POST.get("address")
						chequeMethod.contact_number				=	request.POST.get("contact_number")
						chequeMethod.payment_method 			=	request.POST.get("payment_method")
						chequeMethod.cheque_email				=	request.POST.get("cheque_email")
						chequeMethod.save()
					else:
						chequeMethod							=	AccountDetails()
						chequeMethod.minimum_payout				=	request.POST.get("minimum_payout")
						chequeMethod.name						=	request.POST.get("name")
						chequeMethod.address					=	request.POST.get("address")
						chequeMethod.contact_number				=	request.POST.get("contact_number")
						chequeMethod.payment_method 			=	request.POST.get("payment_method")
						chequeMethod.cheque_email				=	request.POST.get("cheque_email")
						chequeMethod.model_id					=	id
						chequeMethod.save()
					
				if request.POST.get("payment_method")	==	"paypal":
					if accountDetail:
						paypalMethod							=	accountDetail
						paypalMethod.paypal_email				=	request.POST.get("paypal_email")
						paypalMethod.minimum_payout				=	request.POST.get("minimum_payout")
						paypalMethod.payment_method				=	request.POST.get("payment_method")
						paypalMethod.save()
					else:
						paypalMethod							=	AccountDetails()
						paypalMethod.paypal_email				=	request.POST.get("paypal_email")
						paypalMethod.minimum_payout				=	request.POST.get("minimum_payout")
						paypalMethod.payment_method				=	request.POST.get("payment_method")
						paypalMethod.model_id					=	id
						paypalMethod.save()
				
				messages.success(request,"Account Details has been updated successfully.")
				return redirect('/models/')
				
	context	=	{
		"userDetail":userDetail,
		"form":form,
		"accountDetail":accountDetail,
		"errors":validationErrors,
	}
	return render(request, "models/edit_payment_details.html", context)



def ModelActiveSubscribers(request, id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(is_subscription_cancelled = 0).filter(plan_status="active").all()
	totalActiveCount	=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(is_subscription_cancelled = 0).filter(plan_status="active").all().count()

	if request.GET.get('username'):
		DB 			= DB.filter(username__icontains=request.GET.get('username'))
	if request.GET.get('social_account'):
		DB 			= DB.filter(model_subscription__social_account__icontains=request.GET.get('social_account'))	

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")	
	countTotel  = DB.count()
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()
			
	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)

	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	billed	=	""
	if results:
		for result in results:
			totalSpend	=	TransactionHistory.objects.filter(status='success').filter(model_id=id).filter(model_subscription_id=result.model_subscription_id).filter(user_id=result.user_id).all().aggregate(Sum('amount'))

			if totalSpend['amount__sum']:
				if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
					result.total_spend			=	round(totalSpend['amount__sum'])
				else:
					result.total_spend			=	totalSpend['amount__sum']
			else:
				result.total_spend				=	totalSpend['amount__sum']


			if(result.plan_type == "recurring"):
				if(str(result.offer_period_type) == "week"):
					billed	=	"Weekly"
				if(str(result.offer_period_type) == "month"):
					billed	=	"Monthly"
				if(str(result.offer_period_type) == "year"):
					billed	=	"Yearly"
			else:
				billed	=	"One Time"
			result.billed	=	billed

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'totalActiveCount':totalActiveCount,
		'billed':billed,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat
	}


	return render(request, "models/model_active_subscribers.html",context)







def ModelExpiredSubscribers(request, id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire")).all()
	totalExpiredCount	=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire")).all().count()
	if request.GET.get('username'):
		DB 			= DB.filter(username__icontains=request.GET.get('username'))
	if request.GET.get('social_account'):
		DB 			= DB.filter(model_subscription__social_account__icontains=request.GET.get('social_account'))	

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")	
	countTotel  = DB.count()
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()
			
	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)

	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	billed	=	""
	if results:
		for result in results:
			totalSpend	=	TransactionHistory.objects.filter(status='success').filter(model_id=id).filter(model_subscription_id=result.model_subscription_id).filter(user_id=result.user_id).all().aggregate(Sum('amount'))

			if totalSpend['amount__sum']:
				if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
					result.total_spend			=	round(totalSpend['amount__sum'])
				else:
					result.total_spend			=	totalSpend['amount__sum']
			else:
				result.total_spend				=	totalSpend['amount__sum']


			if(result.plan_type == "recurring"):
				if(str(result.offer_period_type) == "week"):
					billed	=	"Weekly"
				if(str(result.offer_period_type) == "month"):
					billed	=	"Monthly"
				if(str(result.offer_period_type) == "year"):
					billed	=	"Yearly"
			else:
				billed	=	"One Time"
			result.billed	=	billed

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'totalExpiredCount':totalExpiredCount,
		'billed':billed,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat
	}

	return render(request, "models/model_expired_subscribers.html",context)





def ModelReportedSubscribers(request, id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(is_flaged=1).all()
	totalReportedCount	=	UserSubscriptionPlan.objects.filter(model_user_id=id).filter(is_flaged=1).all().count()

	if request.GET.get('username'):
		DB 			= DB.filter(username__icontains=request.GET.get('username'))
	if request.GET.get('social_account'):
		DB 			= DB.filter(model_subscription__social_account__icontains=request.GET.get('social_account'))	

	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")	
	countTotel  = DB.count()
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()
			
	recordPerPge	=	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)

	# Get the index of the current page	
	index = results.number - 1 # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns 
    # an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	
	searchingVariables	=	request.GET
	querySring			=	searchingVariables.copy()
	if 'page' in querySring:
		querySring.pop("page")
	if 'direction' in querySring:
		querySring.pop("direction")
	if 'order_by' in querySring:
		querySring.pop("order_by")

	querySring	=	urlencode(querySring)
	billed	=	""
	if results:
		for result in results:
			totalSpend	=	TransactionHistory.objects.filter(status='success').filter(model_id=id).filter(model_subscription_id=result.model_subscription_id).filter(user_id=result.user_id).all().aggregate(Sum('amount'))

			if totalSpend['amount__sum']:
				if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
					result.total_spend			=	round(totalSpend['amount__sum'])
				else:
					result.total_spend			=	totalSpend['amount__sum']
			else:
				result.total_spend				=	totalSpend['amount__sum']


			if(result.plan_type == "recurring"):
				if(str(result.offer_period_type) == "week"):
					billed	=	"Weekly"
				if(str(result.offer_period_type) == "month"):
					billed	=	"Monthly"
				if(str(result.offer_period_type) == "year"):
					billed	=	"Yearly"
			else:
				billed	=	"One Time"
			result.billed	=	billed

	context		=	{
		'results': results,
		'id': id,
		'page': page,
		'totalReportedCount':totalReportedCount,
		'billed':billed,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'datetimeFormat':datetimeFormat
	}


	return render(request, "models/model_reported_subscribers.html",context)




@login_required(login_url='/login/')
def export_models_xls(request):
	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = 'attachment; filename="models.xls"'

	wb = xlwt.Workbook(encoding='utf-8')
	ws = wb.add_sheet('Models')

	# Sheet header, first row
	row_num = 0

	font_style = xlwt.XFStyle()
	font_style.font.bold = True

	columns = ['Model Name', 'First Name', 'Last Name', 'Gender',  'Email', 'Status', 'Total Subscribers', 'Registered On']

	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)

	# Sheet body, remaining rows
	font_style = xlwt.XFStyle()

	# rows = TransactionHistory.objects.filter(user__is_deleted=0).filter(model__is_deleted=0).all().values_list('model__model_name', 'user__email', 'transaction_date', 'transaction_type','amount', 'commission', 'status')

	# for row in rows:
	#     row = list(row)
	#     row[2].replace(tzinfo=None)
	#     row[2] = datetime.datetime.strftime(row[2], "%Y-%m-%d %H:%M:%S")
	#     row_num += 1
	#     for col_num in range(len(row)):
	#         ws.write(row_num, col_num, row[col_num], font_style)

	rows = User.objects.filter(is_deleted=0).filter(user_role_id=3).all()

	for row in rows:
		model_name			=	row.model_name
		first_name			=	row.first_name
		last_name			=	row.last_name
		gender    			=   row.gender
		email   			=   row.email

		if row.is_approved == 1:
			if row.is_active == 1:
				status				=	"Active"
			else:
				status 				=	"Deactive"
		elif row.is_approved == 2:
			status 					=	"Rejected"
		else:
			status 					=	"Profile Approval Pending"
		if row.is_subscription_enabled ==1:
			status 					=	"Subscription Enabled"+" "+status
		else:
			status 					=	"Subscription Disabled"+" "+status
        
		total_subscribers	=	row.total_subscriber_signup
		registered_on		=	row.created_at
		registered_on    	=   datetime.datetime.strftime(registered_on, "%Y-%m-%d %H:%M:%S")
		registered_on		=	registered_on+""
	
		row_num += 1
		for col_num in range(len(columns)):
			if int(col_num) == 0:
				ws.write(row_num, col_num, model_name, font_style)
			if int(col_num) == 1:
				ws.write(row_num, col_num, first_name, font_style)
			if int(col_num) == 2:
				ws.write(row_num, col_num, last_name, font_style)
			if int(col_num) == 3:
				ws.write(row_num, col_num, gender, font_style)
			if int(col_num) == 4:
				ws.write(row_num, col_num, email, font_style)
			if int(col_num) == 5:
				ws.write(row_num, col_num, status, font_style)
			if int(col_num) == 6:
				ws.write(row_num, col_num, total_subscribers, font_style)
			if int(col_num) == 7:
				ws.write(row_num, col_num, registered_on, font_style)

	wb.save(response)
	return response






@login_required(login_url='/login/')
def export_subscribers_xls(request):
	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = 'attachment; filename="subscribers.xls"'

	wb = xlwt.Workbook(encoding='utf-8')
	ws = wb.add_sheet('Subscribers')

	# Sheet header, first row
	row_num = 0

	font_style = xlwt.XFStyle()
	font_style.font.bold = True

	columns = ['Account Name', 'Email', 'Status', 'Sign Up From',  'Registered On']

	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)

	# Sheet body, remaining rows
	font_style = xlwt.XFStyle()

	# rows = TransactionHistory.objects.filter(user__is_deleted=0).filter(model__is_deleted=0).all().values_list('model__model_name', 'user__email', 'transaction_date', 'transaction_type','amount', 'commission', 'status')

	# for row in rows:
	#     row = list(row)
	#     row[2].replace(tzinfo=None)
	#     row[2] = datetime.datetime.strftime(row[2], "%Y-%m-%d %H:%M:%S")
	#     row_num += 1
	#     for col_num in range(len(row)):
	#         ws.write(row_num, col_num, row[col_num], font_style)

	rows = User.objects.filter(is_deleted=0).filter(user_role_id=2).all()

	for row in rows:
		account_name			=	row.model_name
		email					=	row.email
		if row.is_active == 1:
			status				=	"Active"
		else:
			status 				=	"Deactive"
		
		if row.signup_from == None:
			signup_from			=	"Home Page"
		else:
			signup_from 		=	row.signup_from.model_name

		registered_on		=	row.created_at
		registered_on    	=   datetime.datetime.strftime(registered_on, "%Y-%m-%d %H:%M:%S")
		registered_on		=	registered_on+""
	
		row_num += 1
		for col_num in range(len(columns)):
			if int(col_num) == 0:
				ws.write(row_num, col_num, account_name, font_style)
			if int(col_num) == 1:
				ws.write(row_num, col_num, email, font_style)
			if int(col_num) == 2:
				ws.write(row_num, col_num, status, font_style)
			if int(col_num) == 3:
				ws.write(row_num, col_num, signup_from, font_style)
			if int(col_num) == 4:
				ws.write(row_num, col_num, registered_on, font_style)


	wb.save(response)
	return response
	