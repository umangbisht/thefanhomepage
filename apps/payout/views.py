from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,Payout
from apps.dropdownmanger.models import DropDownManager 
from apps.users.models import Upload 
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
from django.template.loader import get_template
import os
import datetime
import json
from django.core.mail import send_mail, BadHeaderError,EmailMessage,EmailMultiAlternatives
from django.core.files.storage import FileSystemStorage
import re
from django.utils.html import strip_tags
from django.template import Context
#from django.shortcuts import render_to_response
from django.conf import settings
from PIL import Image
from decimal import Decimal
import decimal
import random


# Create your views here.
VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]



@login_required(login_url='/login')

def indexPayout(request):
	# userDetail =    User.objects.all().values("id")
	dateFormat  =   settings.READINGDATE_FORMAT
	DB = Payout.objects.all()

	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model__model_name__icontains= model_name)

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
		
	if results:
		for result in results:
			result.gross_revenue	=	round(decimal.Decimal(result.gross_revenue),2)
			result.net_revenue	=	round(decimal.Decimal(result.net_revenue),2)
		
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
		'page': page,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
		'dateFormat':dateFormat
	}
	return render(request, "payout/index.html",context)

@login_required(login_url='/login/')
def uploadPaySlip(request):
	id = request.POST.get("payout_id")
	
	userpaySlip			=	Payout.objects.filter(id=id).first()
	if not userpaySlip:
		return redirect('/payout/')
	form				=	{}
	validationErrors	=	{}
	if request.method	==	"POST":
		if request.FILES.get('payslip_img') ==None or request.FILES.get("payslip_img") == "":
			validationErrors["payslip_img"]	=	"Please select an image"
		else:
			payslip_img = request.FILES.get("payslip_img")
			file = payslip_img.name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["payslip_img"]	=	"This is not a valid image. Please upload a valid featured image."

		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year
			folder = 'media/uploads/payout_slips/'+str(currentMonth)+str(currentYear)+"/"
			folder_directory = 'uploads/payout_slips/'+str(currentMonth)+str(currentYear)+"/"
			if not os.path.exists(folder):
				os.mkdir(folder)

			if request.FILES.get("payslip_img"):
				payslipFile = request.FILES.get("payslip_img")
				filename = payslipFile.name.split(".")[0].lower()
				extension = payslipFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension

				payslip_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				print(newfilename)
				print(payslip_image)
				Upload.upload_image_on_gcp(payslipFile, "payout_slips/"+payslip_image)
				payment_method = request.POST.get("payment_method")
				userFeatImg1						=	userpaySlip
				userFeatImg1.pay_slip		        =	payslip_image
				userFeatImg1.is_paid		        =	1
				userFeatImg1.payment_method		    =	payment_method
				userFeatImg1.save()
				message = "Payout Mark as paid successfully."
				messages.success(request,message) 

		else:
			message = validationErrors["payslip_img"]
			messages.error(request,message) 
		
		
		return redirect('/payout/')
	
@login_required(login_url='/login/')
def editPayout(request,id):
	payoutDetail = Payout.objects.filter(id=id).first()
	payoutDetail.gross_revenue	=	round(decimal.Decimal(payoutDetail.gross_revenue),2)
	payoutDetail.net_revenue	=	round(decimal.Decimal(payoutDetail.net_revenue),2)
	payoutDetail.commission_amount	=	round(decimal.Decimal(payoutDetail.commission_amount),2)
	payoutDetail.rebill_gross_revenue	=	round(decimal.Decimal(payoutDetail.rebill_gross_revenue),2)
	payoutDetail.rebill_net_revenue	=	round(decimal.Decimal(payoutDetail.rebill_net_revenue),2)
	payoutDetail.rebill_commission	=	round(decimal.Decimal(payoutDetail.rebill_commission),2)
	payoutDetail.join_gross_revenue	=	round(decimal.Decimal(payoutDetail.join_gross_revenue),2)
	payoutDetail.join_net_revenue	=	round(decimal.Decimal(payoutDetail.join_net_revenue),2)
	payoutDetail.join_commission	=	round(decimal.Decimal(payoutDetail.join_commission),2)
	payoutDetail.tip_gross_revenue	=	round(decimal.Decimal(payoutDetail.tip_gross_revenue),2)
	payoutDetail.tip_net_revenue	=	round(decimal.Decimal(payoutDetail.tip_net_revenue),2)
	payoutDetail.tip_commission	=	round(decimal.Decimal(payoutDetail.tip_commission),2)
	payoutDetail.refunds_gross_revenue	=	round(decimal.Decimal(payoutDetail.refunds_gross_revenue),2)
	payoutDetail.refunds_net_revenue	=	round(decimal.Decimal(payoutDetail.refunds_net_revenue),2)
	payoutDetail.refunds_commission	=	round(decimal.Decimal(payoutDetail.refunds_commission),2)
	
	if not payoutDetail:
		return redirect('/payout/')
		
	form				=	""
	validationErrors	=	{}
	if request.method	==	"POST":
		form			=	request.POST
		if not validationErrors:
			Obj								= 	payoutDetail
			Obj.gross_revenue 		    	= 	request.POST.get("gross_revenue")
			Obj.net_revenue 				= 	request.POST.get("net_revenue")
			Obj.commission_amount 			= 	request.POST.get("commission_amount")
			Obj.rebill_gross_revenue 		= 	request.POST.get("rebill_gross_revenue")
			Obj.rebill_net_revenue 			= 	request.POST.get("rebill_net_revenue")
			Obj.rebill_commission 			= 	request.POST.get("rebill_commission")
			Obj.join_gross_revenue 			= 	request.POST.get("join_gross_revenue")
			Obj.join_net_revenue 			= 	request.POST.get("join_net_revenue")
			Obj.join_commission 			= 	request.POST.get("join_commission")
			Obj.tip_gross_revenue 			= 	request.POST.get("tip_gross_revenue")
			Obj.tip_net_revenue 			= 	request.POST.get("tip_net_revenue")
			Obj.tip_commission 				= 	request.POST.get("tip_commission")
			Obj.refunds_gross_revenue 			= 	request.POST.get("refunds_gross_revenue")
			Obj.refunds_net_revenue 			= 	request.POST.get("refunds_net_revenue")
			Obj.refunds_commission 				= 	request.POST.get("refunds_commission")
			Obj.save()
			
			messages.success(request,"Payout has been edited successfully.")
			return redirect('/payout/')
			
			
	context		=	{
		"form":form,
		"errors":validationErrors,
		"payoutDetail":payoutDetail
	}
	return render(request,"payout/edit_payout.html",context)
