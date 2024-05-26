from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,TipMe,ModelNotificationSetting
from apps.dropdownmanger.models import DropDownManager 
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from apps.emaillogs.models import EmailLog
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
import hashlib

# Create your views here.

def commonMail(request, action_type,model_id, sub_id,arraydata):
	if action_type == "TIP_RECIVED":
		arraycurrency		=	arraydata['currency']
		arrayamount			=	arraydata['amount']

		modelDetail			=	User.objects.filter(id=model_id).first()
		email				=	modelDetail.email
		model_name			=	modelDetail.model_name

		subscriber_email	=	sub_id

		notification_setting_model = check_notification_enable(request,model_id,action_type)
		if notification_setting_model == True:
			emailaction			=	EmailAction.objects.filter(action="tip_received_notification").first()
			emailTemplates		=	EmailTemplates.objects.filter(action ='tip_received_notification').first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[subscriber_email,model_name,arraycurrency,arrayamount]
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
			htmly     = get_template('common/email.html')
			plaintext = get_template('common/email.txt')
			text_content = plaintext.render(context		=	{
				"body":massage_body
			})
			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,email)

	if action_type == "PLAN_PURCHASE":
		# subscriptionId			=	arraydata['model_subscription_id']
		# planId					=	arraydata['plan_type_id']
		# subscripDetail			=	ModelSubscriptions.objects.filter(id=subscriptionId).first()
		# socialAccount			=	subscripDetail.social_account
		# planDetail				=	ModelSubscriptionPlans.objects.filter(id=planId).first()
		# plan_type				=	planDetail.plan_type
	 
		model_subscription_username	=	arraydata['model_subscription_username']
		subscriber_subscription_username	= arraydata['subscriber_subscription_username']
		
		socialAccount			=	arraydata['socialAccount']
		if(socialAccount == "snapchat"):
			socialAccount	=	"Snapchat"
			model_subscription_url	=	"http://www.snapchat.com/add/"+model_subscription_username
			model_subscription_url_model	=	"http://www.snapchat.com/add/"+subscriber_subscription_username
		elif(socialAccount == "private_feed"):
			socialAccount	=	"Private Feed"
			model_subscription_url	=	"http://thefanhomepage.com/"+model_subscription_username
			model_subscription_url_model	=	"http://thefanhomepage.com/dashboard"
		elif(socialAccount == "whatsapp"):
			socialAccount	=	"Whatsapp"
			model_subscription_url	=	"https://api.whatsapp.com/send?phone="+model_subscription_username
			model_subscription_url_model	=	"https://api.whatsapp.com/send?phone="+subscriber_subscription_username
		elif(socialAccount == "instagram"):
			socialAccount	=	"Instagram"
			model_subscription_url	=	"https://www.instagram.com/"+model_subscription_username
			model_subscription_url_model	=	"https://www.instagram.com/"+subscriber_subscription_username
		elif(socialAccount == "tips"):
			socialAccount	=	"Tip"
		
		currency				=	arraydata['currency']
		price					=	arraydata['price']

		offer_name				=	arraydata['offer_name']

		modelDetail				=	User.objects.filter(id=model_id).first()
		email					=	modelDetail.email
		model_name				=	modelDetail.model_name

		subDetail				=	User.objects.filter(id=sub_id).first()
		sub_name				=	subDetail.username
		sub_email				=	subDetail.email
		
		notification_setting_sub = check_notification_enable(request,sub_id,action_type)
		if notification_setting_sub == True:
			emailaction				=	EmailAction.objects.filter(action="subscriber_subscription_plan_purchase").first()
			emailTemplates			=	EmailTemplates.objects.filter(action="subscriber_subscription_plan_purchase").first()
			
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[subscriber_subscription_username,socialAccount,model_name,currency,price,model_subscription_username,model_subscription_url,offer_name]
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
			htmly     = get_template('common/email.html')
			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,sub_email)
		
		notification_setting_model = check_notification_enable(request,model_id,action_type)
		if notification_setting_model == True:
			emailaction				=	EmailAction.objects.filter(action="model_subscription_plan_purchase").first()
			emailTemplates			=	EmailTemplates.objects.filter(action="model_subscription_plan_purchase").first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[model_name,subscriber_subscription_username,socialAccount,currency,price,subscriber_subscription_username,model_subscription_url_model,offer_name]
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
			htmly     = get_template('common/email.html')
			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,email)

	if action_type == "PLAN_EXPIRE":
		# subscriptionId			=	arraydata['subscription_id']
		# planId					=	arraydata['plan_id']
		# subscripDetail			=	ModelSubscriptions.objects.filter(id=subscriptionId).first()
		# planDetail				=	ModelSubscriptionPlans.objects.filter(id=planId).first()
		socialAccount			=	arraydata['socialAccount']
		if(socialAccount == "snapchat"):
			socialAccount	=	"Snapchat"
		elif(socialAccount == "private_feed"):
			socialAccount	=	"Private Feed"
		elif(socialAccount == "whatsapp"):
			socialAccount	=	"Whatsapp"
		elif(socialAccount == "instagram"):
			socialAccount	=	"Instagram"
		elif(socialAccount == "tips"):
			socialAccount	=	"Tip"
		currency				=	arraydata['currency']
		price					=	str(arraydata['price'])
		
		modelDetail				=	User.objects.filter(id=model_id).first()
		modelemail				=	modelDetail.email
		model_name				=	modelDetail.model_name
		
		subDetail				=	User.objects.filter(id=sub_id).first()
		sub_name				=	arraydata["subscriber_username"]
		sub_email				=	subDetail.email
		
		## for subscriber ##
		notification_setting_sub = check_notification_enable(request,sub_id,action_type)
		if notification_setting_sub == True:
			emailaction				=	EmailAction.objects.filter(action="model_subscription_plan_expires_user").first()
			emailTemplates			=	EmailTemplates.objects.filter(action="model_subscription_plan_expires_user").first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[sub_name,model_name,socialAccount,currency,price]
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
			htmly     = get_template('common/email.html')
			plaintext = get_template('common/email.txt')
			text_content = plaintext.render(context		=	{
				"body":massage_body
			})
			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,sub_email)
		
		
		## For Model ##
		notification_setting_model = check_notification_enable(request,model_id,action_type)
		if notification_setting_model == True:
			emailaction				=	EmailAction.objects.filter(action="model_subscription_plan_expires_model").first()
			emailTemplates			=	EmailTemplates.objects.filter(action="model_subscription_plan_expires_model").first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[sub_name,model_name,socialAccount,currency,price]
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
			htmly     = get_template('common/email.html')
			plaintext = get_template('common/email.txt')
			text_content = plaintext.render(context		=	{
				"body":massage_body
			})
			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,modelemail)

	return True

