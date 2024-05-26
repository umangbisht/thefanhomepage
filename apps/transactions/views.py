from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,Payout,TransactionHistory
from apps.dropdownmanger.models import DropDownManager 
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
from django.template.loader import get_template
import os
import decimal
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
import xlwt
from django.http import HttpResponse
from django.contrib.auth.models import User
import time


# Create your views here.
VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]



@login_required(login_url='/login')
def indexTransaction(request):
	datetimeFormat	=	settings.READINGDATE_TIME_FORMAT
	# userDetail =    User.objects.all().values("id")
	DB = TransactionHistory.objects.filter(model__is_deleted= 0).all()

	if request.GET.get('model_name'):
		model_name= request.GET.get('model_name').strip()
		DB = DB.filter(model__model_name__icontains= model_name)

	if request.GET.get('subscriber_name'):
		subscriber_name= request.GET.get('subscriber_name').strip()
		DB = DB.filter(user__username__icontains= subscriber_name)

	if request.GET.get('started_at'):
		started_at= request.GET.get('started_at').strip()
		DB = DB.filter(created_at__gte= started_at)

	if request.GET.get('ended_at'):
		ended_at= request.GET.get('ended_at').strip()
		DB = DB.filter(created_at__lte= ended_at)
		
	if request.GET.get('transaction_id'):
		transaction_id= request.GET.get('transaction_id').strip()
		DB = DB.filter(transaction_id= transaction_id)

	if request.GET.get('transaction_type'):
		transaction_type= request.GET.get('transaction_type').strip()
		DB = DB.filter(transaction_type__icontains= transaction_type)
		


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
			result.commission	=	round(decimal.Decimal(result.amount)-decimal.Decimal(result.commission),2)
		
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
		'datetimeFormat':datetimeFormat,
		'order_by': order_by,
		'direction': direction,
		'searchingVariables': searchingVariables,
		'querySring': querySring,
		'page_range': page_range,
	}
	return render(request, "transaction/index.html",context)



@login_required(login_url='/login/')
def export_transactions_xls(request):
	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = 'attachment; filename="transactions.xls"'
	wb = xlwt.Workbook(encoding='utf-8')
	ws = wb.add_sheet('Transaction History')
	
	row_num = 0
	
	font_style = xlwt.XFStyle()
	font_style.font.bold = True
	
	columns = ['Model Name', 'Subscriber Email', 'Transaction Date', 'Transaction Type',  'Amount',  'Currency', 'Net Income', 'Status',"Transaction ID","Subscription Name","Type","Time"]
	
	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)
	
	
	order_by	=	request.GET.get('order_by',"created_at")
	direction	=	request.GET.get('direction',"DESC")
	rows = TransactionHistory.objects.filter(user__is_deleted=0).filter(model__is_deleted=0).order_by("-"+order_by).all()
	font_style = xlwt.XFStyle()
	for row in rows:
		model_name			=	row.model.model_name+" "+row.model.email
		subscriber_name		=	row.user.email
		transaction_date	=	row.created_at
		transaction_date    =   datetime.datetime.strftime(transaction_date, "%Y-%m-%d %H:%M:%S")
		transaction_date    =   transaction_date+""
		transaction_type	=	row.transaction_type
		amount				=	str(row.amount)
		currency				=	row.currency
		net_income			=	str(round(decimal.Decimal(row.amount)-decimal.Decimal(row.commission),2))+" "+row.currency
		status				=	row.status
		transaction_id		=	row.transaction_id
		
		if(row.model_subscription and row.model_subscription.social_account == 'private_feed'):
			social_account	=	"Private Feed"
		elif(row.model_subscription):
			social_account	=	row.model_subscription.social_account
		else:
			social_account	=	""
			
		if(row.user_subscription and row.user_subscription.plan_type == 'recurring'):
			plan_type	=	"Recurring"
		else:
			plan_type	=	"One Time"

		if (row.user_subscription and row.user_subscription.plan_type == 'recurring'):
			offer_period_time	=	row.user_subscription.offer_period_time+" "+row.user_subscription.offer_period_type
		else:
			offer_period_time	=	""
			
		row_num += 1
		for col_num in range(len(columns)):
			if int(col_num) == 0:
				ws.write(row_num, col_num, model_name, font_style)
			if int(col_num) == 1:
				ws.write(row_num, col_num, subscriber_name, font_style)
			if int(col_num) == 2:
				ws.write(row_num, col_num, transaction_date, font_style)
			if int(col_num) == 3:
				ws.write(row_num, col_num, transaction_type, font_style)
			if int(col_num) == 4:
				ws.write(row_num, col_num, amount, font_style)
			if int(col_num) == 5:
				ws.write(row_num, col_num, currency, font_style)
			if int(col_num) == 6:
				ws.write(row_num, col_num, net_income, font_style)
			if int(col_num) == 7:
				ws.write(row_num, col_num, status, font_style)
			if int(col_num) == 8:
				ws.write(row_num, col_num, transaction_id, font_style)
			if int(col_num) == 9:
				ws.write(row_num, col_num, social_account, font_style)
			if int(col_num) == 10:
				ws.write(row_num, col_num, plan_type, font_style)
			if int(col_num) == 11:
				ws.write(row_num, col_num, offer_period_time, font_style)
	
	wb.save(response)
	return response
	
	
@login_required(login_url='/login/')
def refundtransaction(request,id):
	transactions = TransactionHistory.objects.filter(id=id).first()
	transactions.status	=	"refunds"
	transactions.payment_type	=	"refunds"
	transactions.save()
	messages.success(request,"Transaction has been mark refunded successfully.")
	return redirect('/transactions/')
	