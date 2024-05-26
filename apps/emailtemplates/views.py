from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.base import ObjectDoesNotExist
from apps.emailtemplates.models import EmailTemplates,EmailAction
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
import urllib
from django.db.models import Q
import os
import datetime
from django.core.files.storage import FileSystemStorage
import re
from django.conf import settings
 
# Create your views here.

@login_required(login_url='/login/')
def index(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = EmailTemplates.objects
	if request.GET.get('name'):
		name = request.GET.get('name').strip()
		DB = DB.filter(name__icontains=name)

	if request.GET.get('subject'):
		subject=request.GET.get('subject').strip()
		DB = DB.filter(subject__icontains=subject)
		
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	if direction == "DESC":
		DB = DB.order_by("-"+order_by).all()
	else:
		DB = DB.order_by(order_by).all()
	recordPerPge    =	settings.READINGRECORDPERPAGE
	page = request.GET.get('page', 1)
	paginator = Paginator(DB, recordPerPge)
	try:
		results = paginator.page(page)
	except PageNotAnInteger:
		results = paginator.page(1)
	except EmptyPage:
		results = paginator.page(paginator.num_pages)
	# Get the index of the current page
	index = results.number - 1  # edited to something easier without index
	# This value is maximum index of your pages, so the last page - 1
	max_index = len(paginator.page_range)
	# You want a range of 7, so lets calculate where to slice the list
	start_index = index - 3 if index >= 3 else 0
	end_index = index + 3 if index <= max_index - 3 else max_index
	# Get our new page range. In the latest versions of Django page_range returns
	# an iterator. Thus pass it to list, to make our slice possible again.
	page_range = list(paginator.page_range)[start_index:end_index]
	searchingVariables	=	request.GET;
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
		'page': page,
		'page_range': page_range,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'datetimeFormat': datetimeFormat
	}
	return render(request, "emailtemplates/index.html", context)

@login_required(login_url='/login/')
def add(request):
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST["name"] == "":
			validationErrors["name"]	=	"The name field is required."
			
		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The subject field is required."
				
		if request.POST["body"] == "":
			validationErrors["body"]	=	"The email body field is required."
			
		if request.POST["action_id"] == "":
			validationErrors["action_id"]	=	"The action field is required."
				
		
		if not validationErrors:
			
			emailTemplatess				=	EmailTemplates()
			emailTemplatess.name = request.POST["name"]
			emailTemplatess.subject = request.POST["subject"]
			emailTemplatess.action = request.POST["action_id"]
			emailTemplatess.body = request.POST["body"]
			
			emailTemplatess.save()
			messages.success(request,"email template has been added successfully.")
			return redirect('/emailtemplates/')
	
	email_actions=EmailAction.objects.all()
	context		=	{
		"form":form,
		"errors":validationErrors,
		"email_actions":email_actions,
	}
	return render(request,"emailtemplates/add.html",context)
	
@login_required(login_url='/login/')
def edit(request,id):
	emailDetail	 =  EmailTemplates.objects.filter(id=id).first()
	if not emailDetail:
		return redirect('/emailtemplates/')

	form				=	emailDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST["name"] == "":
			validationErrors["name"]	=	"The name field is required."
			
		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The subject field is required."
				
			
		if request.POST["body"] == "":
			validationErrors["body"]	=	"The email body field is required."		
		
		if not validationErrors:
			emailTemplatess		=	emailDetail
			emailTemplatess.name = request.POST["name"]
			emailTemplatess.subject = request.POST["subject"]
			emailTemplatess.body = request.POST["body"]
			emailTemplatess.save()

			messages.success(request,"email template has been updated successfully.")
			return redirect('/emailtemplates/')

	email_actions=EmailAction.objects.all()
	context		=	{
		"form":form,
		"errors":validationErrors,
		"emailDetail":emailDetail,
		"email_actions":email_actions,
	}
	return render(request,"emailtemplates/edit.html",context)
	
@login_required(login_url='/login/')
def get_constant(request):
	data = {}
	options = {}
	action 				= request.GET.get('action', None)
	
	if action:
		constants = EmailAction.objects.filter(id=action).values("option").first();
		if constants:
			constants_list 		= constants['option'].split(",")
		else:
			constants_list	=	''
		data['success1'] = 1
		data['options'] = constants_list
	else:
		data['error'] = 1
	return JsonResponse(data)
	