def check_notification_enable(request,user_id,notification_type):
	user_detail = User.objects.filter(id=user_id).first()
	user_notification_detail = ModelNotificationSetting.objects.filter(user_id=user_id).first()
	
	## for model
	if user_detail.user_role_id == 3:
		if notification_type == "PLAN_EXPIRE":
			if user_notification_detail:
				if user_notification_detail.subscription_expires == 1:
					return True
				else:
					return False
			else:
				return False
		if notification_type == "PLAN_PURCHASE":
			if user_notification_detail:
				if user_notification_detail.new_subscription_purchased == 1:
					return True
				else:
					return False
			else:
				return False	
		if notification_type == "TIP_RECIVED":
			if user_notification_detail:
				if user_notification_detail.received_tip == 1:
					return True
				else:
					return False
			else:
				return False				
	## For Subscriber			
	if user_detail.user_role_id == 2:
		if notification_type == "PLAN_EXPIRE":
			if user_notification_detail:
				if user_notification_detail.subscription_expires == 1:
					return True
				else:
					return False
			else:
				return False
		if notification_type == "PLAN_PURCHASE":
			if user_notification_detail:
				if user_notification_detail.new_subscription_purchased == 1:
					return True
				else:
					return False
			else:
				return False
	return True


def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip


def sendEmail(request,subject,html_content,email):
	email_from	=	settings.DEFAULT_FROM_EMAIL
	emailData = EmailMultiAlternatives(subject,html_content,to=[email])
	emailData.content_subtype = "html"
	res = emailData.send()
	# print(res)

	emailLog			=	EmailLog()
	emailLog.email_to	=	email
	emailLog.email_from	=	email_from
	emailLog.subject	=	subject
	emailLog.message	=	html_content
	emailLog.save()
	return True