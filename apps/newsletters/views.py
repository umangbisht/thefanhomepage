from django.shortcuts import render,redirect,HttpResponse
from django.contrib import messages
from apps.newsletters.models import Newsletter
from apps.newsletters.models import NewsletterSubscriber
from apps.newsletters.models import ScheduledNewsletter
from apps.newsletters.models import ScheduledNewsletterSubscriber
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
import urllib
from django.db.models import Q
import os
import re
from django.conf import settings
 

@login_required(login_url='/login/')
def index(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = Newsletter.objects
	if request.GET.get('subject'):
		subject = request.GET.get('subject').strip()
		DB = DB.filter(subject__icontains=subject)

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
	return render(request, "newsletters/index.html", context)

@login_required(login_url='/login/')
def add(request):
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The subject field is required."

		if request.POST.get("body") == "":
			validationErrors["body"]	=	"The email body field is required."
			
		if not validationErrors:
			Obj					= 	Newsletter()
			Obj.subject 		= 	request.POST["subject"]
			Obj.body 			= 	request.POST.get("body")
			Obj.save()
			messages.success(request,"Newsletter has been added successfully.")
			return redirect('/newsletters/')

	context		=	{
		"form":form,
		"errors":validationErrors,
	}
	return render(request,"newsletters/add.html",context)
	
@login_required(login_url='/login/')
def edit(request,id):
	ObjDetail	 =  Newsletter.objects.filter(id=id).first()
	if not ObjDetail:
		return redirect('/newsletters/')

	form				=	ObjDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The newsletter subject field is required."
		
		if request.POST.get("body") == "":
			validationErrors["body"]	=	"The newsletter email body field is required."	
			
		if request.POST.get("constants") == "":
			validationErrors["constants"]	=	"The newsletter constants field is required."
		if not validationErrors:
			Obj						= 	ObjDetail
			Obj.subject 			= 	request.POST["subject"]
			Obj.body 				= 	request.POST.get("body")
			Obj.save()
			messages.success(request,"Newsletter has been updated successfully.")
			return redirect('/newsletters/')
	
	context		=	{
		"form":form,
		"errors":validationErrors,
		"ObjDetail":ObjDetail,
	}
	return render(request,"newsletters/edit.html",context)

@login_required(login_url='/login/')
def deleteNewsletter(request,id):
	Newsletter.objects.filter(id=id).delete()
	messages.success(request,"Newsletter has been deleted successfully.")
	return redirect('/newsletters/')
	
@login_required(login_url='/login/')
def subscribers(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = NewsletterSubscriber.objects
	if request.GET.get('email'):
		email = request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)
	if request.GET.get('started_at'):
		started_at= request.GET.get('started_at').strip()
		DB = DB.filter(created_at__gte= started_at)

	if request.GET.get('ended_at'):
		ended_at= request.GET.get('ended_at').strip()
		DB = DB.filter(created_at__lte= ended_at)

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
		'datetimeFormat':datetimeFormat
	}
	return render(request, "newsletters/subscribers.html", context)

@login_required(login_url='/login/')
def add_newsletter_subscriber(request):
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST["email"] == "" or request.POST["email"] ==None:
			validationErrors["email"]	=	"The subscriber email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST["email"] and not re.match(EMAIL_REGEX, request.POST["email"]):
				validationErrors["email"]	=	"This email is not valid."
			else:
				if NewsletterSubscriber.objects.filter(email=request.POST["email"]).exists():
					validationErrors["email"]	=	"This email is already exists."
		if not validationErrors:
			Obj					= 	NewsletterSubscriber()
			Obj.email 			= 	request.POST["email"]
			Obj.save()
			messages.success(request,"Newsletter Subscriber has been added successfully.")
			return redirect('/newsletters/newsletters-subscribers')
	
	context		=	{
		"form":form,
		"errors":validationErrors,
	}

	return render(request, "newsletters/add_newsletter_subscriber.html", context)


@login_required(login_url='/login/')
def deleteSubscriber(request,id):
	NewsletterSubscriber.objects.filter(id=id).delete()
	messages.success(request,"Subscriber has been deleted successfully.")
	return redirect('/newsletters/newsletters-subscribers')

@login_required(login_url='/login/')
def scheduled_newsletter(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = ScheduledNewsletter.objects
	if request.GET.get('subject'):
		subject = request.GET.get('subject').strip()
		DB = DB.filter(subject__icontains=subject)
	if request.GET.get('scheduled_date'):
		scheduled_date = request.GET.get('scheduled_date').strip()
		DB = DB.filter(scheduled_date__icontains=scheduled_date)


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
		'datetimeFormat':datetimeFormat
	}
	return render(request, "newsletters/scheduled_newsletter.html",context)

