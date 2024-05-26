from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.base import ObjectDoesNotExist
from apps.users.models import User,ModelCategories
from apps.languages.models import Language
from apps.dropdownmanger.models import DropDownManager,DropDownManagerDescription
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
import urllib
from django.db.models import Q
import os
import datetime
from django.conf import settings

# Create your views here.

@login_required(login_url='/login/')
def index(request,dropdown_type):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	DB = DropDownManager.objects
	if request.GET.get('name'):
		name= request.GET.get('name').strip()
		DB = DB.filter(name__icontains= name)
	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	DB = DB.filter(dropdown_type=dropdown_type)
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
	
	dropdown_type_text		=	dropdown_type
	dropdown_type_text		=	dropdown_type_text.replace("-" ," ")

	context		=	{
		'results': results,
		'page': page,
		'page_range': page_range,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'dropdown_type_text': dropdown_type_text,
		'dropdown_type': dropdown_type,
		'datetimeFormat':datetimeFormat
	}
	return render(request,"dropdownmanager/index.html",context)

@login_required(login_url='/login/')
def add(request,dropdown_type):
	languages	 = Language.objects.filter(is_active=1).all()
	dropdown_type_text		=	dropdown_type
	dropdown_type_text		=	dropdown_type_text.replace("-" ," ")
		
	form				=	{}

	if "en" not in form:
		form["en"]	=	{}

		if "name" not in form["en"]:
			form["en"]["name"]	=	{}

		if "ar" not in form:
			form["ar"]	=	{}

		if "name" not in form["ar"]:
			form["ar"]["name"]	=	{}

		form["en"]["name"]	=	"english"
		form["ar"]["name"]	=	"arbic"
		form["ar_name"]		=	"arbic"
		form["en_name"]		=	"english"

	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST.get("data[en][name]") == None or request.POST.get("data[en][name]") == "":
			validationErrors["name"]	=	"The name field is required."
		else:
			if DropDownManager.objects.filter(name=request.POST.get("data[en][name]")).exists():
				validationErrors["name"]	=	"This name is already exists."
		
			
		if not validationErrors:
			Obj					=	DropDownManager()
			Obj.name			=	request.POST.get("data[en][name]")
			Obj.slug			=	request.POST.get("data[en][name]").replace(" ","-")
			Obj.dropdown_type	=	dropdown_type
			Obj.save()

			lastId	=	Obj.id
			for language in languages:
				Obj						=	DropDownManagerDescription()
				Obj.dropdown_manger_id	=	lastId
				Obj.language_code		=	language.lang_code
				Obj.name				=	request.POST.get("data["+language.lang_code+"][name]")
				Obj.save()

			messages.success(request,dropdown_type_text.capitalize()+" has been added successfully.")
			return redirect('/dropdown-managers/'+dropdown_type)

	context		=	{
		"form":form,
		"errors":validationErrors,
		"dropdown_type_text":dropdown_type_text,
		"dropdown_type":dropdown_type,
		"languages":languages,
	}
	return render(request,"dropdownmanager/add.html",context)
	
