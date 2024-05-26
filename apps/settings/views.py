from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.base import ObjectDoesNotExist
from apps.settings.models import Setting
from apps.users.models import Upload
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode 
import urllib
from django.http import JsonResponse
from django.db.models import Q
import os
import sys
import datetime
from django.core.files.storage import FileSystemStorage
import re
from django.core.files import File
import os.path
from os import path
import pathlib
from django.utils.deprecation import MiddlewareMixin
import fileinput
from django.conf import settings
from os import fdopen, remove
from shutil import move
import random

VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]
@login_required(login_url='/login/')
def index(request):
	DB = Setting.objects
	if request.GET.get('title'):
		title=request.GET.get('title').strip()
		DB = DB.filter(title__icontains= title )

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
	return render(request, "settings/index.html", context)

# this function add data
@login_required(login_url='/login/')
def add(request):
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST["title"] == "":
			validationErrors["title"]	=	"The title field is required."
			
		if request.POST["key"] == "":
			validationErrors["key"]	=	"The key field is required."
			
		if request.POST['input_type'] != 'file' and request.POST['input_type'] != 'checkbox' :	
			if request.POST["value"] == "":
				validationErrors["value"]	=	"The value field is required."
				
		if request.POST["input_type"] == "":
			validationErrors["input_type"]	=	"The input type field is required."


		if request.POST['input_type'] == 'file':
			if len(request.FILES) > 0:
				file = request.FILES['attchment'].name
				extension = file.split(".")[-1].lower()
				if not extension in VALID_IMAGE_EXTENSIONS:
					validationErrors["attchment"]	=	"This is not an valid image. Please upload a valid image."
			else:
				validationErrors["attchment"]	=	"The attachment field is required."
				
		if not validationErrors:
			profile_photo	=	""
			if request.method == 'POST' and len(request.FILES) != 0:
				currentMonth = datetime.datetime.now().month
				currentYear = datetime.datetime.now().year
					
				myfile = request.FILES['attchment']
				
				filename = myfile.name.split(".")[0].lower()
				extension = myfile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
	
				imageValue	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(myfile, "setting_images/"+imageValue)
				if imageValue:
					settingss				= Setting()	
					settingss.title			= request.POST["title"]
					settingss.key 			= request.POST["key"]
					settingss.value 		= imageValue
					settingss.input_type 	= request.POST["input_type"]
					settingss.editable 		= 1
					settingss.save()
			else:
				settingss				=	Setting()	
				if request.POST['input_type'] == 'checkbox' :
					settingss.value			= 1
				else:
					settingss.value			= request.POST["value"]
					
				settingss.title			= request.POST["title"]
				settingss.key 			= request.POST["key"]
				settingss.input_type 	= request.POST["input_type"]
				settingss.editable 		= 1
				settingss.save()	
			
			site_custom_global_constants_file_write()
			messages.success(request," Setting has been added successfully.")
			return redirect('/settings/')

	context		=	{
		"form":form,
		"errors":validationErrors
	}
	return render(request,"settings/add.html",context)

# this function edit data 
@login_required(login_url='/login/')
def edit(request,id):
	settingsDetail	 = Setting.objects.filter(id=id).first()
	if not settingsDetail	:
		return redirect('/settings/')

	form				=	settingsDetail
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if request.POST["title"] == "":
			validationErrors["title"]	=	"The title field is required."
			
		if request.POST["key"] == "":
			validationErrors["key"]	=	"The key field is required."
			
		if request.POST['input_type'] != 'file' and request.POST['input_type'] != 'checkbox' :	
			if request.POST["value"] == "":
				validationErrors["value"]	=	"The value field is required."
				
		if request.POST["input_type"] == "":
			validationErrors["input_type"]	=	"The input type field is required."


		if request.POST['input_type'] == 'file' and len(request.FILES) > 0:
			file = request.FILES['attchment'].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["attchment"]	=	"This is not an valid image. Please upload a valid image."
				
		if not validationErrors:
			profile_photo	=	""
			if request.POST['input_type'] == 'file' and len(request.FILES) > 0:
				currentMonth = datetime.datetime.now().month
				currentYear = datetime.datetime.now().year
					
				myfile = request.FILES['attchment']
				
				filename = myfile.name.split(".")[0].lower()
				extension = myfile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension	
				imageValue	=	str(currentMonth)+str(currentYear)+"/"+newfilename

				Upload.upload_image_on_gcp(myfile, "setting_images/"+imageValue)
				if imageValue:
					settingss				= settingsDetail	
					settingss.title			= request.POST["title"]
					settingss.key 			= request.POST["key"]
					settingss.value 		= imageValue
					settingss.input_type 	= request.POST["input_type"]
					settingss.editable 		= 1
					settingss.save()
			elif request.POST['input_type'] != 'file':
				settingss				=	settingsDetail	
				if request.POST['input_type'] == 'checkbox' :
					settingss.value			= 1
				else:
					settingss.value			= request.POST["value"]
					
				settingss.title			= request.POST["title"]
				settingss.key 			= request.POST["key"]
				settingss.input_type 	= request.POST["input_type"]
				settingss.editable 		= 1
				settingss.save()	
			
			site_custom_global_constants_file_write()
			messages.success(request," Setting has been updated successfully.")
			return redirect('/settings/')

	context		=	{
		"form":form,
		"errors":validationErrors,
		"settingsDetail":settingsDetail
	}
	return render(request,"settings/edit.html",context)