@login_required(login_url='/login/')
def sendScheduledNewsletter(request,id):
	NewsletterDetail	 =  Newsletter.objects.filter(id=id).first()
	newsletSubscriber	 =  NewsletterSubscriber.objects.all().values('email')
	
	if not NewsletterDetail:
		return redirect('/newsletters/')

	form				=	NewsletterDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		
		if request.POST["scheduled_date"] == "":
			validationErrors["scheduled_date"]	=	"The scheduled date field is required."

		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The subject field is required."

		if request.POST.get("body") == "":
			validationErrors["body"]	=	"The email body field is required."

		if request.POST.getlist("email") == []:
			validationErrors["email"]	=	"The subscriber's email field is required."

		
			
		if not validationErrors:
			
			Obj					= 	ScheduledNewsletter()
			Obj.scheduled_date 	= 	request.POST["scheduled_date"]
			Obj.subject 		= 	request.POST["subject"]
			Obj.body 			= 	request.POST.get("body")
			Obj.save()
			lastId	=	Obj.id
			
			
			ScheduledNewsletterEmails	=	request.POST.getlist("email")
			ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=lastId).delete()			
			for email in ScheduledNewsletterEmails:
				Obj							=	ScheduledNewsletterSubscriber()
				Obj.email 					= 	email
				Obj.scheduled_newsletter_id	=	lastId
				Obj.save()
		
			messages.success(request,"Scheduled Newsletter has been saved successfully.")
			return redirect('/newsletters/scheduled-newsletters')
				
	context		=	{
		"form":form,
		"errors":validationErrors,
		"NewsletterDetail":NewsletterDetail,
		"newsletSubscriber":newsletSubscriber,
	}
	return render(request, "newsletters/send_scheduled_newsletters.html",context)

@login_required(login_url='/login/')
def editScheduledNewsletter(request, id):
	selectedSubscribers  = ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=id).all().values('email')
	scheduleSubscribers = []
	for subscriber in selectedSubscribers:
		scheduleSubscribers.append(subscriber['email'])
	NewsletterDetail	 =  ScheduledNewsletter.objects.filter(id=id).first()
	newsletSubscriber	 =  NewsletterSubscriber.objects.all()
	if not NewsletterDetail:
		return redirect('/newsletters/')

	form				=	NewsletterDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	{}
		if request.POST["scheduled_date"] == "":
			validationErrors["scheduled_date"]	=	"The scheduled date field is required."
		form['scheduled_date'] = request.POST["scheduled_date"]

		if request.POST["subject"] == "":
			validationErrors["subject"]	=	"The subject field is required."

		if request.POST.get("body") == "":
			validationErrors["body"]	=	"The email body field is required."

		if request.POST.getlist("email") == None:
			validationErrors["email"]	=	"The subscriber email field is required."
		form["email"] = request.POST.getlist("email")
			
		if not validationErrors:
			Obj					= 	NewsletterDetail
			Obj.scheduled_date 	= 	request.POST["scheduled_date"]
			Obj.subject 		= 	request.POST["subject"]
			Obj.body 			= 	request.POST.get("body")
			Obj.save()
			lastId	=	Obj.id
			ScheduledNewsletterEmails	=	request.POST.getlist("email")
			ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=lastId).delete()
			for email in ScheduledNewsletterEmails:
				Obj							=	ScheduledNewsletterSubscriber()
				Obj.email 					= 	email
				Obj.scheduled_newsletter_id	=	lastId
				Obj.save()

			messages.success(request,"Scheduled newsletter has been updated successfully.")
			return redirect('/newsletters/scheduled-newsletters')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"NewsletterDetail":NewsletterDetail,
		"newsletSubscriber":newsletSubscriber,
		"scheduleSubscribers":scheduleSubscribers
	}
	return render(request, "newsletters/edit_scheduled_newsletters.html", context)

@login_required(login_url='/login/')
def deleteScheduledNewsletter(request,id):
	ScheduledNewsletter.objects.filter(id=id).delete()
	messages.success(request,"Scheduled newsletter has been deleted successfully.")
	return redirect('/newsletters/scheduled-newsletters')

@login_required(login_url='/login/')
def statusScheduledEmail(request,id):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = ScheduledNewsletterSubscriber.objects
	if request.GET.get('email'):
		email = request.GET.get('email').strip()
		DB = DB.filter(email__icontains=email)

	DB = DB.filter(scheduled_newsletter_id=id)
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
	index = results.number - 1  # edited to something easier without index
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
		'page': page,
		'page_range': page_range,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'id': id,
		'datetimeFormat':datetimeFormat,
	}
	return render(request, "newsletters/status_scheduled_email.html", context)

@login_required(login_url='/login/')
def deleteStatusEmailScheduledNewsletter(request,scheduled_newsletter_id,id):
	ScheduledNewsletterSubscriber.objects.filter(id=id).delete()
	messages.success(request,"Email has been deleted successfully.")
	return redirect('/newsletters/scheduled-newsletters/status/'+scheduled_newsletter_id)