@login_required(login_url='/login/')
def edit(request,dropdown_type,id):
	DropDownManagerDetail	 = DropDownManager.objects.filter(id=id).first()
	if not DropDownManagerDetail:
		return redirect('/dashboard/')
		
	dropDownDescriptionDetail	 	= DropDownManagerDescription.objects.filter(dropdown_manger_id=id).all()
	
	dropDownLanguageDetails = {}	
	if dropDownDescriptionDetail:
		for descriptionDetails in dropDownDescriptionDetail:
			newArr = {}
			newArr['name'] = descriptionDetails.name
			dropDownLanguageDetails[descriptionDetails.language_code] = newArr
		
	languages	 = Language.objects.filter(is_active=1).all()
	dropdown_type_text		=	dropdown_type
	dropdown_type_text		=	dropdown_type_text.replace("_" ," ")
		
	form				=	DropDownManagerDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST.get("data[en][name]") == None or request.POST.get("data[en][name]") == "":
			validationErrors["name"]	=	"The name field is required."
		else :
			if DropDownManager.objects.filter(name=request.POST.get("data[en][name]")).exclude(id=id).exists():
				validationErrors["name"]	=	"This name is already exists."
			
		if not validationErrors:
			Obj					=	DropDownManagerDetail
			Obj.name			=	request.POST.get("data[en][name]")
			Obj.slug			=	request.POST.get("data[en][name]").replace(" ","-")
			Obj.dropdown_type	=	dropdown_type
			Obj.save()

			lastId	=	Obj.id
			DropDownManagerDescription.objects.filter(dropdown_manger_id=lastId).delete()
			for language in languages:
				Obj						=	DropDownManagerDescription()
				Obj.dropdown_manger_id	=	lastId
				Obj.language_code		=	language.lang_code
				Obj.name				=	request.POST.get("data["+language.lang_code+"][name]")
				Obj.save()

			messages.success(request,dropdown_type_text.capitalize()+" has been updated successfully.")
			return redirect('/dropdown-managers/'+dropdown_type)

	context		=	{
		"form":form,
		"errors":validationErrors,
		"dropdown_type_text":dropdown_type_text,
		"dropdown_type":dropdown_type,
		"languages":languages,
		"DropDownManager":DropDownManagerDetail,
		"dropDownLanguageDetails":dropDownLanguageDetails,
	}
	return render(request,"dropdownmanager/edit.html",context)
	
@login_required(login_url='/login/')
def changeStatus(request,id,status,dropdown_type):
	dropdown_type_text		=	dropdown_type
	dropdown_type_text		=	dropdown_type_text.replace("_" ," ")
	
	dropdownmanager				=	DropDownManager.objects.filter(id=id).first()
	if status == "0":
		messages.success(request,dropdown_type_text.capitalize()+" has been activated successfully.")
		dropdownmanager.is_active		=	1
	else:
		messages.success(request,dropdown_type_text.capitalize()+" has been deactivated successfully.")
		dropdownmanager.is_active		=	0

	dropdownmanager.save()
	return redirect('/dropdown-managers/'+dropdown_type)

@login_required(login_url='/login/')
def deleteDropDown(request,dropdown_type,id):
	dropdown_type_text		=	dropdown_type
	dropdown_type_text		=	dropdown_type_text.replace("_" ," ")
	############ Delete Report Reason ############
	dropdownReportReason	=	DropDownManager.objects.filter(dropdown_type='report-reason').filter(id=id).first()
	if dropdownReportReason:
		reportReasonDescription	=	DropDownManagerDescription.objects.filter(dropdown_manger_id=id).all()
		if reportReasonDescription:
			for reason in reportReasonDescription:
				reason.delete()
		dropdownReportReason.delete()

	############ Delete Category #################	
	dropdownCategory	=	DropDownManager.objects.filter(dropdown_type='category').filter(id=id).first()
	modelCategory		=	ModelCategories.objects.all().values('dropdown_manager_id')
	modelselectcategory	= DropDownManager.objects.filter(dropdown_type='category').filter(id=id).filter(id__in=modelCategory)
	if not modelselectcategory:
		if dropdownCategory:
			categoryDescription	=	DropDownManagerDescription.objects.filter(dropdown_manger_id=id).all()
			if categoryDescription:
				for category in categoryDescription:
					category.delete()
			dropdownCategory.delete()
	if modelselectcategory:
		messages.success(request,"This category is selected by some model so unable to delete this category.")
		return redirect('/dropdown-managers/'+dropdown_type)
	
	############### Delete Country ################
	dropdownCountry		=	DropDownManager.objects.filter(dropdown_type='country').filter(id=id).first()
	modelCountry		=	User.objects.filter(is_deleted=0).all().values("country")
	modelselectcountry	= DropDownManager.objects.filter(dropdown_type='country').filter(id=id).filter(id__in=modelCountry)
	if not modelselectcountry:
		if dropdownCountry:
			countryDescription	=	DropDownManagerDescription.objects.filter(dropdown_manger_id=id).all()
			if countryDescription:
				for country in countryDescription:
					country.delete()
			dropdownCountry.delete()
	if modelselectcountry:
		messages.success(request,"This country is selected by some model so unable to delete this country.")
		return redirect('/dropdown-managers/'+dropdown_type)
	messages.success(request,dropdown_type_text.capitalize()+" has been deleted successfully.")
	return redirect('/dropdown-managers/'+dropdown_type)