# this function use for delete data
@login_required(login_url='/login/')
def delete(request,id):
	Setting.objects.filter(id=id).delete()
	site_custom_global_constants_file_write()
	return redirect('/settings/')
	
#this function use for settings prefix	
@login_required(login_url='/login/')
def prefix(request,key):
	test	=	settings.MEDIA_ROOT
	#return HttpResponse(test)
	results=Setting.objects.filter(key__icontains=key).filter(editable=1).all()
	context={
		"results":results,
		"key":key,
	}
	return render(request,"settings/prefix.html",context)

# this function user for UpdatePrifix data 
def updatePrifix(request,key):
	if request.method	==	"POST":
		results=Setting.objects.filter(key__icontains=key).filter(editable=1).all()
		if results !=  None :
			for result in results: 
				if result.input_type == 'file' :	
					if len(request.FILES) != 0:
						for fileResult in request.FILES:
							if request.method == 'POST' and len(request.FILES) != 0:
								currentMonth = datetime.datetime.now().month
								currentYear = datetime.datetime.now().year
								folder = 'media/uploads/setting_images/'+str(currentMonth)+str(currentYear)+"/"
								folder_directory = 'uploads/setting_images/'+str(currentMonth)+str(currentYear)+"/"
								if not os.path.exists(folder):
									os.mkdir(folder)

								myfile = request.FILES[fileResult]
								fs = FileSystemStorage()
								filename = myfile.name.split(".")[0].lower()
								extension = myfile.name.split(".")[-1].lower()
								newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
								fs.save(folder_directory+newfilename, myfile)	
								imageValue	=	str(currentMonth)+str(currentYear)+"/"+newfilename

								settingsObj			=	Setting.objects.filter(id=result.id).first()	
								if imageValue:
									settingsObj.value 	= 	imageValue
									settingsObj.save()
					
						
				else:
					settingsObj			=	Setting.objects.filter(id=result.id).first()
					if result.input_type == 'checkbox' :
						if request.POST.get(result.key) == '1':
							settingsObj.value 	= 	1
						else:
							settingsObj.value 	= 	0
					else:
						settingsObj.value 	= 	request.POST.get(result.key)
					settingsObj.save()

	site_custom_global_constants_file_write()
	return redirect('settings.prefix' ,key=key )
	
@login_required(login_url='/login/')
def delete_image(request):
	id = request.GET.get('id', None)
	data = {}
	data['success'] = 0
	resultall=Setting.objects.all()
	settingsDetail = Setting.objects.filter(id=id).first()
	if settingsDetail:
		settingsDetail.value = ''
		settingsDetail.save()
		data['success'] = 1
		
	site_custom_global_constants_file_write()
	return JsonResponse(data)  

def site_custom_global_constants_file_write():
	results=Setting.objects.all()
	for item in results:	
		data        =  ''
		settingKey	=	item.key.replace(".","")
		settingKey	=	settingKey.upper()
		data       	=  settingKey +'="'+item.value+'"'
		old       	=  settingKey +'='

		fileObj	=	open('tfh/settings.py').read()
		if old in fileObj:	
			for line in fileinput.input("tfh/settings.py", inplace=True):
				if line.strip().startswith(old):
					line = settingKey +'="'+item.value+'"\n'
				sys.stdout.write(line)
		else:
			output_file =  'tfh/settings.py'
			fileObj     =    open(output_file, "a")
			data       	=  settingKey +'="'+item.value+'"'
			fileObj.write(data+ '\n')
			fileObj.close();

