from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.base import ObjectDoesNotExist
from apps.languages.models import Language
from apps.blocks.models import Block,BlockDescription
from apps.users.models import Upload
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
	DB = Block.objects
	if request.GET.get('page_name'):
		page_name= request.GET.get('page_name').strip()
		DB = DB.filter(page_name__icontains= page_name)
	
	if request.GET.get('block_name'):
		block_name= request.GET.get('block_name').strip()
		DB = DB.filter(block_name__icontains= block_name)
	
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
	return render(request,"blocks/index.html",context)

@login_required(login_url='/login/')
def add(request):
	languages	 = Language.objects.filter(is_active=1).all()
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST.get("page_name") == None or request.POST.get("page_name") == "":
			validationErrors["page_name"]	=	"The page name field is required."
		
		if request.POST.get("block_order") == None or request.POST.get("block_order") == "":
			validationErrors["block_order"]	=	"The order field is required."
		else:
			if Block.objects.filter(block_order=request.POST.get("block_order")).exists():
				validationErrors["block_order"]	=	"This block order is already exists."
			
		if request.POST.get("data[en][block_name]") == None or request.POST.get("data[en][block_name]") == "":
			validationErrors["block_name"]	=	"The block name field is required."
		else:
			if Block.objects.filter(block_name=request.POST.get("data[en][block_name]")).exists():
				validationErrors["block_name"]	=	"This block name is already exists."

		if request.POST.get("data[en][description]") == None or request.POST.get("data[en][description]") == "":
			validationErrors["description"]	=	"The description field is required."
			
		if len(request.FILES) > 0:
			file = request.FILES["attachment"].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["attachment"]	=	"The image an not valid image. Please upload a valid image. Valid extenstions are jpg,jpeg,png,gif"

		if not validationErrors:
			Obj						=	Block()
			Obj.page_name			=	request.POST.get("page_name")
			Obj.block_order			=	request.POST.get("block_order")
			Obj.block_name			=	request.POST.get("data[en][block_name]")
			Obj.slug				=	request.POST.get("data[en][block_name]").replace(" ","-")
			Obj.page_slug				=	request.POST.get("page_name").replace(" ","-")
			Obj.description			=	request.POST.get("data[en][description]")
			attachment	=	""
			if request.method == 'POST' and len(request.FILES) > 0:
				currentMonth = datetime.datetime.now().month
				currentMonth = str(currentMonth)
				if len(currentMonth) < 2:
					currentMonth = '0'+currentMonth
				currentYear = datetime.datetime.now().year

					
				myfile = request.FILES['attachment']
				filename = myfile.name.split(".")[0].lower()
				extension = myfile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+"."+extension	
				attachment	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(myfile, "block_images/"+attachment)

			Obj.image			=	attachment
			Obj.save()

			lastId	=	Obj.id
			for language in languages:
				Obj						=	BlockDescription()
				Obj.block_id			=	lastId
				Obj.language_code		=	language.lang_code
				Obj.block_name			=	request.POST.get("data["+language.lang_code+"][block_name]")
				Obj.description			=	request.POST.get("data["+language.lang_code+"][description]")
				Obj.save()

			messages.success(request,"Block has been added successfully.")
			return redirect('/blocks/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"languages":languages,
	}
	return render(request,"blocks/add.html",context)
	
@login_required(login_url='/login/')
def edit(request,id):
	BlockDetail	 				= Block.objects.filter(id=id).first()
	if not BlockDetail:
		return redirect('/dashboard/')
		
	BlockDescriptionDetail	 	= BlockDescription.objects.filter(block_id=id).all()	
	blockLanguageDetails = {}	
	if BlockDescriptionDetail:
		for descriptionDetails in BlockDescriptionDetail:
			newArr = {}
			newArr['name'] = descriptionDetails.block_name
			newArr['description'] = descriptionDetails.description
			blockLanguageDetails[descriptionDetails.language_code] = newArr
			
	languages	 = Language.objects.filter(is_active=1).all()
	form				=	BlockDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST.get("page_name") == None or request.POST.get("page_name") == "":
			validationErrors["page_name"]	=	"The page name field is required."
		
		if request.POST.get("block_order") == None or request.POST.get("block_order") == "":
			validationErrors["block_order"]	=	"The order field is required."
		else:
			if Block.objects.filter(block_order=request.POST.get("block_order")).exclude(id=id).exists():
				validationErrors["block_order"]	=	"This block order is already exists."
			
		if request.POST.get("data[en][block_name]") == None or request.POST.get("data[en][block_name]") == "":
			validationErrors["block_name"]	=	"The block name field is required."
		else:
			if Block.objects.filter(block_name=request.POST.get("data[en][block_name]")).exclude(id=id).exists():
				validationErrors["block_name"]	=	"This block name is already exists."

		if request.POST.get("data[en][description]") == None or request.POST.get("data[en][description]") == "":
			validationErrors["description"]	=	"The description field is required."
			
		if len(request.FILES) > 0:
			file = request.FILES["attachment"].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["attachment"]	=	"The image an not valid image. Please upload a valid image. Valid extenstions are jpg,jpeg,png,gif"

		if not validationErrors:
			Obj						=	BlockDetail
			Obj.page_name			=	request.POST.get("page_name")
			Obj.block_order			=	request.POST.get("block_order")
			Obj.block_name			=	request.POST.get("data[en][block_name]")
			Obj.description			=	request.POST.get("data[en][description]")
			if request.method == 'POST' and len(request.FILES) > 0:
				currentMonth = datetime.datetime.now().month
				currentMonth = str(currentMonth)
				if len(currentMonth) < 2:
					currentMonth = '0'+currentMonth
				currentYear = datetime.datetime.now().year
					
				myfile = request.FILES['attachment']
				filename = myfile.name.split(".")[0].lower()
				extension = myfile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+"."+extension
				attachment	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				print(newfilename)
				print(attachment)
				Upload.upload_image_on_gcp(myfile, "block_images/"+attachment)
				Obj.image			=	attachment

			Obj.save()

			lastId	=	Obj.id
			BlockDescription.objects.filter(block_id=lastId).delete()
			for language in languages:
				Obj						=	BlockDescription()
				Obj.block_id			=	lastId
				Obj.language_code		=	language.lang_code
				Obj.block_name			=	request.POST.get("data["+language.lang_code+"][block_name]")
				Obj.description			=	request.POST.get("data["+language.lang_code+"][description]")
				Obj.save()

			messages.success(request,"Block has been updated successfully.")
			return redirect('/blocks/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"languages":languages,
		"BlockDetail":BlockDetail,
		"blockLanguageDetails":blockLanguageDetails,
	}
	return render(request,"blocks/edit.html",context)


@login_required(login_url='/login/')
def changeStatus(request,id,status):
    BlockDetail	 =  Block.objects.filter(id=id).first()
    if not BlockDetail:
        return redirect('/blocks/')
    if status=="1":
        BlockDetail.is_active= 1
        BlockDetail.save()
        message = 'Block has been Activated successfully.' 
    else:
        BlockDetail.is_active= 0
        BlockDetail.save()
        message = 'Block has been Deactivated successfully.' 
    messages.success(request,message) 
    return redirect('blocks.index')
	
