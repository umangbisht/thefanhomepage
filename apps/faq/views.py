from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.base import ObjectDoesNotExist
from apps.languages.models import Language
from apps.faq.models import Faq, FaqDescription
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
import urllib
from django.db.models import Q
import os
import datetime
from django.core.files.storage import FileSystemStorage
import re
from django.conf import settings


VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]

@login_required(login_url='/login/')
def index(request):
	DB = Faq.objects
	if request.GET.get('page_name'):
		page_name= request.GET.get('page_name').strip()
		DB = DB.filter(page_name__icontains= page_name)
	
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
	}
	return render(request,"faq/index.html",context)

@login_required(login_url='/login/')
def add(request):
	languages	 = Language.objects.filter(is_active=1).all()
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
			
		if request.POST.get("data[en][question]") == None or request.POST.get("data[en][question]") == "":
			validationErrors["question"]	=	"The question field is required."
			
		if request.POST.get("data[en][answer]") == None or request.POST.get("data[en][answer]") == "":
			validationErrors["answer"]	=	"The answer field is required."

		if not validationErrors:
			Obj						=	Faq()
			Obj.question			=	request.POST.get("data[en][question]")
			Obj.answer				=	request.POST.get("data[en][answer]")		
			Obj.pagename				=	request.POST.get("pagename")		
			Obj.save()
			
			lastId	=	Obj.id
			for language in languages:
				Obj						=	FaqDescription()
				Obj.faq_id				=	lastId
				Obj.language_code		=	language.lang_code
				Obj.question			=	request.POST.get("data["+language.lang_code+"][question]")
				Obj.answer				=	request.POST.get("data["+language.lang_code+"][answer]")
				Obj.save()


			messages.success(request,"Faq has been added successfully.")
			return redirect('/faq/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"languages":languages,
	}
	return render(request,"faq/add.html",context)
	
@login_required(login_url='/login/')
def edit(request,id):
	FaqDetail	 				= Faq.objects.filter(id=id).first()
	if not FaqDetail:
		return redirect('/dashboard/')
		
	FaqDescriptionDetail	 	= FaqDescription.objects.filter(faq_id=id).all()	
	faqLanguageDetails = {}	
	if FaqDescriptionDetail:
		for descriptionDetails in FaqDescriptionDetail:
			newArr = {}
			newArr['question'] = descriptionDetails.question
			newArr['answer'] = descriptionDetails.answer
			faqLanguageDetails[descriptionDetails.language_code] = newArr
			
	languages	 = Language.objects.filter(is_active=1).all()
	form				=	FaqDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		print(request.POST.get("data[en][question]"))
		print(request.POST.get("data[en][answer]"))

		if request.POST.get("data[en][question]") == None or request.POST.get("data[en][question]") == "":
			validationErrors["question"]	=	"The question field is required."
			
		if request.POST.get("data[en][answer]") == None or request.POST.get("data[en][answer]") == "":
			validationErrors["answer"]	=	"The answer field is required."
			
		if not validationErrors:
			Obj						=	FaqDetail
			Obj.question			=	request.POST.get("data[en][question]")
			Obj.answer				=	request.POST.get("data[en][answer]")
			Obj.pagename			=	request.POST.get("pagename")

			Obj.save()

			lastId	=	Obj.id
			FaqDescription.objects.filter(faq_id=lastId).delete()
			for language in languages:
				Obj						=	FaqDescription()
				Obj.faq_id				=	lastId
				Obj.language_code		=	language.lang_code
				Obj.question			=	request.POST.get("data["+language.lang_code+"][question]")
				Obj.answer				=	request.POST.get("data["+language.lang_code+"][answer]")
				Obj.save()

			messages.success(request,"Faq has been updated successfully.")
			return redirect('/faq/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"languages":languages,
		"FaqDetail":FaqDetail,
		"faqLanguageDetails":faqLanguageDetails,
	}
	return render(request,"faq/edit.html",context)


@login_required(login_url='/login/')
def changeStatus(request,id,status):
    FaqDetail	 =  Faq.objects.filter(id=id).first()
    if not FaqDetail:
        return redirect('/faq/')
    if status=="1":
        FaqDetail.is_active= 1
        FaqDetail.save()
        message = 'Faq has been Activated successfully.' 
    else:
        FaqDetail.is_active= 0
        FaqDetail.save()
        message = 'Faq has been Deactivated successfully.' 
    messages.success(request,message) 
    return redirect('faq.index')
	
