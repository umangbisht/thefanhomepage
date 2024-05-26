from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,ModelFollower,ModelNotificationSetting,UserSubscriptionPlan,PrivateFeedModel,TransactionHistory,TipMe,ModelViews, Upload
from apps.cmspages.models import CmsPage,CmsPageDescription
from apps.newsletters.models import NewsletterSubscriber
from apps.api.models import ReportReasonModel
from apps.slider.models import SliderImage
from apps.supports.models import Support
from apps.blocks.models import Block,BlockDescription
from apps.dropdownmanger.models import DropDownManagerDescription,DropDownManager
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
import os
import datetime
from django.core.files.storage import FileSystemStorage
import re
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from PIL import Image
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework_jwt.settings import api_settings
from django.http import JsonResponse
from django.conf import settings
import hashlib
import json
from collections import namedtuple
from django.core.mail import send_mail, BadHeaderError,EmailMessage,EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _
from django.utils import translation
import random
import socket
from django.db.models import Count

# Create your views here.

VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]

@login_required(login_url='/login/')
def index_slider(request):
    DB = SliderImage.objects
    # if request.GET.get('subject'):
    #     subject = request.GET.get('subject').strip()
    #     DB = DB.filter(subject__icontains=subject)

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
    max_index = len(paginator.page_range)
    start_index = index - 3 if index >= 3 else 0
    end_index = index + 3 if index <= max_index - 3 else max_index
    page_range = list(paginator.page_range)[start_index:end_index]

    context		=	{
        'results': results,
        'page': page,
        'page_range': page_range,
        'order_by': order_by,
        'direction': direction,
    }
    return render(request,"slider/index_slider.html",context)

@login_required(login_url='/login/')
def add_slider(request):
    form				=	""
    validationErrors	=	{}
    if request.method	==	"POST":
        form			=	request.POST
		
        if request.POST.get("title") == "":
            validationErrors["title"]	=	"The title field is required."

        if request.POST.get("description") == "":
            validationErrors["description"]	=	"The description field is required."

        if request.POST.get("order") == "":
            validationErrors["order"]	=	"The order field is required."
        
        if SliderImage.objects.filter(order=request.POST.get("order")).exists():
            validationErrors["order"]	=	"The order should be different. Try another order."
        
        if len(request.FILES) == 0:
            validationErrors["slider"]	=	"Please select Slider Image"
        else:
            image = request.FILES.get("slider")
            file = image.name
            extension = file.split(".")[-1].lower()
            if not extension in VALID_IMAGE_EXTENSIONS:
                validationErrors["slider"]	=	"This is not a valid image. Please upload a valid image."
			
        if not validationErrors:
            currentMonth = datetime.datetime.now().month
            currentYear = datetime.datetime.now().year

            slider_image  = ''

            if request.FILES.get("slider"):
                sliderFile = request.FILES.get("slider")
                filename = sliderFile.name.split(".")[0].lower()
                extension = sliderFile.name.split(".")[-1].lower()
                newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
                slider_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
                Upload.upload_image_on_gcp(sliderFile, "slider_images/"+slider_image)	

            Obj					= 	SliderImage()
            Obj.slider 		    = 	slider_image
            Obj.title 		    = 	request.POST.get("title")
            Obj.description 	= 	request.POST.get("description")
            Obj.order 			= 	request.POST.get("order")
            Obj.save()

            messages.success(request,"Slider has been added successfully.")
            return redirect('/slider/')
	
    context		=	{
        "form":form,
        "errors":validationErrors,
    }
    return render(request,"slider/add_slider.html",context)

@login_required(login_url='/login/')
def editSlider(request,id):
    sliderDetail = SliderImage.objects.filter(id=id).first()
    orderDiffer = SliderImage.objects.filter(id=id).first()

    if not sliderDetail:
        return redirect('/slider/')
    form				=	""
    validationErrors	=	{}
    if request.method	==	"POST":
        form			=	request.POST

        if request.POST.get("title") == "":
            validationErrors["title"]	=	"The title field is required."

        if request.POST.get("description") == "":
            validationErrors["description"]	=	"The description field is required."

        if request.POST.get("order") == "":
            validationErrors["order"]	=	"The order field is required."
        else:
            if SliderImage.objects.filter(order=request.POST.get("order")).exclude(id=id).exists():
                validationErrors["order"]	=	"This order already exists."
        
        # if SliderImage.objects.filter(order=request.POST.get("order")).exists():
        #     validationErrors["order"]	=	"The order should be different. Try another order."
        
        # if len(request.FILES) == 0:
        #     validationErrors["slider"]	=	"Please select Slider Image"
        if len(request.FILES) != 0:
            image = request.FILES.get("slider")
            file = image.name
            extension = file.split(".")[-1].lower()
            if not extension in VALID_IMAGE_EXTENSIONS:
                validationErrors["slider"]	=	"This is not a valid image. Please upload a valid image."
			
        if not validationErrors:
            currentMonth = datetime.datetime.now().month
            currentYear = datetime.datetime.now().year

            slider_image  = ''

            Obj					= 	sliderDetail
            Obj.title 		    = 	request.POST.get("title")
            Obj.description 	= 	request.POST.get("description")
            Obj.order 			= 	request.POST.get("order")

            if request.FILES.get("slider"):
                sliderFile = request.FILES.get("slider")
                filename = sliderFile.name.split(".")[0].lower()
                extension = sliderFile.name.split(".")[-1].lower()
                newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
                slider_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
                Upload.upload_image_on_gcp(sliderFile, "slider_images/"+slider_image)
                Obj.slider 		    = 	slider_image
            Obj.save()

            messages.success(request,"Slider has been edited successfully.")
            return redirect('/slider/')
	
    context		=	{
        "form":form,
        "errors":validationErrors,
        "sliderDetail":sliderDetail
    }
    return render(request,"slider/edit_slider.html",context)


@login_required(login_url='/login/')
def deleteSlider(request,id):
	SliderImage.objects.filter(id=id).delete()
	messages.success(request,"Slider image has been deleted successfully.")
	return redirect('/slider/')


@login_required(login_url='/login/')
def changeStatusSlider(request,id,status):
    sliderDetail = SliderImage.objects.filter(id=id).first()
    if status=="1":
        sliderDetail.is_active= 1
        sliderDetail.save()
        message = 'Slider has been Activated successfully.' 
    else:
        sliderDetail.is_active= 0
        sliderDetail.save()
        message = 'Slider has been Deactivated successfully.' 
    messages.success(request,message) 
    return redirect('/slider/')