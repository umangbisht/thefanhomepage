from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,ModelFollower,ModelNotificationSetting,UserSubscriptionPlan,PrivateFeedModel,TransactionHistory,TipMe,ModelViews,LastPayoutDate,Payout,TopFan,AccountDetails,AuthorizeDevices, AdditionalLinks, PaymentGatewayErrors,FinalizedTransaction, Upload
from apps.cmspages.models import CmsPage,CmsPageDescription
from apps.newsletters.models import NewsletterSubscriber
from apps.api.models import ReportReasonModel,currencyRate
from apps.faq.models import Faq,FaqDescription
from apps.slider.models import SliderImage
from apps.supports.models import Support
from apps.blocks.models import Block,BlockDescription
from apps.dropdownmanger.models import DropDownManagerDescription,DropDownManager
from apps.settings.models import Setting
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
import decimal
import os
import requests
from requests.auth import HTTPBasicAuth
import datetime, calendar
from django.core.files.storage import FileSystemStorage
import re
from hashlib import sha1
import hmac
import hashlib
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
from django.db.models import Count,Sum
from django.db.models import F
from decimal import Decimal
from datetime import  date,timedelta
from apps.common.views import commonMail,get_client_ip,sendEmail
from user_agents import parse
import time
from dateutil.relativedelta import relativedelta



# Get the JWT settings
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]

PRIVATE_FEED_VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
    "mp4",
    "webm",
    "avi",
    "mpeg",
    "mov",
    "3gp",
]

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

class LoginView(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	_("The_password_field_is_required")

		if not validationErrors:
			password = request.data.get("password", "")
			username = request.data.get("email", "")
			user = authenticate(request, username=username, password=password)
			if user is not None:
				# login saves the user’s ID in the session,
				# using Django’s session framework.
				login(request, user)
				if request.user.user_role_id == 1:
					content = {
						"success": 3,
						"data":[],
						"msg":_("Invalid_email_or_password")
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_active == 0:
					content = {
						"success": 3,
						"data":[],
						"msg":_("Your_account_has_been_deactivated_Please_contact_to_admin")
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_verified == 0:
					content = {
						"success": 2,
						"data":[],
						"msg":_("Your_account_is_not_verified")
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_approved == 0 and request.user.user_role_id == 3:
					content = {
						"success": 3,
						"data":[],
						"msg":_("Your_profile_is_pending_for_approval")
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				else:
					if request.user.user_role_id == 3:
						if request.user.main_image == None or request.user.main_image == "":
							ModelImage = ModelImages.objects.filter(user_id=request.user.id).all()
							if ModelImage:
								profile_image					=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
							else:
								profile_image					=	""
						else:
							profile_image						=	settings.MODEL_IMAGE_URL+request.user.main_image
					else:
						profile_image							=	""
								
					userDetail	=	{
						"email":request.user.email,"user_role_id":request.user.user_role_id,"first_name":request.user.first_name,"last_name":request.user.last_name,"from_date":request.user.from_date,"address_line_2":request.user.address_line_2,"city":request.user.city,"age":request.user.age,"hair":request.user.hair,"eyes":request.user.eyes,"gender":request.user.gender,"date_of_birth":request.user.date_of_birth,"address_line_1	":request.user.address_line_1,"amazon_wishlist_link":request.user.amazon_wishlist_link,"bio":request.user.bio,"height":request.user.height,"model_name":request.user.model_name,"postal_code":request.user.postal_code,"previous_first_name":request.user.previous_first_name,"previous_last_name":request.user.previous_last_name,"private_snapchat_link":request.user.private_snapchat_link,"public_instagram_link":request.user.public_instagram_link,"public_snapchat_link":request.user.public_snapchat_link,"skype_number":request.user.skype_number,"twitter_link":request.user.twitter_link,"weight":request.user.weight,"youtube_link":request.user.youtube_link,"youtube_video_url":request.user.youtube_video_url,"user_id":request.user.id,"default_currency":request.user.default_currency,"rank":request.user.rank,"rank_status":request.user.rank_status,"profile_image":profile_image,"is_private_feed":request.user.is_private_feed
					}
					user_email				=	request.user.email		
					user_agent				=	request.META['HTTP_USER_AGENT']
					user_agent_calc 		=	parse(user_agent)
					user_browser			=	user_agent_calc.browser.family
					user_browser_version	=	user_agent_calc.browser.version_string
					user_os					=	user_agent_calc.os.family
					browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'

					IPAddr 					= 	get_client_ip(request)
					authorizeDetails		=	AuthorizeDevices.objects.filter(user_id=request.user.id).filter(user_agent=user_agent).filter(browser_device=browser_detail).filter(ip_address=IPAddr).first()
					if authorizeDetails == None or authorizeDetails =="":
						NotiSettingObj	=   ModelNotificationSetting.objects.filter(user_id=request.user.id).first()
						if NotiSettingObj:
							if NotiSettingObj.detects_login_unverified_device	==	1:
								emailaction			=	EmailAction.objects.filter(action="login_on_unverified_device_notification").first()
								emailTemplates		=	EmailTemplates.objects.filter(action ='login_on_unverified_device_notification').first()
								constant = list()
								data = (emailaction.option.split(','))
								for obj in data:
									constant.append("{"+ obj +"}")
								subject=emailTemplates.subject
								massage_body  	= emailTemplates.body
								website_url		=	settings.FRONT_SITE_URL
								site_title		=	settings.SITETITLE
								rep_Array=[user_email,IPAddr,user_browser,user_agent]
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
								sendEmail(request,subject,html_content,user_email)

					content = {
						"success": True,
						"msg":_("You_have_login_successfully"),
						"token":jwt_encode_handler(jwt_payload_handler(user)),
						"profile_image":profile_image,
						"data":userDetail
					}
					return Response(content)
			else:
				if User.objects.filter(email=request.POST.get("email")).exists():
					userDetail		=	User.objects.filter(email=request.POST.get("email")).first()
					if userDetail.is_active == 0:
						content = {
							"success": 3,
							"data":[],
							"msg":_("Your_account_has_been_deactivated_Please_contact_to_admin")
						}
						return Response(content,status=status.HTTP_401_UNAUTHORIZED)
					else:
						userId			=	userDetail.id
						userEmail		=	userDetail.email
						NotiSettingObj	=   ModelNotificationSetting.objects.filter(user_id=userId).first()
						user_agent		=	request.META['HTTP_USER_AGENT']
						IPAddr 			= 	get_client_ip(request)
						if NotiSettingObj:
							if NotiSettingObj.detects_unsuccessful_login	== 1:
								emailaction			=	EmailAction.objects.filter(action="unsuccessful_login_notification").first()
								emailTemplates		=	EmailTemplates.objects.filter(action ='unsuccessful_login_notification').first()
								constant = list()
								data = (emailaction.option.split(','))
								for obj in data:
									constant.append("{"+ obj +"}")
								subject=emailTemplates.subject
								massage_body  = emailTemplates.body
								website_url		=	settings.FRONT_SITE_URL
								site_title		=	settings.SITETITLE
								rep_Array=[userEmail,IPAddr,user_agent]
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
								sendEmail(request,subject,html_content,userEmail)


				content = {
					
					"success": 3,
					"data":[],
					"msg":_("Invalid_email_or_password")
				}
				return Response(content,status=status.HTTP_401_UNAUTHORIZED)
		else:

			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

class ValidateSignupUsers(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")
			else:
				if User.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	_("This_email_is_already_exists")

		if request.POST.get("confirm_email") == "":
			validationErrors["confirm_email"]	=	_("The_confirm_email_field_is_required")
		else:
			if request.POST.get("confirm_email") != request.POST.get("email"):
				validationErrors["confirm_email"]	=	_("The_email_and_confirm_email_field_is_not_equal")

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	_("The_password_field_is_required")

		if request.POST.get("user_role") == None or request.POST.get("user_role") == "":
			validationErrors["user_role"]	=	_("The_user_role_field_is_required")
		else:
			if request.POST.get("user_role") != "model" and request.POST.get("user_role") != "subscriber":
				validationErrors["user_role"]	=	_("The_user_role_value_is_not_valid")
			
		if not validationErrors:
			password = request.data.get("password", "")
			email = request.data.get("email", "")
			user_role = request.data.get("user_role", "")
		
			if user_role == "model":
				user_role_id	=	3
			else:
				user_role_id	=	2
				
			if request.data.get("signup_from") == "" or request.data.get("signup_from") == None or request.data.get("signup_from") == "null":
				signupFromId = None
			else:
				signup_from = request.data.get("signup_from")
				signupFrom	=	User.objects.filter(user_role_id = 3).filter(slug=signup_from).first()
				if signupFrom != None:
					signupFromId = int(signupFrom.id)
				else:
					signupFromId = None
					
			if user_role_id == 2:
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=user_role_id,is_approved=1,is_verified=1,validate_string=validatestring, signup_from_id = signupFromId
				)
			else:
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=user_role_id,is_approved=0,is_verified=1,validate_string=validatestring
				)
			
			lastUserId				=	new_user.id
			
			if user_role_id == 3:
				user = User.objects.filter(id=lastUserId).first()
				d = datetime.date.today()
				next_monday = next_weekday(d, 0)
				
				payObj 					= LastPayoutDate()
				payObj.model_id 		= lastUserId
				payObj.last_payout_date = next_monday+timedelta(days=14)
				payObj.save()
			
			user_agent				=	request.META['HTTP_USER_AGENT']
			user_agent_calc 		=	parse(user_agent)
			user_browser			=	user_agent_calc.browser.family
			user_browser_version	=	user_agent_calc.browser.version_string
			user_os					=	user_agent_calc.os.family
			browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'
			IPAddr 					= 	get_client_ip(request)
			
			AuthorizeDevicesInfo									=	AuthorizeDevices()
			AuthorizeDevicesInfo.user_id 							= 	lastUserId
			AuthorizeDevicesInfo.user_agent							= 	user_agent
			AuthorizeDevicesInfo.browser_device						= 	browser_detail
			AuthorizeDevicesInfo.ip_address 						= 	IPAddr
			AuthorizeDevicesInfo.save()

			ModelNotificationInfo									=	ModelNotificationSetting()
			ModelNotificationInfo.user_id 							= 	lastUserId
			ModelNotificationInfo.new_subscription_purchased 		= 	1
			ModelNotificationInfo.subscription_expires 				= 	1
			ModelNotificationInfo.received_tip 						= 	1
			ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
			ModelNotificationInfo.detects_login_unverified_device 	= 	1
			ModelNotificationInfo.detects_unsuccessful_login 		= 	1
			ModelNotificationInfo.save()
			
			if signupFromId != None:
				total_subscriber_signup		=	User.objects.filter(signup_from_id=signupFromId).filter(is_deleted=0).count()
				User.objects.filter(id=signupFromId).update(total_subscriber_signup=total_subscriber_signup)

			newsletter_subscription		=	request.POST.get('newsletter_subscription',"")
			if newsletter_subscription:
				if newsletter_subscription == "true":
					newsletterObj			=	NewsletterSubscriber()
					newsletterObj.user_id	=	lastUserId
					newsletterObj.email		=	email
					newsletterObj.save()

					email 			=	email
					website_url		=	settings.FRONT_SITE_URL
					unsubscribelink			=  	settings.FRONT_SITE_URL+'user/unsubscribe-newletter?subscriber_email='+email
					emailaction				=	EmailAction.objects.filter(action="send_newsletter").first()
					emailTemplates			=	EmailTemplates.objects.filter(action = 'send_newsletter').first()
					constant = list()
					data = (emailaction.option.split(','))
					for obj in data:
						constant.append("{"+ obj +"}")
					subject=emailTemplates.subject
					rep_Array=[email,website_url,unsubscribelink]
					massage_body  = emailTemplates.body
					# website_url		=	settings.FRONT_SITE_URL
					site_title		=	settings.SITETITLE
					x = range(len(constant))
					for i in x:
						massage_body=re.sub(constant[i], rep_Array[i], massage_body)
					massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)

					htmly     = get_template('common/email.html')
					plaintext = get_template('common/email.txt')

					html_content = htmly.render(context		=	{
						"body":massage_body,
						"website_url":website_url,
						"site_title":site_title
					})
					sendEmail(request,subject,html_content,email)
					
			##Well come email
			username 		= 	email
			email 			=	email
			emailaction		=EmailAction.objects.filter(action="user_registration").first()
			emailTemplates	=EmailTemplates.objects.filter(action = 'user_registration').first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			website_url		=	settings.FRONT_SITE_URL
			rep_Array=[email,password,website_url]
			massage_body  = emailTemplates.body
			site_title		=	settings.SITETITLE
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
			
			if user_role_id == 3:
				emailaction		=EmailAction.objects.filter(action="model_signup_information_to_admin").first()
				emailTemplates	=EmailTemplates.objects.filter(action = 'model_signup_information_to_admin').first()
				constant = list()
				data = (emailaction.option.split(','))
				for obj in data:
					constant.append("{"+ obj +"}")
				subject=emailTemplates.subject
				website_url		=	settings.FRONT_SITE_URL
				rep_Array=[email]
				massage_body  = emailTemplates.body
				site_title		=	settings.SITETITLE
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
				admin_email			=	""
				SettingDetails = Setting.objects.filter(key="Site.model_signup_email_to_admin").first()
				if SettingDetails:
					admin_email	=	SettingDetails.value
					
				sendEmail(request,subject,html_content,admin_email)
			
			

			user = User.objects.filter(id=lastUserId).first()
			userDetail	=	{
						"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status,"is_private_feed":user.is_private_feed
					}
					
			content = {
				"success": True,
				"token":jwt_encode_handler(jwt_payload_handler(user)),
				"data":userDetail,
				"msg":_("Your_account_has_been_registered_successfully")
			}
			return Response(content)
			
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
			
class createSubscriber(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")

		if not validationErrors:
			email= request.POST.get("email",'')
			userDetails		=   User.objects.filter(email=email).filter(is_deleted=0).first()
			if userDetails:
				lastUserId	=	userDetails.id
			else:
				if request.data.get("signup_from") == "" or request.data.get("signup_from") == None or request.data.get("signup_from") == "null":
					signupFromId = None
				else:
					signup_from = request.data.get("signup_from")
					signupFrom	=	User.objects.filter(user_role_id = 3).filter(slug=signup_from).first()
					if signupFrom != None:
						signupFromId = int(signupFrom.id)
					else:
						signupFromId = None
			
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				password = User.objects.make_random_password()
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=2,is_approved=1,is_verified=1,validate_string=validatestring, signup_from_id = signupFromId
				)
				lastUserId				=	new_user.id
				user_agent				=	request.META['HTTP_USER_AGENT']
				user_agent_calc 		=	parse(user_agent)
				user_browser			=	user_agent_calc.browser.family
				user_browser_version	=	user_agent_calc.browser.version_string
				user_os					=	user_agent_calc.os.family
				browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'
				IPAddr 					= 	get_client_ip(request)

				if lastUserId :
					AuthorizeDevicesInfo									=	AuthorizeDevices()
					AuthorizeDevicesInfo.user_id 							= 	lastUserId
					AuthorizeDevicesInfo.user_agent							= 	user_agent
					AuthorizeDevicesInfo.browser_device						= 	browser_detail
					AuthorizeDevicesInfo.ip_address 						= 	IPAddr
					AuthorizeDevicesInfo.save()

					ModelNotificationInfo									=	ModelNotificationSetting()
					ModelNotificationInfo.user_id 							= 	lastUserId
					ModelNotificationInfo.new_subscription_purchased 		= 	1
					ModelNotificationInfo.subscription_expires 				= 	1
					ModelNotificationInfo.received_tip 						= 	1
					ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
					ModelNotificationInfo.detects_login_unverified_device 	= 	1
					ModelNotificationInfo.detects_unsuccessful_login 		= 	1
					ModelNotificationInfo.save()

					user_details 	= 	User.objects.filter(id=lastUserId).first()
					##verification email
					username 		= 	email
					email 			=	email
					link			=  	settings.FRONT_SITE_URL+'verify-account?validate_string='+validatestring
					emailaction				=EmailAction.objects.filter(action="user_registration").first()
					emailTemplates			=EmailTemplates.objects.filter(action = 'user_registration').first()
					constant = list()
					data = (emailaction.option.split(','))
					for obj in data:
						constant.append("{"+ obj +"}")
					subject=emailTemplates.subject
					website_url		=	settings.FRONT_SITE_URL
					rep_Array=[email,password,website_url]
					massage_body  = emailTemplates.body
					site_title		=	settings.SITETITLE
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
					
					
			content = {
				"success": True,
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

class RegisterUsers(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")
			else:
				if User.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	_("This_email_is_already_exists")

		if request.POST.get("confirm_email") == "":
			validationErrors["confirm_email"]	=	_("The_confirm_email_field_is_required")
		else:
			if request.POST.get("confirm_email") != request.POST.get("email"):
				validationErrors["confirm_email"]	=	_("The_email_and_confirm_email_field_is_not_equal")

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	_("The_password_field_is_required")

		if request.POST.get("user_role") == None or request.POST.get("user_role") == "":
			validationErrors["user_role"]	=	_("The_user_role_field_is_required")
		else:
			if request.POST.get("user_role") != "model" and request.POST.get("user_role") != "subscriber":
				validationErrors["user_role"]	=	_("The_user_role_value_is_not_valid")
			
		if not validationErrors:
			password = request.data.get("password", "")
			email = request.data.get("email", "")
			user_role = request.data.get("user_role", "")
			if user_role == "model":
				user_role_id	=	3
			else:
				user_role_id	=	2

			if user_role_id == 3:
				validatestring = ''
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=user_role_id,is_approved=0,is_verified=1,validate_string=validatestring
				)
				currentMonth = datetime.datetime.now().month
				currentYear = datetime.datetime.now().year
				
				
				# gifi_image  = ''
				# gibi_image  = ''
				# pnti_image	= ''
				# pntiwdp_image = ''

				user_agent				=	request.META['HTTP_USER_AGENT']
				user_agent_calc 		=	parse(user_agent)
				user_browser			=	user_agent_calc.browser.family
				user_browser_version	=	user_agent_calc.browser.version_string
				user_os					=	user_agent_calc.os.family
				browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'
				IPAddr 					= 	get_client_ip(request)	
				
				# if request.FILES.get("government_id_front_image"):
				# 	gifiFile = request.FILES.get("government_id_front_image")
				# 	fs = FileSystemStorage()
				# 	filename = gifiFile.name.split(".")[0].lower()
				# 	extension = gifiFile.name.split(".")[-1].lower()
				# 	newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				# 	fs.save(folder_directory+newfilename, gifiFile)	
				# 	gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				# if request.FILES.get("government_id_back_image"):
				# 	gibiFile = request.FILES.get("government_id_back_image")
				# 	fs = FileSystemStorage()
				# 	filename = gibiFile.name.split(".")[0].lower()
				# 	extension = gibiFile.name.split(".")[-1].lower()
				# 	newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				# 	fs.save(folder_directory+newfilename, gibiFile)	
				# 	gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				# if request.FILES.get("photo_next_to_id"):
				# 	pntiFile = request.FILES.get("photo_next_to_id")
				# 	fs = FileSystemStorage()
				# 	filename = pntiFile.name.split(".")[0].lower()
				# 	extension = pntiFile.name.split(".")[-1].lower()
				# 	newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				# 	fs.save(folder_directory+newfilename, pntiFile)	
				# 	pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				# if request.FILES.get("photo_next_to_id_with_dated_paper"):
				# 	pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
				# 	fs = FileSystemStorage()
				# 	filename = pntiwdpFile.name.split(".")[0].lower()
				# 	extension = pntiwdpFile.name.split(".")[-1].lower()
				# 	newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				# 	fs.save(folder_directory+newfilename, pntiwdpFile)	
				# 	pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				totelModels = User.objects.filter(is_verified=1).count()
				
				slug = (request.POST.get("last_name","")+'-'+request.POST.get("last_name","")).lower()
				if User.objects.filter(slug=slug).exists():
					slug = (request.POST.get("last_name","")+'-'+request.POST.get("last_name","")+'-'+str(new_user.id)).lower()
				lastUserId										=	new_user.id
				NewUserObj 										= 	new_user
				NewUserObj.model_name							=	request.POST.get("model_name","")
				NewUserObj.best_known_for						=	request.POST.get("best_known_for","")
				NewUserObj.bio									=	request.POST.get("bio","")
				NewUserObj.private_snapchat_link				=	request.POST.get("private_snapchat_link","")
				NewUserObj.public_snapchat_link					=	request.POST.get("public_snapchat_link","")
				NewUserObj.public_instagram_link				=	request.POST.get("public_instagram_link","")
				NewUserObj.twitter_link							=	request.POST.get("twitter_link","")
				NewUserObj.youtube_link							=	request.POST.get("youtube_link","")
				NewUserObj.amazon_wishlist_link					=	request.POST.get("amazon_wishlist_link","")
				NewUserObj.age									=	request.POST.get("age","")
				NewUserObj.from_date							=	request.POST.get("from_date","")
				NewUserObj.height								=	request.POST.get("height","")
				NewUserObj.weight								=	request.POST.get("weight","")
				NewUserObj.hair									=	request.POST.get("hair","")
				NewUserObj.eyes									=	request.POST.get("eyes","")
				NewUserObj.youtube_video_url					=	request.POST.get("youtube_video_url","")
				NewUserObj.default_currency						=	request.POST.get("default_currency","")
				NewUserObj.government_id_front_image			=	request.POST.get("government_id_front_image","")
				NewUserObj.government_id_back_image				=	request.POST.get("government_id_back_image","")
				NewUserObj.photo_next_to_id						=	request.POST.get("photo_next_to_id","")
				NewUserObj.photo_next_to_id_with_dated_paper	=	request.POST.get("photo_next_to_id_with_dated_paper","")
				NewUserObj.rank									=	totelModels
				NewUserObj.rank_status							=	'stable'
				NewUserObj.save()





				AuthorizeDevicesInfo									=	AuthorizeDevices()
				AuthorizeDevicesInfo.user_id 							= 	lastUserId
				AuthorizeDevicesInfo.user_agent							= 	user_agent
				AuthorizeDevicesInfo.browser_device						= 	browser_detail
				AuthorizeDevicesInfo.ip_address 						= 	IPAddr
				AuthorizeDevicesInfo.save()
				
				
				ModelNotificationInfo									=	ModelNotificationSetting()
				ModelNotificationInfo.user_id 							= 	lastUserId
				ModelNotificationInfo.new_subscription_purchased 		= 	1
				ModelNotificationInfo.subscription_expires 				= 	1
				ModelNotificationInfo.received_tip 						= 	1
				ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
				ModelNotificationInfo.detects_login_unverified_device 	= 	1
				ModelNotificationInfo.detects_unsuccessful_login 		= 	1
				ModelNotificationInfo.save()


				newsletter_subscription		=	request.POST.get('newsletter_subscription')
				if newsletter_subscription:
					if newsletter_subscription == "true":
						newsletterObj			=	NewsletterSubscriber()
						newsletterObj.user_id	=	lastUserId
						newsletterObj.email		=	email
						newsletterObj.save()

						email 			=	email
						website_url		=	settings.FRONT_SITE_URL
						unsubscribelink			=  	settings.FRONT_SITE_URL+'user/unsubscribe-newletter?subscriber_email='+email
						emailaction				=	EmailAction.objects.filter(action="send_newsletter").first()
						emailTemplates			=	EmailTemplates.objects.filter(action = 'send_newsletter').first()
						constant = list()
						data = (emailaction.option.split(','))
						for obj in data:
							constant.append("{"+ obj +"}")
						subject=emailTemplates.subject
						rep_Array=[email,website_url,unsubscribelink]
						massage_body  = emailTemplates.body
						# website_url		=	settings.FRONT_SITE_URL
						site_title		=	settings.SITETITLE
						x = range(len(constant))
						for i in x:
							massage_body=re.sub(constant[i], rep_Array[i], massage_body)
						massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)

						htmly     = get_template('common/email.html')
						plaintext = get_template('common/email.txt')

						html_content = htmly.render(context		=	{
							"body":massage_body,
							"website_url":website_url,
							"site_title":site_title
						})
						sendEmail(request,subject,html_content,email)
						
				##Well come email
				username 		= 	email
				email 			=	email
				emailaction		=EmailAction.objects.filter(action="user_registration").first()
				emailTemplates	=EmailTemplates.objects.filter(action = 'user_registration').first()
				constant = list()
				data = (emailaction.option.split(','))
				for obj in data:
					constant.append("{"+ obj +"}")
				subject=emailTemplates.subject
				website_url		=	settings.FRONT_SITE_URL
				rep_Array=[email,password,website_url]
				massage_body  = emailTemplates.body
				site_title		=	settings.SITETITLE
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

				categories 					=   request.POST.get('categories')
				if categories != None and categories != "":
					categories = categories.split(',')
					for category in categories:
						ModelCategoriesInfo							=	ModelCategories()
						ModelCategoriesInfo.dropdown_manager_id 	= 	category
						ModelCategoriesInfo.user_id 				= 	lastUserId
						ModelCategoriesInfo.save()

				images 							= request.POST.getlist("images")
				if images:
					for imge in images:
						myfile = imge
						filename = myfile.split(".")[0].lower()
						extension = myfile.split(".")[-1].lower()
						newfilename = filename+"."+extension
						
						model_image	=	newfilename
						Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
						
						ModelImagesInfo							=	ModelImages()
						ModelImagesInfo.image_url 				= 	model_image
						ModelImagesInfo.user_id 				= 	lastUserId
						ModelImagesInfo.save()

				ModelImage = ModelImages.objects.filter(user_id=lastUserId).all()
				if ModelImage:
					profile_image					=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
				else:
					profile_image					=	""
						
				subscription_dict = request.POST.get("subscription")
				discount_arr = []
				today_date = str(datetime.datetime.today().date())+" 00:00:00"
				if subscription_dict:
					subscription_dict = json.loads(subscription_dict)
					for subdata in subscription_dict:
						if subdata:
							if subscription_dict[subdata]['is_enabled'] == True:
								is_enabled = 1
							else:
								is_enabled = 0
								
							if subscription_dict[subdata]['username']:
								userName = subscription_dict[subdata]['username']
							else:
								userName = ''
								
							subObj 					= ModelSubscriptions()
							subObj.user_id 			= lastUserId
							subObj.social_account 	= subdata
							subObj.username 		= userName
							subObj.is_enabled 		= is_enabled
							subObj.save()
							subId = subObj.id
							if subdata != 'tips':
								if is_enabled == 1 and len(subscription_dict[subdata]['plans']) > 0:
								
									for planData in subscription_dict[subdata]['plans']:
										if planData:
											if planData['is_discount_enabled']:
												is_discount_enabled = 1
												discount_arr.append(planData['discount'])
												discount_arr = [Decimal(x) for x in discount_arr]
											else:
												is_discount_enabled = 0
												
											if "is_permanent_discount" in planData and planData['is_permanent_discount']:
												is_permanent_discount = 1
											else:
												is_permanent_discount = 0
											
											plansObj 									= ModelSubscriptionPlans()	
											if 'is_apply_to_rebills' in planData and planData['is_apply_to_rebills']:
												is_apply_to_rebills = 1
											else:
												is_apply_to_rebills = 0
											if 'from_discount_date' in planData and planData['from_discount_date']:
												plansObj.from_discount_date = planData['from_discount_date']
											else:
												plansObj.from_discount_date = ""
											if('offer_name' in planData and planData['offer_name'] != ""):
												plansObj.offer_name 					= planData['offer_name']
											else:
												plansObj.offer_name = ""
											if 'to_discount_date' in planData and planData['to_discount_date']:
												plansObj.to_discount_date 					= planData['to_discount_date']
											else:
												plansObj.to_discount_date = ""		
												
											if planData['plan_type'] == "recurring":
												if plansObj.from_discount_date:
													if plansObj.from_discount_date > today_date:
														is_discount_enabled = 0
											
											
											plansObj.user_id 							= lastUserId
											plansObj.model_subscription_id 				= subId
											plansObj.plan_type 							= planData['plan_type']
											plansObj.offer_period_time 					= planData['offer_period_time']
											plansObj.offer_period_type 					= planData['offer_period_type']
											plansObj.price 								= planData['price']
											plansObj.discounted_price 					= round(float(planData['discounted_price']),2)
											plansObj.currency 							= planData['currency']
											plansObj.description 						= planData['description']
											plansObj.is_discount_enabled 				= is_discount_enabled
											plansObj.discount 							= planData['discount']
											
											
																				
											plansObj.is_permanent_discount 				= is_permanent_discount
											plansObj.is_apply_to_rebills 				= is_apply_to_rebills
											plansObj.save()
										
					if len(discount_arr)!=0:
						high_discount	=	max(discount_arr)
						User.objects.filter(id=lastUserId).update(highest_discount=high_discount)
					else:
						discount_arr = []
						
				
						
			user = User.objects.filter(id=lastUserId).first()
			
			#Save Next Payout Date		
			d = datetime.date.today()
			next_monday = next_weekday(d, 0)
			
			payObj 					= LastPayoutDate()
			payObj.model_id 		= lastUserId
			payObj.last_payout_date = next_monday+timedelta(days=14)
			payObj.save()
			
			userDetail	=	{
						"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status
					}		

			
			content = {
				"success": True,
				"token":jwt_encode_handler(jwt_payload_handler(user)),
				"data":userDetail,
				"profile_image":profile_image,
				"msg":_("Your_account_has_been_registered_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
class ListModelCategory(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		activeCategory = DropDownManager.objects.filter(dropdown_type="category").filter(is_active=1).values("id")
		category = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=activeCategory).filter(language_code=user_language).all().values('name',"dropdown_manger_id")  # or simply .values() to get all fields
		category = list(category)  # important: convert the QuerySet to a list object
		content = {
			"success": True,
			"data":category,
			"msg":""
		}
		return Response(content)

class ListCountry(generics.ListAPIView):
	#permission_classes = (permissions.IsAuthenticated,)
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		activeCountry = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).exclude(name="United Kingdom").exclude(name="United States of America").exclude(name="Australia").values("id")

		country = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=activeCountry).filter(language_code=user_language).all().values('name',"dropdown_manger_id").order_by('name')  # or simply .values() to get all fields
		country = list(country)  # important: convert the QuerySet to a list object, United Kingdom,United States of America,Australia

		topRatedCountries1 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United Kingdom").values("id")
		topThreeCountry1 = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=topRatedCountries1).filter(language_code=user_language).all().values('name',"dropdown_manger_id").order_by('name')  # or simply .values() to get all fields
		topThreeCountry1 = list(topThreeCountry1)

		
		topRatedCountries2 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="United States of America").values("id")
		topThreeCountry2 = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=topRatedCountries2).filter(language_code=user_language).all().values('name',"dropdown_manger_id").order_by('name')  # or simply .values() to get all fields
		topThreeCountry2 = list(topThreeCountry2)
		
		
		topRatedCountries3 = DropDownManager.objects.filter(dropdown_type="country").filter(is_active=1).filter(name="Australia").values("id")
		topThreeCountry3 = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=topRatedCountries3).filter(language_code=user_language).all().values('name',"dropdown_manger_id").order_by('name')  # or simply .values() to get all fields
		topThreeCountry3 = list(topThreeCountry3)
		
		
		 
		
		content = {
			"success": True,
			"data":topThreeCountry1+topThreeCountry2+topThreeCountry3 + country,
			"msg":""
		}
		return Response(content)

class FeaturedProfile(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		FeaturedProfiles = User.objects.filter(is_approved=1).filter(is_active=1).filter(is_featured=1).filter(user_role_id=3).filter(is_deleted=0).all()[:10]
		FeaturedProfiles = list(FeaturedProfiles)  # important: convert the QuerySet to a list object
		
		profiles	=	[]
		if FeaturedProfiles:
			for Profile in FeaturedProfiles:
				profile					=	{}
				profile["model_name"]	=	Profile.model_name
				profile["is_subscription_enabled"]	=	Profile.is_subscription_enabled
				profile["slug"]			=	Profile.slug
				profile["bio"]			=	Profile.bio
				profile["first_name"]					=	Profile.first_name
				profile["last_name"]					=	Profile.last_name
				profile["discount_percentage"]			=	Profile.highest_discount
				if Profile.highest_discount > 0:
					profile["is_discount_enabled"]		=	1
				else:
					profile["is_discount_enabled"]		=	0
				profile["amazon_wishlist_link"]			=	Profile.amazon_wishlist_link
				profile["private_snapchat_link"]			=	Profile.private_snapchat_link
				profile["public_instagram_link"]			=	Profile.public_instagram_link
				profile["public_snapchat_link"]			=	Profile.public_snapchat_link
				profile["twitter_link"]					=	Profile.twitter_link
				profile["youtube_link"]					=	Profile.youtube_link
				profile["user_id"]							=	Profile.id
				if Profile.featured_image != "" and Profile.featured_image != "null" and Profile.featured_image != None: 
					profile["profile_image"]					=	settings.MODEL_IMAGE_URL+Profile.featured_image
				else :
					profile["profile_image"]					=	""
					
				# ModelImage = ModelImages.objects.filter(user_id=Profile.id).first()
				# if ModelImage:
				# 	profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage.image_url
				# else:
				# 	profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/dummy.jpg"
					
					
				subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).filter(is_enabled=1).filter(is_deleted=0).exclude(social_account='tips').all().values('social_account',"username","is_enabled","id")
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).filter(is_deleted=0).all().values('plan_type',"offer_period_time","offer_period_type","price","discounted_price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","offer_name")
						for planData_detail in planData:
							planData_detail["social_account"] =	subcription["social_account"]
							if(planData_detail["plan_type"] == "one_time"):
								if(int(planData_detail["is_discount_enabled"]) == int(1)):
									planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["discounted_price"]))
								else:
									planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["price"]))
							else:
								if(planData_detail["offer_period_time"] == "" or int(planData_detail["offer_period_time"]) <= int(0)):
									offer_period_time	=	1
								else:
									offer_period_time	=	int(planData_detail["offer_period_time"])
								
								
								if(planData_detail["offer_period_type"] == "week"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
										
								elif(planData_detail["offer_period_type"] == "month"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
										
								elif(planData_detail["offer_period_type"] == "year"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
						
						planData = sorted(planData, key=lambda x:x['plan_price_per_year'])
						planData = list(planData)
						if planData:
							subcription['plans'] = planData	
							
							
				subcriptions_single	=	[]
				if subcriptionData:
					for subcription in subcriptionData:
						counter	=	0
						for planData_detail in subcription["plans"]:
							if(counter == 0):
								subcriptions_single.append(planData_detail)
								
							counter	=	int(counter)+1
				
				profile['subcriptions'] = subcriptionData
				subcriptions_single = sorted(subcriptions_single, key=lambda x:x['plan_price_per_year'])
				profile['subcriptions_single'] = subcriptions_single

				profiles.append(profile)
				
				

		content = {
			"success": True,
			"data":profiles,
			"msg":""
		}
		return Response(content)

class allModels(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if(int(settings.SITESHOW_MODEL_LISTING_ON_HOMEPAGE) == 1):
			TotalModels = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(is_homepage_profile=1)
			DB = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(is_homepage_profile=1)

			if request.GET.get('name'):
				name = request.GET.get('name').strip()
				DB = DB.filter(Q(model_name__icontains=name) | Q(first_name__icontains=name) | Q(last_name__icontains=name) | Q(previous_last_name__icontains=name)| Q(previous_first_name__icontains=name))
				TotalModels = TotalModels.filter(Q(model_name__icontains=name) | Q(first_name__icontains=name) | Q(last_name__icontains=name) | Q(previous_last_name__icontains=name)| Q(previous_first_name__icontains=name))

			if request.GET.get('category'):
				category = request.GET.getlist('category')
				categoryUsers = ModelCategories.objects.filter(dropdown_manager_id__in=category).values("user_id")
				DB = DB.filter(Q(id__in=categoryUsers))
				TotalModels = TotalModels.filter(Q(id__in=categoryUsers))
				
			if request.GET.get('social_account'):
				social_account = request.GET.get('social_account').strip()
				if social_account == 'instagram':
					instaUsers = ModelSubscriptions.objects.filter(social_account='instagram').filter(is_deleted=0).filter(is_enabled=1).values("user_id")
					DB = DB.filter(Q(id__in=instaUsers))
					TotalModels = TotalModels.filter(Q(id__in=instaUsers))
				if social_account == 'snapchat':
					snapUsers = ModelSubscriptions.objects.filter(social_account='snapchat').filter(is_deleted=0).filter(is_enabled=1).values("user_id")		
					DB = DB.filter(Q(id__in=snapUsers))
					TotalModels = TotalModels.filter(Q(id__in=snapUsers))
				if social_account == 'whatsapp':
					whatsappUsers = ModelSubscriptions.objects.filter(social_account='whatsapp').filter(is_deleted=0).filter(is_enabled=1).values("user_id")
					DB = DB.filter(Q(id__in=whatsappUsers))
					TotalModels = TotalModels.filter(Q(id__in=whatsappUsers))
				if social_account == 'private_feed':
					privateFeedUsers = ModelSubscriptions.objects.filter(social_account='private_feed').filter(is_deleted=0).filter(is_enabled=1).values("user_id")
					DB = DB.filter(Q(id__in=privateFeedUsers))
					TotalModels = TotalModels.filter(Q(id__in=privateFeedUsers))
				if social_account == 'tips':
					tipsUsers = ModelSubscriptions.objects.filter(social_account='tips').filter(is_deleted=0).filter(is_enabled=1).values("user_id")
					DB = DB.filter(Q(id__in=tipsUsers))
					TotalModels = TotalModels.filter(Q(id__in=tipsUsers))

			if request.GET.get('sort_by'):
				sort_by = request.GET.get('sort_by')
				if sort_by =='newest':
					DB = DB.order_by('-created_at')

				elif sort_by =='a_z':
					DB = DB.order_by('model_name')

				elif sort_by =='z_a':
					DB = DB.order_by('-model_name')

				elif sort_by == 'most_views':
					DB = DB.order_by('-total_views')

				elif sort_by == 'most_subscribers':
					DB = DB.annotate(c_count=Count('userparent'))
					DB = DB.order_by('-c_count')
			if request.GET.get('filter_by'):
				list_arr = []
				filter_by = request.GET.get('filter_by')
				if filter_by== 'highest_discount':
					DB = DB.filter(highest_discount__gte = 1).filter(highest_discount__lte = 100).order_by("-highest_discount")
					TotalModels = TotalModels.filter(highest_discount__gte = 1).filter(highest_discount__lte = 100).order_by("-highest_discount")
			
			recordPerPge	=	6
			TotalModels	=	TotalModels.count()
			
			page = request.GET.get('page', 1)
			paginator = Paginator(DB, recordPerPge)
			try:
				results = paginator.page(page)
			except PageNotAnInteger:
				results = paginator.page(1)
			except EmptyPage:
				results = paginator.page(paginator.num_pages)
				
			profiles	=	[]
			if results:
				for Profile in results:
					profile					=	{}
					profile["model_name"]	=	Profile.model_name
					profile["slug"]	=	Profile.slug
					profile["bio"]			=	Profile.bio
					profile["amazon_wishlist_link"]			=	Profile.amazon_wishlist_link
					profile["private_snapchat_link"]		=	Profile.private_snapchat_link
					profile["public_instagram_link"]		=	Profile.public_instagram_link
					profile["public_snapchat_link"]			=	Profile.public_snapchat_link
					profile["twitter_link"]					=	Profile.twitter_link
					profile["youtube_link"]					=	Profile.youtube_link
					profile["user_id"]						=	Profile.id
					profile["discount"]						=	Profile.highest_discount

					ModelImage = ModelImages.objects.filter(user_id=Profile.id).all()
					if ModelImage:
						images	=	[]
						for ProfileImage in ModelImage:
							images.append(settings.MODEL_IMAGE_URL+ProfileImage.image_url)

						profile["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
						profile["images"]			=	images
					else:
						profile["profile_image"]	=	settings.MEDIA_URL+"dummy.jpeg"
						profile["images"]			=	""
						
					subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).filter(is_enabled=1).filter(is_deleted=0).exclude(social_account='tips').all().values('social_account',"username","is_enabled","id")
					subcriptionData = list(subcriptionData)
					if subcriptionData:
						for subcription in subcriptionData:
							planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).filter(is_deleted=0).all().values('plan_type',"offer_period_time","offer_period_type","price","discounted_price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","offer_name")
							for planData_detail in planData:
								planData_detail["social_account"] =	subcription["social_account"]
								if(planData_detail["plan_type"] == "one_time"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["discounted_price"]))
									else:
										planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["price"]))
								else:
									if(planData_detail["offer_period_time"] == "" or int(planData_detail["offer_period_time"]) <= int(0)):
										offer_period_time	=	1
									else:
										offer_period_time	=	int(planData_detail["offer_period_time"])
									
									
									if(planData_detail["offer_period_type"] == "week"):
										if(int(planData_detail["is_discount_enabled"]) == int(1)):
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
										else:
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
											
									elif(planData_detail["offer_period_type"] == "month"):
										if(int(planData_detail["is_discount_enabled"]) == int(1)):
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
										else:
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
											
									elif(planData_detail["offer_period_type"] == "year"):
										if(int(planData_detail["is_discount_enabled"]) == int(1)):
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
										else:
											planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
							
							planData = sorted(planData, key=lambda x:x['plan_price_per_year'])
							planData = list(planData)
							if planData:
								subcription['plans'] = planData	
								
								
					subcriptions_single	=	[]
					if subcriptionData:
						for subcription in subcriptionData:
							counter	=	0
							for planData_detail in subcription["plans"]:
								if(counter == 0):
									subcriptions_single.append(planData_detail)
									
								counter	=	int(counter)+1
					
					profile['subcriptions'] = subcriptionData
					subcriptions_single = sorted(subcriptions_single, key=lambda x:x['plan_price_per_year'])
					profile['subcriptions_single'] = subcriptions_single

					profiles.append(profile)
		else:
			profiles	=	[]
			TotalModels	=	0
			recordPerPge	=	0

		is_show_models	=	0
		SettingDetails = Setting.objects.filter(key="Site.show_model_listing_on_homepage").first()
		if SettingDetails:
			is_show_models	=	SettingDetails.value
			
		content = {
			"success": True,
			"data":profiles,
			"msg":"",
			"TotalModels":TotalModels,
			"recordPerPge":recordPerPge,
			"is_show_models":is_show_models,
			"image_path_1":settings.MODEL_IMAGE_URL + "lunching_soon.png",
			"image_path_2":settings.MODEL_IMAGE_URL + "lunching_soon_1.png",
		}
		return Response(content)

class subscriberModelForYou(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		modelsSubscriptionActive	=	UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(plan_status='active').values("model_user_id")
		
		DB = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).exclude(id__in=modelsSubscriptionActive)
		
		# category = request.GET.getlist('category')
		# categoryUsers = ModelCategories.objects.filter(dropdown_manager_id__in=category).values("user_id")
		# DB = DB.filter(Q(id__in=categoryUsers))
			
		DB = DB.order_by("-highest_discount")
		
		recordPerPge	=	20
		
		page = request.GET.get('page', 1)
		paginator = Paginator(DB, recordPerPge)
		try:
			results = paginator.page(page)
		except PageNotAnInteger:
			results = paginator.page(1)
		except EmptyPage:
			results = paginator.page(paginator.num_pages)
			
		profiles	=	[]
		if results:
			for Profile in results:
				profile					=	{}
				profile["model_name"]	=	Profile.model_name
				profile["slug"]	=	Profile.slug
				profile["bio"]			=	Profile.bio
				profile["amazon_wishlist_link"]			=	Profile.amazon_wishlist_link
				profile["private_snapchat_link"]		=	Profile.private_snapchat_link
				profile["public_instagram_link"]		=	Profile.public_instagram_link
				profile["public_snapchat_link"]			=	Profile.public_snapchat_link
				profile["twitter_link"]					=	Profile.twitter_link
				profile["youtube_link"]					=	Profile.youtube_link
				profile["user_id"]						=	Profile.id
				profile["discount"]						=	Profile.highest_discount

				ModelImage = ModelImages.objects.filter(user_id=Profile.id).all()
				if ModelImage:
					images	=	[]
					for ProfileImage in ModelImage:
						images.append(settings.MODEL_IMAGE_URL+ProfileImage.image_url)

					profile["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
					profile["images"]			=	images
				else:
					profile["profile_image"]	=	settings.MEDIA_URL+"dummy.jpeg"
					profile["images"]			=	""
				
				profiles.append(profile)

		content = {
			"success": True,
			"data":profiles,
			"msg":"",
		}
		return Response(content)
		
class modelProfile(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET.get("slug") != None and request.GET.get("slug") != "":
			slug	=	request.GET.get("slug")
			ModelDetail = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(slug=slug).first()

			if ModelDetail:
				hostname = socket.gethostname()    
				IPAddr = get_client_ip(request)
				Obj					=		ModelViews()
				Obj.model_id		=		ModelDetail.id
				Obj.ip_address		=		IPAddr
				Obj.save()
				
				User.objects.filter(id=ModelDetail.id).update(total_views=F('total_views')+1)
				ModelDetailBio	=	ModelDetail.bio
				ModelDetailSubscription = ModelDetail.is_subscription_enabled
				ModelDetail = model_to_dict(ModelDetail)
				ModelDetail["bio"]	=	ModelDetailBio
				ModelDetail["is_subscription_enabled"] = ModelDetailSubscription
				totalFollowers = ModelFollower.objects.filter(model_id=ModelDetail["id"]).all().count()
				ModelDetail["total_followers"] = totalFollowers
				if request.user.is_authenticated:
					user_id = request.user.id
					followDetails	=   ModelFollower.objects.filter(subscriber_id=user_id).filter(model_id=ModelDetail["id"]).first()
					subscripDetail	=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_user_id=ModelDetail["id"]).filter(model_subscription__social_account='private_feed').filter(is_subscription_cancelled=0).first()
					if subscripDetail and subscripDetail.plan_type == "recurring":
						today_date = str(datetime.datetime.today().date())+" 00:00:00"
						expiry_time = str(subscripDetail.expiry_date)+" 23:59:59"
						if expiry_time > today_date:
							ModelDetail["is_private_feed_subscribed"] = 1
						else:
							ModelDetail["is_private_feed_subscribed"] = 0
					if subscripDetail and subscripDetail.plan_type == "one_time":
						ModelDetail["is_private_feed_subscribed"] = 1
					else:
						ModelDetail["is_private_feed_subscribed"] = 0

					if followDetails:
						ModelDetail["is_followed"] = 1
					else:
						ModelDetail["is_followed"] = 0
				else:
					ModelDetail["is_followed"] = 0
					ModelDetail["is_private_feed_subscribed"] = 0

				ModelImage = ModelImages.objects.filter(user_id=ModelDetail["id"]).all()
				totalImages = ModelImages.objects.filter(user_id=ModelDetail["id"]).all().count()
	
				ModelDetail["total_images"] = totalImages
				
				if ModelImage:
					images	=	[]
					for ProfileImage in ModelImage:
						images.append(settings.MODEL_IMAGE_URL+ProfileImage.image_url)
					if ModelDetail["main_image"] == None or ModelDetail["main_image"] == "":
						ModelDetail["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
						ModelDetail["images"]			=	images
					else:
						ModelDetail["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelDetail["main_image"]
						ModelDetail["images"]			=	images
				else:
					ModelDetail["profile_image"]		=	settings.MEDIA_URL+"dummy.jpeg"
					ModelDetail["images"]				=	""
					
					
				ModelCat = ModelCategories.objects.filter(user_id=ModelDetail["id"]).all()
				#ModelCat = list(ModelCat)
				
				catDataList = []
				if ModelCat:
					for catData in ModelCat:
						catListData = {}
						catListData['name'] = catData.dropdown_manager.name
						catListData['id'] = catData.dropdown_manager_id
						catDataList.append(catListData)
					ModelDetail["categories"] = catDataList
				else:
					ModelDetail["categories"] = catDataList

				subcriptionData = ModelSubscriptions.objects.filter(user_id=ModelDetail["id"]).filter(is_enabled=1).filter(is_deleted=0).exclude(social_account="tips").all().values('id','social_account',"username","is_enabled","id")
				subscriptionEnableTip = ModelSubscriptions.objects.filter(user_id=ModelDetail["id"]).filter(is_deleted=0).filter(social_account='tips').first()
				ModelDetail['tip_enable']	=	subscriptionEnableTip.is_enabled
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).filter(is_deleted=0).all().values('id','plan_type',"offer_period_time","offer_period_type","price","discounted_price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","offer_name");
						for planData_detail in planData:
							planData_detail["social_account"] = subcription["social_account"]
							if(planData_detail["plan_type"] == "one_time"):
								if(int(planData_detail["is_discount_enabled"]) == int(1)):
									if planData_detail["discounted_price"]:
										if (decimal.Decimal(planData_detail["discounted_price"]) > decimal.Decimal(0)):
											planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["discounted_price"]))
										else:
											planData_detail["discounted_price"]		=	0.00
									else:
										planData_detail["discounted_price"]			=	0.00
								else:
									if planData_detail["price"]:
										if (decimal.Decimal(planData_detail["price"]) > decimal.Decimal(0)):
											planData_detail["plan_price_per_year"]	=	round(decimal.Decimal(planData_detail["price"]))
										else:
											planData_detail["plan_price_per_year"]	=	0.00
									else:
										planData_detail["plan_price_per_year"]	=	0.00
							else:
								if(planData_detail["offer_period_time"] == "" or int(planData_detail["offer_period_time"]) <= int(0)):
									offer_period_time	=	1
								else:
									offer_period_time	=	int(planData_detail["offer_period_time"])
								
								
								if(planData_detail["offer_period_type"] == "week"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
										
								elif(planData_detail["offer_period_type"] == "month"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
										
								elif(planData_detail["offer_period_type"] == "year"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
						
						planData = sorted(planData, key=lambda x:x['plan_price_per_year'])
						planData = list(planData)
						if planData:
							subcription['plans'] = planData	
						
				subcriptions_single	=	[]
				if subcriptionData:
					for subcription in subcriptionData:
						counter	=	0
						for planData_detail in subcription["plans"]:
							if(counter == 0):
								subcriptions_single.append(planData_detail)
								
							counter	=	int(counter)+1
				
				subcriptions_single = sorted(subcriptions_single, key=lambda x:x['plan_price_per_year'])
				
				ModelDetail['subcriptions'] = subcriptionData
				ModelDetail['subcriptions_single'] = subcriptions_single
				content = {
					"success": True,
					"data":ModelDetail,
					"msg":"",
				}
				return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Model_not_found"),
				}
				return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("Model_not_found"),
			}
			return Response(content)

class cmsPageView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET['slug'] == None or request.GET['slug'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			cmsPageDetail = CmsPage.objects.filter(slug=request.GET['slug']).first();
			if cmsPageDetail:
				cmsdata = CmsPageDescription.objects.filter(cms_page_id=cmsPageDetail.id).filter(language_code=user_language).first()
				cmsListData	=	{}
				cmsListData["page_title"]				=	cmsdata.page_title
				cmsListData["description"]				=	cmsdata.description
				content = {
					"success": True,
					"data":cmsListData,
					"msg":""
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}
				
		return Response(content)

class supportView(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")
		if request.POST.get("phone_number") == None or request.POST.get("phone_number") == "":
			validationErrors["phone_number"]	=	_("The_phone_number_field_is_required")
		else:
			PHONE_REGEX = r"(^[0-9]{10}$)"
			if request.POST.get("phone_number") and not re.match(PHONE_REGEX, request.POST.get("phone_number")):
				validationErrors["phone_number"]	=	_("This_phone_number_is_not_valid")
			
		if request.POST.get("name") == None or request.POST.get("name") == "":
			validationErrors["name"]	=	_("The_name_field_is_required")
			
		# if request.POST.get("subject") == None or request.POST.get("subject") == "":
			# validationErrors["subject"]	=	_("The_subject_field_is_required")
			
		if request.POST.get("message") == None or request.POST.get("message") == "":
			validationErrors["message"]	=	_("The_message_field_is_required")

		
			
		if not validationErrors:
			Obj						=	Support()
			Obj.email				=	request.POST.get("email")
			Obj.phone_number		=	request.POST.get("phone_number")
			Obj.name				=	request.POST.get("name")
			# Obj.subject				=	request.POST.get("subject")
			Obj.message				=	request.POST.get("message")
			Obj.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Support_request_sent_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		blockData = Block.objects.filter(page_slug="Support").filter(is_active=1).order_by("block_order").values("id")
		

		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).filter(language_code=user_language).all()  # or simply .values() to get all fields		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					# blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["slug"]					=	BlockObj.block.slug
					blocks.append(blockList)
			
			siteemail	=	[]
			siteaddress	=	[]
			sitephone	=	[]
			if settings.SITEEMAIL:
				siteemail.append(settings.SITEEMAIL)
			if settings.SITEADDRESS:
				siteaddress.append(settings.SITEADDRESS)
			if settings.SITEPHONE:
				sitephone.append(settings.SITEPHONE)
			content = {
				"success": True,
				"data":blocks,
				"siteemail":siteemail,
				"siteaddress":siteaddress,
				"sitephone":sitephone,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"siteemail":[],
				"siteaddress":[],
				"sitephone":[],
				"msg":_("No_data_found")
			}
		
				
		return Response(content)
			
class aboutView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		blockData = Block.objects.filter(page_slug="about").filter(is_active=1).order_by("block_order").values("id")
		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).filter(language_code=user_language).all()  # or simply .values() to get all fields		
			blocks	=	[]
			about_url = "https://www.youtube.com/embed/ioaTIMB8vIg?autostart=0&color=white&controls=0&showinfo=0&rel=0&disablekb=0fs=0&hl=nl-be"
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.BLOCK_IMAGE_URL+BlockObj.block.image
					blockList["slug"]					=	BlockObj.block.slug
					blocks.append(blockList)

			content = {
				"success": True,
				"data":blocks,
				"about_url":about_url,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}
		return Response(content)
		
		
class makeMoneyOne(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		blockData = Block.objects.filter(page_slug="Make-Money-1").filter(is_active=1).order_by("block_order").values("id");
		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).filter(language_code=user_language).all()  # or simply .values() to get all fields		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.BLOCK_IMAGE_URL+BlockObj.block.image
					blockList["slug"]					=	BlockObj.block.slug
					blocks.append(blockList)
			content = {
				"success": True,
				"data":blocks,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}
		
				
		return Response(content)
		
class makeMoneyTwo(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		blockData = Block.objects.filter(page_slug="Make-Money-2").filter(is_active=1).order_by("block_order").values("id")

		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).filter(language_code=user_language).all()  # or simply .values() to get all fields		
			blocks	=	[]

			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.BLOCK_IMAGE_URL+BlockObj.block.image
					blockList["slug"]					=	BlockObj.block.slug
					blocks.append(blockList)

			content = {
				"success": True,
				"data":blocks,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}
		
				
		return Response(content)
		
class verifyAccountView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		if request.GET['validate_string'] == None or request.GET['validate_string'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			userDetail = User.objects.filter(validate_string=request.GET['validate_string']).first()
			if userDetail:
				obj 				= userDetail
				obj.validate_string = ''
				obj.is_verified 	= 1
				obj.save()
				content = {
					"success": True,
					"data":[],
					"msg":_("Your_account_verified_successfully")
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}
				
		return Response(content)
		
		
class manageSubscription(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id
		subcriptionData = ModelSubscriptions.objects.filter(user_id=user_id).filter(is_deleted=0).all().values('social_account',"username","is_enabled","id")
		subcriptionData = list(subcriptionData)
		if subcriptionData:
			for subcription in subcriptionData:
				planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).filter(is_deleted=0).all().values('id','plan_type',"offer_period_time","offer_period_type","price","discounted_price","currency","description","is_discount_enabled","discount","offer_name","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills")
				
				for planData_detail in planData:
					if(planData_detail["plan_type"] == "one_time"):
						if(int(planData_detail["is_discount_enabled"]) == int(1)):
							planData_detail["plan_price_per_year"]	=	decimal.Decimal(planData_detail["discounted_price"])
						else:
							planData_detail["plan_price_per_year"]	=	decimal.Decimal(planData_detail["price"])
					else:
						if(planData_detail["offer_period_time"] == "" or int(planData_detail["offer_period_time"]) <= int(0)):
							offer_period_time	=	1
						else:
							offer_period_time	=	int(planData_detail["offer_period_time"])
						
						
						if(planData_detail["offer_period_type"] == "week"):
							if(int(planData_detail["is_discount_enabled"]) == int(1)):
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
							else:
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
								
						elif(planData_detail["offer_period_type"] == "month"):
							if(int(planData_detail["is_discount_enabled"]) == int(1)):
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
							else:
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
								
						elif(planData_detail["offer_period_type"] == "year"):
							if(int(planData_detail["is_discount_enabled"]) == int(1)):
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
							else:
								planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
				
				planData = sorted(planData, key=lambda x:x['plan_price_per_year'])
				planData = list(planData)
				subcription['plans'] = planData
		content = {
			"success": True,
			"data":subcriptionData,
			"msg":""
		}
		return Response(content)
		
	def delete(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET['sub_id'] == None or request.GET['sub_id'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			modelPlan 			= 	ModelSubscriptionPlans.objects.filter(id=request.GET['sub_id']).all().values("plan_type","is_deleted").update(is_deleted=1)

			content = {
				"success": True,
				"data":[],
				"msg":_("Subscription_plan_removed_successfully")
			}	
		return Response(content)

	
			
'''class editProfile1(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)			
			
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
			if request.POST.get("oldpassword") == None or request.POST.get("oldpassword") == "":
				validationErrors["oldpassword"]	=	_("The_old_password_field_is_required")
			else:
				lengthOldpass	=	len(request.POST.get("oldpassword"))
				if lengthOldpass < 8 :
					validationErrors["oldpassword"]	=	_("The_old_password_field_should_be_atleast_8_digits")

			if request.POST.get("newpassword") == None or request.POST.get("newpassword") == "":
				validationErrors["newpassword"]	=	_("The_new_password_field_is_required")
			else:

				lengthNewpass	=	len(request.POST.get("newpassword"))
				if lengthNewpass < 8 :
					validationErrors["newpassword"]	=	_("The_new_password_field_should_be_atleast_8_digits")

			if request.POST.get("confirmpassword") == None or request.POST.get("confirmpassword") == "":
				validationErrors["confirmpassword"]	=	_("The_confirm_password_field_is_required")
			else:
				if request.POST.get("confirmpassword") != request.POST.get("newpassword"):
					validationErrors["confirmpassword"]	=	_("The_confirm_password_and_new_password_does_not_match")

		user_id 		= request.user.id	
		userDetails		=   User.objects.filter(is_approved=1).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		
		
		if not userDetails:
			validationErrors["user"]	=	_("Invalid_request")
		
		
		if not validationErrors:
			currentpassword										=	request.user.password
			if userDetails.user_role_id == 2:
				NewUserObj										=   userDetails
				NewUserObj.skype_number							=	request.POST.get("skype_number")
				NewUserObj.model_name							=	request.POST.get("model_name")
				NewUserObj.phone_number							=	request.POST.get("phone_number")
				if request.POST.get("newpassword"):
					oldpassword			=	request.POST.get("oldpassword")
					newpassword			=	request.POST.get("newpassword")
					matchcheck= check_password(oldpassword, currentpassword)
					if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
						if matchcheck:
							NewUserObj.password							=	make_password(request.POST.get("newpassword", ""))
							NewUserObj.save()
							content = {
								"success": True,
								"data":[],
								"msg":_("Password_has_been_changed_successfully_please_login_again")
							}
							return Response(content)
						if not matchcheck:
							validationErrors["oldpassword"]	=	_("Old_password_is_not_correct")
							content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
							return Response(content)
				NewUserObj.save()
			
			else:
				lastUserId										=	user_id
				NewUserObj										=   userDetails
				if request.POST.get("type") == 'account':
					NewUserObj.model_name							=	request.POST.get("model_name")
					NewUserObj.phone_number							=	request.POST.get("phone_number")
					NewUserObj.skype_number							=	request.POST.get("skype_number")
					if request.POST.get("newpassword"):
						oldpassword			=	request.POST.get("oldpassword")
						newpassword			=	request.POST.get("newpassword")
						matchcheck= check_password(oldpassword, currentpassword)
						if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
							if matchcheck:
								NewUserObj.password							=	make_password(request.POST.get("newpassword", ""))
								NewUserObj.save()
								content = {
									"success": True,
									"data":[],
									"msg":_("Password_has_been_changed_successfully_please_login_again")
								}
								return Response(content)
						else:
							if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
								if not matchcheck:
									validationErrors["oldpassword"]	=	_("Old_password_is_not_correct")
							content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
							return Response(content)
				else:
					currentMonth = datetime.datetime.now().month
					currentYear = datetime.datetime.now().year
					folder = 'media/uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
					folder_directory = 'uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
					if not os.path.exists(folder):
						os.mkdir(folder)
					if request.POST.get("model_name") != None:
						NewUserObj.model_name							=	request.POST.get("model_name")
					if request.POST.get("bio") != None:
						NewUserObj.bio									=	request.POST.get("bio")

				
				NewUserObj.save()
				
				
				
				images 							= 	request.FILES.getlist("images")
				orientations 					=   request.POST.getlist('orientations')
				if images:
					counter = 0
					for imge in images:	
						myfile = imge
						fs = FileSystemStorage()
						filename = myfile.name.split(".")[0].lower()
						extension = myfile.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						
						angle1 = 270
						angle2 = 90
						orientation = orientations[counter]
						
						if orientation == '6':
							fs.save(folder_directory+newfilename, myfile)
							image_path = os.path.join(settings.MEDIA_ROOT+'/')
							img = Image.open(image_path+folder_directory+newfilename)
							img = img.rotate(angle1, expand=True)
							img.save(image_path+folder_directory+newfilename)
							img.close()
						elif orientation == '8':
							fs.save(folder_directory+newfilename, myfile)
							image_path = os.path.join(settings.MEDIA_ROOT+'/')
							img = Image.open(image_path+folder_directory+newfilename)
							img = img.rotate(angle2, expand=True)
							img.save(image_path+folder_directory+newfilename)
							img.close()
						else:
							fs.save(folder_directory+newfilename, myfile)
						model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
						
						ModelImagesInfo							=	ModelImages()
						ModelImagesInfo.image_url 				= 	model_image
						ModelImagesInfo.user_id 				= 	lastUserId
						ModelImagesInfo.save()
						counter  += 1
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

		
class editProfile(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id
		userDetail = User.objects.filter(id=user_id).filter(is_deleted=0).first()
		if userDetail:
			if userDetail.user_role_id == 2:
				ModelDetail = model_to_dict(userDetail)
			else:
				ModelDetail = User.objects.filter(id=user_id).filter(is_deleted=0).first()
				ModelDetail = model_to_dict(ModelDetail)
				if ModelDetail:
					ModelImage = ModelImages.objects.filter(user_id=ModelDetail["id"]).all()
					if ModelImage:
						images	=	[]
						for ProfileImage in ModelImage:
							imgList = {}
							imgList['img_url'] = settings.MEDIA_SITE_URL+"uploads/model_images/"+ProfileImage.image_url
							imgList['id'] 		= ProfileImage.id
							images.append(imgList)
						ModelDetail["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage[0].image_url
						ModelDetail["images"]			=	images
					else:
						ModelDetail["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/dummy.jpeg"
						ModelDetail["images"]			=	""
						
						
					ModelCat = ModelCategories.objects.filter(user_id=ModelDetail["id"]).all()
					#ModelCat = list(ModelCat)
					
					catDataList = []
					if ModelCat:
						for catData in ModelCat:
							catListData = {}
							catListData['name'] = catData.dropdown_manager.name
							catListData['id'] = catData.dropdown_manager_id
							catDataList.append(catListData)
						ModelDetail["categories"] = catDataList
					else:
						ModelDetail["categories"] = catDataList
			content = {
				"success": True,
				"data12":ModelDetail,
				"msg":""
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data12":[],
				"msg":_("Invalid_requst")
			}
			return Response(content)
		
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
			if request.POST.get("oldpassword") == None or request.POST.get("oldpassword") == "":
				validationErrors["oldpassword"]	=	_("The_old_password_field_is_required")
			else:
				lengthOldpass	=	len(request.POST.get("oldpassword"))
				if lengthOldpass < 8 :
					validationErrors["oldpassword"]	=	_("The_old_password_field_should_be_atleast_8_digits")

			if request.POST.get("newpassword") == None or request.POST.get("newpassword") == "":
				validationErrors["newpassword"]	=	_("The_new_password_field_is_required")
			else:

				lengthNewpass	=	len(request.POST.get("newpassword"))
				if lengthNewpass < 8 :
					validationErrors["newpassword"]	=	_("The_new_password_field_should_be_atleast_8_digits")

			if request.POST.get("confirmpassword") == None or request.POST.get("confirmpassword") == "":
				validationErrors["confirmpassword"]	=	_("The_confirm_password_field_is_required")
			else:
				if request.POST.get("confirmpassword") != request.POST.get("newpassword"):
					validationErrors["confirmpassword"]	=	_("The_confirm_password_and_new_password_does_not_match")

		user_id 		= request.user.id	
		userDetails		=   User.objects.filter(is_approved=1).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		
		
		if not userDetails:
			validationErrors["user"]	=	_("Invalid_request")
		
		
		if not validationErrors:
			currentpassword										=	request.user.password
			if userDetails.user_role_id == 2:
				NewUserObj										=   userDetails
				NewUserObj.skype_number							=	request.POST.get("skype_number")
				NewUserObj.model_name							=	request.POST.get("model_name")
				NewUserObj.phone_number							=	request.POST.get("phone_number")
				if request.POST.get("newpassword"):
					oldpassword			=	request.POST.get("oldpassword")
					newpassword			=	request.POST.get("newpassword")
					matchcheck= check_password(oldpassword, currentpassword)
					if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
						if matchcheck:
							NewUserObj.password							=	make_password(request.POST.get("newpassword", ""))
							NewUserObj.save()
							content = {
								"success": True,
								"data":[],
								"msg":_("Password_has_been_changed_successfully_please_login_again")
							}
							return Response(content)
						if not matchcheck:
							validationErrors["oldpassword"]	=	_("Old_password_is_not_correct")
							content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
							return Response(content)
				NewUserObj.save()
			
			else:
				currentMonth = datetime.datetime.now().month
				currentYear = datetime.datetime.now().year
				folder = 'media/uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
				folder_directory = 'uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
				if not os.path.exists(folder):
					os.mkdir(folder)
				
				
				gifi_image  = ''
				gibi_image  = ''
				pnti_image	= ''
				pntiwdp_image = ''

				if request.FILES.get("government_id_front_image") != None:
					if request.FILES.get("government_id_front_image"):
						gifiFile = request.FILES.get("government_id_front_image")
						fs = FileSystemStorage()
						filename = gifiFile.name.split(".")[0].lower()
						extension = gifiFile.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						fs.save(folder_directory+newfilename, gifiFile)	
						gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename

				if request.FILES.get("government_id_back_image") != None:
					if request.FILES.get("government_id_back_image"):
						gibiFile = request.FILES.get("government_id_back_image")
						fs = FileSystemStorage()
						filename = gibiFile.name.split(".")[0].lower()
						extension = gibiFile.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						fs.save(folder_directory+newfilename, gibiFile)	
						gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				if request.FILES.get("photo_next_to_id") != None:
					if request.FILES.get("photo_next_to_id"):
						pntiFile = request.FILES.get("photo_next_to_id")
						fs = FileSystemStorage()
						filename = pntiFile.name.split(".")[0].lower()
						extension = pntiFile.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						fs.save(folder_directory+newfilename, pntiFile)	
						pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename

				if request.FILES.get("photo_next_to_id_with_dated_paper") != None:	
					if request.FILES.get("photo_next_to_id_with_dated_paper"):
						pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
						fs = FileSystemStorage()
						filename = pntiwdpFile.name.split(".")[0].lower()
						extension = pntiwdpFile.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						fs.save(folder_directory+newfilename, pntiwdpFile)	
						pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				
				lastUserId										=	user_id
				NewUserObj										=   userDetails
				if request.POST.get("type") == 'account':
					NewUserObj.model_name							=	request.POST.get("model_name")
					NewUserObj.phone_number							=	request.POST.get("phone_number")
					NewUserObj.skype_number							=	request.POST.get("skype_number")
					if request.POST.get("newpassword"):
						oldpassword			=	request.POST.get("oldpassword")
						newpassword			=	request.POST.get("newpassword")
						matchcheck= check_password(oldpassword, currentpassword)
						if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
							if matchcheck:
								NewUserObj.password							=	make_password(request.POST.get("newpassword", ""))
								NewUserObj.save()
								content = {
									"success": True,
									"data":[],
									"msg":_("Password_has_been_changed_successfully_please_login_again")
								}
								return Response(content)
						else:
							if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
								if not matchcheck:
									validationErrors["oldpassword"]	=	_("Old_password_is_not_correct")
							content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
							return Response(content)
				else:
					if request.POST.get("first_name") != None:
						NewUserObj.first_name							=	request.POST.get("first_name")
					if request.POST.get("last_name") != None:
						NewUserObj.last_name							=	request.POST.get("last_name")
					if request.POST.get("previous_first_name") != None:
						NewUserObj.previous_first_name					=	request.POST.get("previous_first_name")
					if request.POST.get("previous_last_name") != None:
						NewUserObj.previous_last_name					=	request.POST.get("previous_last_name")
					if request.POST.get("date_of_birth") != None:
						NewUserObj.date_of_birth						=	request.POST.get("date_of_birth")
					if request.POST.get("gender") != None:
						NewUserObj.gender								=	request.POST.get("gender")
					if request.POST.get("country") != None:
						NewUserObj.country								=	request.POST.get("country")
					if request.POST.get("address_line_1") != None:
						NewUserObj.address_line_1						=	request.POST.get("address_line_1")
					if request.POST.get("address_line_2") != None:
						NewUserObj.address_line_2						=	request.POST.get("address_line_2")
					if request.POST.get("city") != None:
						NewUserObj.city									=	request.POST.get("city")
					if request.POST.get("postal_code") != None:
						NewUserObj.postal_code							=	request.POST.get("postal_code")
					if request.POST.get("skype_number") != None:
						NewUserObj.skype_number							=	request.POST.get("skype_number")
					if request.POST.get("best_known_for") != None:
						NewUserObj.best_known_for						=	request.POST.get("best_known_for")
					if request.POST.get("private_snapchat_link") != None:
						NewUserObj.private_snapchat_link				=	request.POST.get("private_snapchat_link")
					if request.POST.get("public_snapchat_link") != None:
						NewUserObj.public_snapchat_link					=	request.POST.get("public_snapchat_link")
					if request.POST.get("public_instagram_link") != None:
						NewUserObj.public_instagram_link				=	request.POST.get("public_instagram_link")
					if request.POST.get("twitter_link") != None:
						NewUserObj.twitter_link							=	request.POST.get("twitter_link")
					if request.POST.get("youtube_link") != None:
						NewUserObj.youtube_link							=	request.POST.get("youtube_link")
					if request.POST.get("amazon_wishlist_link") != None:
						NewUserObj.amazon_wishlist_link					=	request.POST.get("amazon_wishlist_link")
					if request.POST.get("age") != None:
						NewUserObj.age									=	request.POST.get("age")
					if request.POST.get("from_date") != None:
						NewUserObj.from_date							=	request.POST.get("from_date")
					if request.POST.get("height") != None:
						NewUserObj.height								=	request.POST.get("height")
					if request.POST.get("weight") != None:
						NewUserObj.weight								=	request.POST.get("weight")
					if request.POST.get("hair") != None:
						NewUserObj.hair									=	request.POST.get("hair")
					if request.POST.get("eyes") != None:
						NewUserObj.eyes									=	request.POST.get("eyes")
					if request.POST.get("youtube_video_url") != None:
						NewUserObj.youtube_video_url					=	request.POST.get("youtube_video_url")
					if request.POST.get("government_id_number") != None:
						NewUserObj.government_id_number					=	request.POST.get("government_id_number")
					if request.POST.get("government_id_expiration_date") != None:
						NewUserObj.government_id_expiration_date		=	request.POST.get("government_id_expiration_date")
					if request.POST.get("phone_number") != None:
						NewUserObj.phone_number							=	request.POST.get("phone_number")
					if request.FILES.get("government_id_front_image") != None:
						NewUserObj.government_id_front_image			=	gifi_image
					if request.FILES.get("government_id_back_image") != None:
						NewUserObj.government_id_back_image				=	gibi_image
					if request.FILES.get("photo_next_to_id") != None:
						NewUserObj.photo_next_to_id						=	pnti_image
					if request.FILES.get("photo_next_to_id_with_dated_paper") != None:
						NewUserObj.photo_next_to_id_with_dated_paper	=	pntiwdp_image
				
				NewUserObj.save()
				
				
						
				categories 					=   request.POST.get('categories')
				if categories != None and categories != "":
					ModelCategories.objects.filter(user_id=request.user.id).delete()
					categories = categories.split(',')
					for category in categories:
						ModelCategoriesInfo							=	ModelCategories()
						ModelCategoriesInfo.dropdown_manager_id 	= 	category
						ModelCategoriesInfo.user_id 				= 	lastUserId
						ModelCategoriesInfo.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)'''
		
class followModel(generics.CreateAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}	
		if request.POST.get("model_id") == None or request.POST.get("model_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
			return Response(content)
		else:
			followDetails	=   ModelFollower.objects.filter(subscriber_id=request.user.id).filter(model_id=request.POST.get("model_id")).first()	
			if not followDetails:
				Obj						=	ModelFollower()
				Obj.subscriber_id		=	request.user.id
				Obj.model_id			=	request.POST.get("model_id")
				Obj.save()
				content = {
					"success": True,
					"data":[],
					"status":1,
					"msg":_("Model_followed_successfully")
				}
				return Response(content)
			else:
				ModelFollower.objects.filter(subscriber_id=request.user.id).filter(model_id=request.POST.get("model_id")).delete()
				content = {
					"success": True,
					"data":[],
					"status":0,
					"msg":_("Model_unfollowed_successfully")
				}
				return Response(content)
				
				
class newModels(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		NewProfiles = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).order_by("-updated_at").all()[:10]
		NewProfiles = list(NewProfiles)  # important: convert the QuerySet to a list object
		
		profiles	=	[]
		if NewProfiles:
			for Profile in NewProfiles:
				profile					=	{}
				profile["model_name"]	=	Profile.model_name
				profile["slug"]			=	Profile.slug
				profile["bio"]			=	Profile.bio
				profile["amazon_wishlist_link"]			=	Profile.amazon_wishlist_link
				profile["private_snapchat_link"]			=	Profile.private_snapchat_link
				profile["public_instagram_link"]			=	Profile.public_instagram_link
				profile["public_snapchat_link"]			=	Profile.public_snapchat_link
				profile["twitter_link"]					=	Profile.twitter_link
				profile["youtube_link"]					=	Profile.youtube_link
				profile["user_id"]							=	Profile.id
				ModelImage = ModelImages.objects.filter(user_id=Profile.id).all()
					
				if ModelImage:
					images	=	[]
					for ProfileImage in ModelImage:
						images.append(settings.MODEL_IMAGE_URL+ProfileImage.image_url)

					profile["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
					profile["images"]			=	images
				else:
					profile["profile_image"]	=	settings.MEDIA_URL+"dummy.jpeg"
					profile["images"]			=	""
					
					
				subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).filter(is_enabled=1).filter(is_deleted=0).exclude(social_account='tips').all().values('social_account',"username","is_enabled","id");
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).filter(is_deleted=0).all().values('plan_type',"offer_period_time","offer_period_type","price","discounted_price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills","offer_name")
						for planData_detail in planData:
							planData_detail["social_account"] =	subcription["social_account"]
							if(planData_detail["plan_type"] == "one_time"):
								if(int(planData_detail["is_discount_enabled"]) == int(1)):
									planData_detail["plan_price_per_year"]	=	decimal.Decimal(planData_detail["discounted_price"])
								else:
									planData_detail["plan_price_per_year"]	=	decimal.Decimal(planData_detail["price"])
							else:
								if(planData_detail["offer_period_time"] == "" or int(planData_detail["offer_period_time"]) <= int(0)):
									offer_period_time	=	1
								else:
									offer_period_time	=	int(planData_detail["offer_period_time"])
								
								
								if(planData_detail["offer_period_type"] == "week"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(52))
										
								elif(planData_detail["offer_period_type"] == "month"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(12))
										
								elif(planData_detail["offer_period_type"] == "year"):
									if(int(planData_detail["is_discount_enabled"]) == int(1)):
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["discounted_price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
									else:
										planData_detail["plan_price_per_year"]	=	round((decimal.Decimal(planData_detail["price"])/decimal.Decimal(offer_period_time))*decimal.Decimal(1))
						
						planData = sorted(planData, key=lambda x:x['plan_price_per_year'])
						planData = list(planData)
						if planData:
							subcription['plans'] = planData	
							
							
				subcriptions_single	=	[]
				if subcriptionData:
					for subcription in subcriptionData:
						counter	=	0
						for planData_detail in subcription["plans"]:
							if(counter == 0):
								subcriptions_single.append(planData_detail)
								
							counter	=	int(counter)+1
				
				profile['subcriptions'] = subcriptionData
				subcriptions_single = sorted(subcriptions_single, key=lambda x:x['plan_price_per_year'])
				profile['subcriptions_single'] = subcriptions_single

				profiles.append(profile)
				
				

		content = {
			"success": True,
			"data":profiles,
			"msg":""
		}
		return Response(content)
		
class followingList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		followList	=   ModelFollower.objects.filter(subscriber_id=request.user.id).all().values("model_id")
		if followList:
			FollowingProfiles = User.objects.filter(id__in=followList).filter(is_deleted=0).all()
			FollowingProfiles = list(FollowingProfiles)  # important: convert the QuerySet to a list object
			profiles	=	[]
			if FollowingProfiles:
				for Profile in FollowingProfiles:
					profile								=	{}
					profile["model_name"]				=	Profile.model_name
					profile["slug"]						=	Profile.slug
					profile["bio"]						=	Profile.bio
					profile["amazon_wishlist_link"]		=	Profile.amazon_wishlist_link
					profile["private_snapchat_link"]	=	Profile.private_snapchat_link
					profile["public_instagram_link"]	=	Profile.public_instagram_link
					profile["public_snapchat_link"]		=	Profile.public_snapchat_link
					profile["twitter_link"]				=	Profile.twitter_link
					profile["youtube_link"]				=	Profile.youtube_link
					profile["user_id"]					=	Profile.id
					ModelImage = ModelImages.objects.filter(user_id=Profile.id).first()
					if ModelImage:
						profile["profile_image"]					=	settings.MODEL_IMAGE_URL+ModelImage.image_url
					else:
						profile["profile_image"]					=	settings.MEDIA_URL+"dummy.jpeg"
						
					profiles.append(profile)
			content = {
				"success": True,
				"data":profiles,
				"msg":_("Following_listed_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_followings_found")
			}
			return Response(content)
		
			
class deleteImage(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def delete(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET['img_id'] == None or request.GET['img_id'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			
			ModelImages.objects.filter(id=request.GET['img_id']).all().delete()
			content = {
				"success": True,
				"data":[],
				"msg":_("Image_removed_successfully")
			}	
		return Response(content)
		
class manageNotifications(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id
		notificationData = ModelNotificationSetting.objects.filter(user_id=user_id).first()

		if notificationData:
			notificationData = model_to_dict(notificationData)
		content = {
			"success": True,
			"data":notificationData,
			"msg":""
		}
		return Response(content)
	
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		
		user_id = request.user.id	
		if not validationErrors:
			NotiSettingObj										=   ModelNotificationSetting.objects.filter(user_id=user_id).first()
			if NotiSettingObj:
				NotiSettingObj = NotiSettingObj
			else:
				NotiSettingObj  = ModelNotificationSetting()
				NotiSettingObj.user_id = user_id
			NotiSettingObj.new_subscription_purchased 			= 	request.POST.get("new_subscription_purchased",1)
			NotiSettingObj.subscription_expires 				= 	request.POST.get("subscription_expires",1)
			NotiSettingObj.received_tip 						= 	request.POST.get("received_tip",1)
			NotiSettingObj.subscriber_updates_snapchat_name 	= 	request.POST.get("subscriber_updates_snapchat_name",1)
			NotiSettingObj.detects_login_unverified_device 		= 	request.POST.get("detects_login_unverified_device",1)
			NotiSettingObj.detects_unsuccessful_login 			= 	request.POST.get("detects_unsuccessful_login",1)
			NotiSettingObj.save()
			content = {
				"success": True,
				"data":[],
				"msg":_("Notification_setting_updated_sucessfully")
			}
			return Response(content)

class UserSubscribe(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		email= request.POST.get("email",'')
		userDetails		=   User.objects.filter(email=email).first()
		if userDetails:
			content = {
				"success": True,
				"data":[],
				"token":jwt_encode_handler(jwt_payload_handler(userDetails)),
				"msg":_("User_already_exiets_Please_login_to_process")
			}
			return Response(content)
		else:
			strEmal = str(email)
			res = hashlib.md5(strEmal.encode()) 
			validatestring = res.hexdigest() 
			password = 'System@123'
			new_user = User.objects.create_user(
				username=email, password=password, email=email, user_role_id=2,is_approved=1,is_verified=1,validate_string=validatestring
			)
			lastUserId	=	new_user.id
			
			if lastUserId :
				user_details 	= 	User.objects.filter(id=lastUserId).first()
				###verification email
				username 		= 	email
				email 			=	email
				link			=  	settings.FRONT_SITE_URL+'verify-account?validate_string='+validatestring
				emailaction				=EmailAction.objects.filter(action="account_verification").first()
				emailTemplates			=EmailTemplates.objects.filter(action = 'account_verification').first()
				constant = list()
				data = (emailaction.option.split(','))
				for obj in data:
					constant.append("{"+ obj +"}")
				subject=emailTemplates.subject
				rep_Array=[email,link]
				massage_body  = emailTemplates.body
				website_url		=	settings.FRONT_SITE_URL
				site_title		=	settings.SITETITLE
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
				#sendEmail(request,subject,html_content,email)
				###verification email
				
				
				
			content = {
				"success": True,
				"data":[],
				"token":jwt_encode_handler(jwt_payload_handler(user_details)),
				"msg":_("Your_account_has_been_registered_successfully")
			}
			return Response(content)			
			
class saveUserSubscription(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		validationErrors	=	{}
		if request.POST.get("cardNumber") == None or request.POST.get("cardNumber") == "":
			validationErrors["cardNumber"]	=	_("The_card_number_field_is_required")
		else:
			lengthcardNumber	=	len(str(request.POST.get("cardNumber")))
			if int(lengthcardNumber) > 16 or int(lengthcardNumber) < 16 :
				validationErrors["cardNumber"]	=	_("The_card_number_field_should_be_exactly_of_16_digits.")

		if request.POST.get("cvv") == None or request.POST.get("cvv") == "":
			validationErrors["cvv"]	=	_("The_cvv_field_is_required")
		else:
			lengthcvv	=	len(str(request.POST.get("cvv")))
			if int(lengthcvv) > 3 or int(lengthcvv) < 3 :
				validationErrors["cvv"]	=	_("The_cvv_field_should_be_exactly_of_3_digits.")


		if request.POST.get("expiry_month") == None or request.POST.get("expiry_month") == "" or request.POST.get("expiry_year") == None or request.POST.get("expiry_year") == "":
			validationErrors["expiry_date"]	=	_("The_expiry_date_field_is_required")

		else:
			expiry_month = request.POST.get("expiry_month")
			expiry_year = request.POST.get("expiry_year")
			expiry_date = expiry_year+"-"+expiry_month
			# currentMonth = str(datetime.datetime.now().month)
			# currentYear = str(datetime.datetime.now().year)
			# currentYear = currentYear[2:]

			currentDate = datetime.datetime.today().strftime('%Y-%m')
            
			if expiry_date < currentDate:
				validationErrors["expiry_date"]	=	_("The_expiry_date_field_is_not_valid")
		

		if request.POST.get("account_holder") == None or request.POST.get("account_holder") == "":
			validationErrors["account_holder"]	=	_("The_account_holder_field_is_required")
			
		if not validationErrors:
			email= request.POST.get("email",'')
			userDetails		=   User.objects.filter(email=email).filter(is_deleted=0).first()
			if userDetails:
				if int(userDetails.user_role_id) == int(3):
					content = {
						"success": False,
						"data":[],
						"msg":_("You cannot subscribe with selected email. The email has already associated with a model.")
					}
					return Response(content)
					
				lastUserId	=	userDetails.id
			else:
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				password = User.objects.make_random_password()
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=2,is_approved=1,is_verified=1,validate_string=validatestring
				)
				lastUserId				=	new_user.id
				user_agent				=	request.META['HTTP_USER_AGENT']
				user_agent_calc 		=	parse(user_agent)
				user_browser			=	user_agent_calc.browser.family
				user_browser_version	=	user_agent_calc.browser.version_string
				user_os					=	user_agent_calc.os.family
				browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'
				IPAddr 					= 	get_client_ip(request)

				if lastUserId :
					AuthorizeDevicesInfo									=	AuthorizeDevices()
					AuthorizeDevicesInfo.user_id 							= 	lastUserId
					AuthorizeDevicesInfo.user_agent							= 	user_agent
					AuthorizeDevicesInfo.browser_device						= 	browser_detail
					AuthorizeDevicesInfo.ip_address 						= 	IPAddr
					AuthorizeDevicesInfo.save()

					ModelNotificationInfo									=	ModelNotificationSetting()
					ModelNotificationInfo.user_id 							= 	lastUserId
					ModelNotificationInfo.new_subscription_purchased 		= 	1
					ModelNotificationInfo.subscription_expires 				= 	1
					ModelNotificationInfo.received_tip 						= 	1
					ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
					ModelNotificationInfo.detects_login_unverified_device 	= 	1
					ModelNotificationInfo.detects_unsuccessful_login 		= 	1
					ModelNotificationInfo.save()

					user_details 	= 	User.objects.filter(id=lastUserId).first()
					##verification email
					username 		= 	email
					email 			=	email
					link			=  	settings.FRONT_SITE_URL+'verify-account?validate_string='+validatestring
					emailaction				=EmailAction.objects.filter(action="user_registration").first()
					emailTemplates			=EmailTemplates.objects.filter(action = 'user_registration').first()
					constant = list()
					data = (emailaction.option.split(','))
					for obj in data:
						constant.append("{"+ obj +"}")
					subject=emailTemplates.subject
					website_url		=	settings.FRONT_SITE_URL
					rep_Array=[email,password,website_url]
					massage_body  = emailTemplates.body
					site_title		=	settings.SITETITLE
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

			sub_type 		= 	request.POST.get("subscription_type",'')
			model_id 		= 	request.POST.get("model_id",'')
			user_id 		= 	lastUserId
			today = datetime.date.today()
			
			#subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).filter(expiry_date__gte=today).first()
			
			subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).filter(plan_status='active').filter(is_subscription_cancelled=0).first()
			
			if subDetails:
				content = {
					"success": False,
					"data":[],
					"msg":_("You_have_already_Subscribe_for_this_plan")
				}
				return Response(content)
			else:
				planInfo = ModelSubscriptionPlans.objects.filter(id=request.POST.get("plan_type",'')).filter(is_deleted=0).first()
				if(int(planInfo.is_discount_enabled) == int(1)):
					amount  = 	decimal.Decimal(planInfo.discounted_price)
					amount	=	round(amount,2)
				else:
					amount  = 	decimal.Decimal(planInfo.price)
					amount	=	round(amount,2)
				
				modelDetails	= 	User.objects.filter(id=model_id).first()
				order_id		=	random.randint(1000000000000000000,9223372036854775806)
				
				context	=	{"model_name":modelDetails.model_name,"amount":amount,"currency":modelDetails.default_currency,"order_id":order_id,"card_number":request.POST.get("cardNumber",""),"exp_year":request.POST.get("expiry_year",""),"exp_month":request.POST.get("expiry_month",""),"cvc":request.POST.get("cvv",""),"holder":request.POST.get("account_holder","")}
				address = settings.PAYMENT_GATEWAY_CREATE_PAYMENT_PATH
				r	=	requests.post(address, data=context)
				response		=	json.loads(r.content.decode('utf-8'))
				transaction_id	=	""
				transaction_payment_id	=	""
				if response["status"] and response["status"] == "success":
					if response["response"] and response["response"]["status"] == "approved":
						transaction_id	=	response["response"]["id"]
						transaction_payment_id	=	response["response"]["id"]
					elif response["response"] and response["response"]["status"] == "pending":
						transaction_id	=	response["response"]["id"]
						content = {
							"success": "pending",
							"data":response["response"]["authorization_information"],
							"transaction_payment_id":transaction_id,
							"msg":""
						}
						return Response(content)
					else:
						priceInModelCurrency = 0						

						socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()
						paymentErroraObj  									= 	PaymentGatewayErrors()
						paymentErroraObj.user_id 								=   lastUserId
						if socialAccountFeed.social_account	== 'private_feed':
							new_username 									= 	request.POST.get("email")
							new_username 									= 	new_username.split("@")[0]
							paymentErroraObj.username 						= 	new_username
						else:
							paymentErroraObj.username 						= 	request.POST.get("username",'')
							
						paymentErroraObj.email 								= 	request.POST.get("email",'')
						paymentErroraObj.sub_name 							= 	request.POST.get("sub_name",'')
						paymentErroraObj.post_code 							= 	request.POST.get("post_code",'')
						paymentErroraObj.amount 								= 	request.POST.get("amount",'')
						paymentErroraObj.price_in_model_currency 				= 	priceInModelCurrency
						paymentErroraObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
						paymentErroraObj.plan_type_id 						= 	request.POST.get("plan_type",'')
						paymentErroraObj.model_user_id 						= 	request.POST.get("model_id",'')
						paymentErroraObj.subscription_desc 					= 	""
						paymentErroraObj.expiry_date 							= 	None
						paymentErroraObj.plan_status 							= 	"active"
						paymentErroraObj.plan_validity						=	planInfo.offer_period_type
						paymentErroraObj.transaction_id						=	""
						paymentErroraObj.transaction_payment_id				=	""
						
						
						paymentErroraObj.user_subscription_plan_description				=	planInfo.description
						paymentErroraObj.plan_type				=	planInfo.plan_type
						paymentErroraObj.offer_period_time		=	planInfo.offer_period_time
						paymentErroraObj.offer_period_type		=	planInfo.offer_period_type
						paymentErroraObj.is_discount_enabled		=	planInfo.is_discount_enabled	
						paymentErroraObj.discount					=	planInfo.discount		
						paymentErroraObj.from_discount_date		=	planInfo.from_discount_date		
						paymentErroraObj.to_discount_date			=	planInfo.to_discount_date		
						paymentErroraObj.is_permanent_discount	=	planInfo.is_permanent_discount		
						paymentErroraObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
						paymentErroraObj.planprice				=	planInfo.price		
						paymentErroraObj.discounted_price			=	planInfo.discounted_price
						paymentErroraObj.response				=	r.content
						paymentErroraObj.transaction_type		=	"subscription"
						
						paymentErroraObj.save()

						content = {
							"success": False,
							"data":[],
							"msg":"Your payment has been failed. Please try again."
						}
						return Response(content)
							
				else:
					priceInModelCurrency = 0						

					socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()
					paymentErroraObj  									= 	PaymentGatewayErrors()
					paymentErroraObj.user_id 								=   lastUserId
					if socialAccountFeed.social_account	== 'private_feed':
						new_username 									= 	request.POST.get("email")
						new_username 									= 	new_username.split("@")[0]
						paymentErroraObj.username 						= 	new_username
					else:
						paymentErroraObj.username 						= 	request.POST.get("username",'')
						
					paymentErroraObj.email 								= 	request.POST.get("email",'')
					paymentErroraObj.sub_name 							= 	request.POST.get("sub_name",'')
					paymentErroraObj.post_code 							= 	request.POST.get("post_code",'')
					paymentErroraObj.amount 								= 	request.POST.get("amount",'')
					paymentErroraObj.price_in_model_currency 				= 	priceInModelCurrency
					paymentErroraObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
					paymentErroraObj.plan_type_id 						= 	request.POST.get("plan_type",'')
					paymentErroraObj.model_user_id 						= 	request.POST.get("model_id",'')
					paymentErroraObj.subscription_desc 					= 	""
					paymentErroraObj.expiry_date 							= 	None
					paymentErroraObj.plan_status 							= 	"active"
					paymentErroraObj.plan_validity						=	planInfo.offer_period_type
					paymentErroraObj.transaction_id						=	""
					paymentErroraObj.transaction_payment_id				=	""
					
					
					paymentErroraObj.user_subscription_plan_description				=	planInfo.description
					paymentErroraObj.plan_type				=	planInfo.plan_type
					paymentErroraObj.offer_period_time		=	planInfo.offer_period_time
					paymentErroraObj.offer_period_type		=	planInfo.offer_period_type
					paymentErroraObj.is_discount_enabled		=	planInfo.is_discount_enabled	
					paymentErroraObj.discount					=	planInfo.discount		
					paymentErroraObj.from_discount_date		=	planInfo.from_discount_date		
					paymentErroraObj.to_discount_date			=	planInfo.to_discount_date		
					paymentErroraObj.is_permanent_discount	=	planInfo.is_permanent_discount		
					paymentErroraObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
					paymentErroraObj.planprice				=	planInfo.price		
					paymentErroraObj.discounted_price			=	planInfo.discounted_price
					paymentErroraObj.response				=	r.content	
					paymentErroraObj.transaction_type		=	"subscription"
					
					paymentErroraObj.save()
					content = {
						"success": False,
						"data":[],
						"msg":_("Your payment has been failed. Please try again.")
					}
					return Response(content)
				
				
				
				priceInModelCurrency = 0
				
				if(planInfo.plan_type == "recurring"):
					if planInfo.offer_period_type == 'week':
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*7))
					elif planInfo.offer_period_type == 'month':
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*30))
					else:
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*365.25))
				else:
					expiry_date	=	None

				socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()

				userSubPlanObj  									= 	UserSubscriptionPlan()
				userSubPlanObj.user_id 								=   user_id
				if socialAccountFeed.social_account	== 'private_feed':
					new_username 									= 	request.POST.get("email")
					new_username 									= 	new_username.split("@")[0]
					userSubPlanObj.username 						= 	new_username
				else:
					userSubPlanObj.username 						= 	request.POST.get("username",'')
					
				userSubPlanObj.email 								= 	request.POST.get("email",'')
				userSubPlanObj.sub_name 							= 	request.POST.get("sub_name",'')
				userSubPlanObj.post_code 							= 	request.POST.get("post_code",'')
				userSubPlanObj.amount 								= 	request.POST.get("amount",'')
				userSubPlanObj.price_in_model_currency 				= 	priceInModelCurrency
				userSubPlanObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
				userSubPlanObj.plan_type_id 						= 	request.POST.get("plan_type",'')
				userSubPlanObj.model_user_id 						= 	request.POST.get("model_id",'')
				userSubPlanObj.subscription_desc 					= 	""
				userSubPlanObj.expiry_date 							= 	expiry_date
				userSubPlanObj.plan_status 							= 	"active"
				userSubPlanObj.plan_validity						=	planInfo.offer_period_type
				userSubPlanObj.transaction_id						=	transaction_id
				userSubPlanObj.transaction_payment_id				=	transaction_payment_id
				
				
				userSubPlanObj.user_subscription_plan_description				=	planInfo.description
				userSubPlanObj.plan_type				=	planInfo.plan_type
				userSubPlanObj.offer_period_time		=	planInfo.offer_period_time
				userSubPlanObj.offer_period_type		=	planInfo.offer_period_type
				userSubPlanObj.is_discount_enabled		=	planInfo.is_discount_enabled	
				userSubPlanObj.discount					=	planInfo.discount		
				userSubPlanObj.from_discount_date		=	planInfo.from_discount_date		
				userSubPlanObj.to_discount_date			=	planInfo.to_discount_date		
				userSubPlanObj.is_permanent_discount	=	planInfo.is_permanent_discount		
				userSubPlanObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
				userSubPlanObj.planprice				=	planInfo.price		
				userSubPlanObj.discounted_price			=	planInfo.discounted_price		
				userSubPlanObj.offer_name				=	planInfo.offer_name		
				userSubPlanObj.offer_description		=	planInfo.description		
				
				userSubPlanObj.save()
				
				
				
				transactionObj										=	TransactionHistory()
				transactionObj.user_id								=	user_id
				transactionObj.model_id								=	request.POST.get("model_id",'')
				transactionObj.amount								=	userSubPlanObj.amount
				transactionObj.expiry_date							=	expiry_date
				transactionObj.price_in_model_currency				=	priceInModelCurrency
				transactionObj.transaction_date						=	datetime.date.today()
				transactionObj.model_subscription_id				=	request.POST.get("subscription_type",'')
				transactionObj.plan_id								=	request.POST.get("plan_type",'')
				transactionObj.transaction_type						= 	'subscription'
				transactionObj.payment_type							= 	'joins'
				transactionObj.transaction_id						=	transaction_id
				transactionObj.status								=	'success'
				transactionObj.currency								=	modelDetails.default_currency
				transactionObj.user_subscription_id					=	userSubPlanObj.id
				
				web_commission 		= settings.SITEWEBSITECOMMISSION
				SettingDetails = Setting.objects.filter(key="Site.websiteCommission").first()
				if SettingDetails:
					web_commission	=	SettingDetails.value
					
				if(decimal.Decimal(web_commission) > decimal.Decimal(0)):
					t_commission	=	round((decimal.Decimal(web_commission)/100)*decimal.Decimal(transactionObj.amount),2)
				else:
					t_commission			=	0
					
				transactionObj.commission	=	t_commission
				transactionObj.save()
				
				arrayData						=	{}
				arrayData['socialAccount']		=	planInfo.model_subscription.social_account
				arrayData['currency']			=	modelDetails.default_currency
				arrayData['price']				=	userSubPlanObj.amount
				arrayData['model_subscription_username']				=	planInfo.model_subscription.username
				arrayData['model_subscription_username']				=	planInfo.model_subscription.username
				arrayData['subscriber_subscription_username']				=	userSubPlanObj.username
				
				if planInfo.offer_name:
					arrayData['offer_name']								=	planInfo.offer_name
				else:
					arrayData['offer_name']								=		""
				commonMail(request,"PLAN_PURCHASE",userSubPlanObj.model_user_id,userSubPlanObj.user_id,arrayData)
				
				# userSubscriptionPlanDetails 					= 	UserSubscriptionPlan.objects.filter(id=userSubPlanObj.id).first()
				# userSubscriptionPlanDetails.transaction_id		=	transactionObj.transaction_id
				# userSubscriptionPlanDetails.save()
				
				

			
			
				user		=   User.objects.filter(id=lastUserId).filter(is_deleted=0).first()
				userDetail	=	{
							"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status,"is_private_feed":user.is_private_feed
						}
				
				sub_data						=	{}
				sub_data["transaction_id"]		=	transactionObj.transaction_id
				sub_data["amount"]				=	userSubPlanObj.amount
				
				content = {
					"success": True,
					"result":[sub_data],
					"data":userDetail,
					"token":jwt_encode_handler(jwt_payload_handler(user)),
					"msg":_("Plan_subscribed_successfully")
				}
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
		return Response(content)
		
class saveUserSubscriptionfinalize(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		validationErrors	=	{}
		
		if request.POST.get("payment_id") == None or request.POST.get("payment_id") == "":
			validationErrors["payment_id"]	=	_("The_payment_id_field_is_required")
			
		if not validationErrors:
			payment_id= request.POST.get("payment_id",'')
			authorize_data= request.POST.get("authorize_data",'')
			
			
			email= request.POST.get("email",'')
			userDetails		=   User.objects.filter(email=email).filter(is_deleted=0).first()
			if userDetails:
				lastUserId	=	userDetails.id
			else:
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				password = User.objects.make_random_password()
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=2,is_approved=1,is_verified=1,validate_string=validatestring
				)
				lastUserId				=	new_user.id
				user_agent				=	request.META['HTTP_USER_AGENT']
				user_agent_calc 		=	parse(user_agent)
				user_browser			=	user_agent_calc.browser.family
				user_browser_version	=	user_agent_calc.browser.version_string
				user_os					=	user_agent_calc.os.family
				browser_detail			=	user_browser+' '+user_browser_version +' '+'('+user_os+')'
				IPAddr 					= 	get_client_ip(request)

				if lastUserId :
					AuthorizeDevicesInfo									=	AuthorizeDevices()
					AuthorizeDevicesInfo.user_id 							= 	lastUserId
					AuthorizeDevicesInfo.user_agent							= 	user_agent
					AuthorizeDevicesInfo.browser_device						= 	browser_detail
					AuthorizeDevicesInfo.ip_address 						= 	IPAddr
					AuthorizeDevicesInfo.save()

					ModelNotificationInfo									=	ModelNotificationSetting()
					ModelNotificationInfo.user_id 							= 	lastUserId
					ModelNotificationInfo.new_subscription_purchased 		= 	1
					ModelNotificationInfo.subscription_expires 				= 	1
					ModelNotificationInfo.received_tip 						= 	1
					ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	1
					ModelNotificationInfo.detects_login_unverified_device 	= 	1
					ModelNotificationInfo.detects_unsuccessful_login 		= 	1
					ModelNotificationInfo.save()

					user_details 	= 	User.objects.filter(id=lastUserId).first()
					##verification email
					username 		= 	email
					email 			=	email
					link			=  	settings.FRONT_SITE_URL+'verify-account?validate_string='+validatestring
					emailaction				=EmailAction.objects.filter(action="user_registration").first()
					emailTemplates			=EmailTemplates.objects.filter(action = 'user_registration').first()
					constant = list()
					data = (emailaction.option.split(','))
					for obj in data:
						constant.append("{"+ obj +"}")
					subject=emailTemplates.subject
					website_url		=	settings.FRONT_SITE_URL
					rep_Array=[email,password,website_url]
					massage_body  = emailTemplates.body
					site_title		=	settings.SITETITLE
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

			sub_type 		= 	request.POST.get("subscription_type",'')
			model_id 		= 	request.POST.get("model_id",'')
			user_id 		= 	lastUserId
			today = datetime.date.today()
			
			#subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).filter(expiry_date__gte=today).first()
			
			subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).filter(plan_status='active').filter(is_subscription_cancelled=0).first()
			
			if subDetails:
				content = {
					"success": False,
					"data":[],
					"msg":_("You_have_already_Subscribe_for_this_plan")
				}
				return Response(content)
			else:
				planInfo = ModelSubscriptionPlans.objects.filter(id=request.POST.get("plan_type",'')).filter(is_deleted=0).first()
				if(int(planInfo.is_discount_enabled) == int(1)):
					amount  = 	decimal.Decimal(planInfo.discounted_price)
					amount	=	round(amount,2)
				else:
					amount  = 	decimal.Decimal(planInfo.price)
					amount	=	round(amount,2)
				
				modelDetails	= 	User.objects.filter(id=model_id).first()
				order_id		=	random.randint(1000000000000000000,9223372036854775806)
				
				transaction_id			=	payment_id
				transaction_payment_id	=	payment_id
				
				FinalizedTransactionInfo	= 	FinalizedTransaction.objects.filter(transaction_id=transaction_id).first()
				if FinalizedTransactionInfo:
					if(FinalizedTransactionInfo.status == "approved"):
						transaction_id			=	payment_id
						transaction_payment_id	=	payment_id
						
						FinalizedTransaction.objects.filter(transaction_id=transaction_id).all().delete()
					else:
						priceInModelCurrency = 0	
						socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()
						paymentErroraObj  									= 	PaymentGatewayErrors()
						paymentErroraObj.user_id 								=   lastUserId
						if socialAccountFeed.social_account	== 'private_feed':
							new_username 									= 	request.POST.get("email")
							new_username 									= 	new_username.split("@")[0]
							paymentErroraObj.username 						= 	new_username
						else:
							paymentErroraObj.username 						= 	request.POST.get("username",'')
							
						paymentErroraObj.email 								= 	request.POST.get("email",'')
						paymentErroraObj.sub_name 							= 	request.POST.get("sub_name",'')
						paymentErroraObj.post_code 							= 	request.POST.get("post_code",'')
						paymentErroraObj.amount 								= 	request.POST.get("amount",'')
						paymentErroraObj.price_in_model_currency 				= 	priceInModelCurrency
						paymentErroraObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
						paymentErroraObj.plan_type_id 						= 	request.POST.get("plan_type",'')
						paymentErroraObj.model_user_id 						= 	request.POST.get("model_id",'')
						paymentErroraObj.subscription_desc 					= 	""
						paymentErroraObj.expiry_date 							= 	None
						paymentErroraObj.plan_status 							= 	"active"
						paymentErroraObj.plan_validity						=	planInfo.offer_period_type
						paymentErroraObj.transaction_id						=	""
						paymentErroraObj.transaction_payment_id				=	""
						
						
						paymentErroraObj.user_subscription_plan_description				=	planInfo.description
						paymentErroraObj.plan_type				=	planInfo.plan_type
						paymentErroraObj.offer_period_time		=	planInfo.offer_period_time
						paymentErroraObj.offer_period_type		=	planInfo.offer_period_type
						paymentErroraObj.is_discount_enabled		=	planInfo.is_discount_enabled	
						paymentErroraObj.discount					=	planInfo.discount		
						paymentErroraObj.from_discount_date		=	planInfo.from_discount_date		
						paymentErroraObj.to_discount_date			=	planInfo.to_discount_date		
						paymentErroraObj.is_permanent_discount	=	planInfo.is_permanent_discount		
						paymentErroraObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
						paymentErroraObj.planprice				=	planInfo.price		
						paymentErroraObj.discounted_price			=	planInfo.discounted_price
						paymentErroraObj.response				=	FinalizedTransactionInfo.errors
						paymentErroraObj.transaction_type		=	"subscription"
						
						paymentErroraObj.save()

						content = {
							"success": False,
							"data":[],
							"msg":"Your payment has been failed. Please try again."
						}
						return Response(content)
				else:
					priceInModelCurrency = 0	
					socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()
					paymentErroraObj  									= 	PaymentGatewayErrors()
					paymentErroraObj.user_id 								=   lastUserId
					if socialAccountFeed.social_account	== 'private_feed':
						new_username 									= 	request.POST.get("email")
						new_username 									= 	new_username.split("@")[0]
						paymentErroraObj.username 						= 	new_username
					else:
						paymentErroraObj.username 						= 	request.POST.get("username",'')
						
					paymentErroraObj.email 								= 	request.POST.get("email",'')
					paymentErroraObj.sub_name 							= 	request.POST.get("sub_name",'')
					paymentErroraObj.post_code 							= 	request.POST.get("post_code",'')
					paymentErroraObj.amount 								= 	request.POST.get("amount",'')
					paymentErroraObj.price_in_model_currency 				= 	priceInModelCurrency
					paymentErroraObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
					paymentErroraObj.plan_type_id 						= 	request.POST.get("plan_type",'')
					paymentErroraObj.model_user_id 						= 	request.POST.get("model_id",'')
					paymentErroraObj.subscription_desc 					= 	""
					paymentErroraObj.expiry_date 							= 	None
					paymentErroraObj.plan_status 							= 	"active"
					paymentErroraObj.plan_validity						=	planInfo.offer_period_type
					paymentErroraObj.transaction_id						=	""
					paymentErroraObj.transaction_payment_id				=	""
					
					
					paymentErroraObj.user_subscription_plan_description				=	planInfo.description
					paymentErroraObj.plan_type				=	planInfo.plan_type
					paymentErroraObj.offer_period_time		=	planInfo.offer_period_time
					paymentErroraObj.offer_period_type		=	planInfo.offer_period_type
					paymentErroraObj.is_discount_enabled		=	planInfo.is_discount_enabled	
					paymentErroraObj.discount					=	planInfo.discount		
					paymentErroraObj.from_discount_date		=	planInfo.from_discount_date		
					paymentErroraObj.to_discount_date			=	planInfo.to_discount_date		
					paymentErroraObj.is_permanent_discount	=	planInfo.is_permanent_discount		
					paymentErroraObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
					paymentErroraObj.planprice				=	planInfo.price		
					paymentErroraObj.discounted_price			=	planInfo.discounted_price
					paymentErroraObj.response				=	"Transaction Not Found."
					paymentErroraObj.transaction_type		=	"subscription"
					
					paymentErroraObj.save()

					content = {
						"success": False,
						"data":[],
						"msg":"Your payment has been failed. Please try again."
					}
					return Response(content)
				
				
				
				
				priceInModelCurrency = 0
				
				if(planInfo.plan_type == "recurring"):
					if planInfo.offer_period_type == 'week':
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*7))
					elif planInfo.offer_period_type == 'month':
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*30))
					else:
						expiry_date					=	today+datetime.timedelta(days=(int(planInfo.offer_period_time)*365.25))
				else:
					expiry_date	=	None

				socialAccountFeed						=	ModelSubscriptions.objects.filter(id=request.POST.get("subscription_type")).first()

				userSubPlanObj  									= 	UserSubscriptionPlan()
				userSubPlanObj.user_id 								=   user_id
				if socialAccountFeed.social_account	== 'private_feed':
					new_username 									= 	request.POST.get("email")
					new_username 									= 	new_username.split("@")[0]
					userSubPlanObj.username 						= 	new_username
				else:
					userSubPlanObj.username 						= 	request.POST.get("username",'')
					
				userSubPlanObj.email 								= 	request.POST.get("email",'')
				userSubPlanObj.sub_name 							= 	request.POST.get("sub_name",'')
				userSubPlanObj.post_code 							= 	request.POST.get("post_code",'')
				userSubPlanObj.amount 								= 	request.POST.get("amount",'')
				userSubPlanObj.price_in_model_currency 				= 	priceInModelCurrency
				userSubPlanObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
				userSubPlanObj.plan_type_id 						= 	request.POST.get("plan_type",'')
				userSubPlanObj.model_user_id 						= 	request.POST.get("model_id",'')
				userSubPlanObj.subscription_desc 					= 	""
				userSubPlanObj.expiry_date 							= 	expiry_date
				userSubPlanObj.plan_status 							= 	"active"
				userSubPlanObj.plan_validity						=	planInfo.offer_period_type
				userSubPlanObj.transaction_id						=	transaction_id
				userSubPlanObj.transaction_payment_id				=	transaction_payment_id
				
				
				userSubPlanObj.user_subscription_plan_description				=	planInfo.description
				userSubPlanObj.plan_type				=	planInfo.plan_type
				userSubPlanObj.offer_period_time		=	planInfo.offer_period_time
				userSubPlanObj.offer_period_type		=	planInfo.offer_period_type
				userSubPlanObj.is_discount_enabled		=	planInfo.is_discount_enabled	
				userSubPlanObj.discount					=	planInfo.discount		
				userSubPlanObj.from_discount_date		=	planInfo.from_discount_date		
				userSubPlanObj.to_discount_date			=	planInfo.to_discount_date		
				userSubPlanObj.is_permanent_discount	=	planInfo.is_permanent_discount		
				userSubPlanObj.is_apply_to_rebills		=	planInfo.is_apply_to_rebills		
				userSubPlanObj.planprice				=	planInfo.price		
				userSubPlanObj.discounted_price			=	planInfo.discounted_price		
				userSubPlanObj.offer_name				=	planInfo.offer_name		
				userSubPlanObj.offer_description		=	planInfo.description		
				userSubPlanObj.save()
				
				
				
				transactionObj										=	TransactionHistory()
				transactionObj.user_id								=	user_id
				transactionObj.model_id								=	request.POST.get("model_id",'')
				transactionObj.amount								=	userSubPlanObj.amount
				transactionObj.expiry_date							=	expiry_date
				transactionObj.price_in_model_currency				=	priceInModelCurrency
				transactionObj.transaction_date						=	datetime.date.today()
				transactionObj.model_subscription_id				=	request.POST.get("subscription_type",'')
				transactionObj.plan_id								=	request.POST.get("plan_type",'')
				transactionObj.transaction_type						= 	'subscription'
				transactionObj.payment_type							= 	'joins'
				transactionObj.transaction_id						=	transaction_id
				transactionObj.status								=	'success'
				transactionObj.currency								=	modelDetails.default_currency
				transactionObj.user_subscription_id					=	userSubPlanObj.id
				
				web_commission 		= settings.SITEWEBSITECOMMISSION
				SettingDetails = Setting.objects.filter(key="Site.websiteCommission").first()
				if SettingDetails:
					web_commission	=	SettingDetails.value
					
				if(decimal.Decimal(web_commission) > decimal.Decimal(0)):
					t_commission	=	round((decimal.Decimal(web_commission)/100)*decimal.Decimal(transactionObj.amount),2)
				else:
					t_commission			=	0
					
				transactionObj.commission	=	t_commission
				transactionObj.save()
				
				arrayData						=	{}
				arrayData['socialAccount']		=	planInfo.model_subscription.social_account
				arrayData['currency']			=	modelDetails.default_currency
				arrayData['price']				=	userSubPlanObj.amount
				arrayData['model_subscription_username']				=	planInfo.model_subscription.username
				arrayData['model_subscription_username']				=	planInfo.model_subscription.username
				arrayData['subscriber_subscription_username']				=	userSubPlanObj.username
				arrayData['subscriber_subscription_username']				=	userSubPlanObj.username
				if planInfo.offer_name:
					arrayData['offer_name']								=	planInfo.offer_name
				else:
					arrayData['offer_name']								=		""
				commonMail(request,"PLAN_PURCHASE",userSubPlanObj.model_user_id,userSubPlanObj.user_id,arrayData)
				
				# userSubscriptionPlanDetails 					= 	UserSubscriptionPlan.objects.filter(id=userSubPlanObj.id).first()
				# userSubscriptionPlanDetails.transaction_id		=	transactionObj.transaction_id
				# userSubscriptionPlanDetails.save()
				
				

			
			
				user		=   User.objects.filter(id=lastUserId).filter(is_deleted=0).first()
				userDetail	=	{
							"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status,"is_private_feed":user.is_private_feed
						}
				
				sub_data						=	{}
				sub_data["transaction_id"]		=	transactionObj.transaction_id
				sub_data["amount"]				=	userSubPlanObj.amount
				
				content = {
					"success": True,
					"result":[sub_data],
					"data":userDetail,
					"token":jwt_encode_handler(jwt_payload_handler(user)),
					"msg":_("Plan_subscribed_successfully")
				}
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
		return Response(content)


class SubscribeNewsletter(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")
			else:
				if NewsletterSubscriber.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	_("This_email_is_already_exists")
			
		if not validationErrors:
			email 			=	request.data.get("email", "")
			Obj				=	NewsletterSubscriber()
			Obj.email		=	email
			Obj.save()
			
			
			website_url		=	settings.FRONT_SITE_URL
			unsubscribelink			=  	settings.FRONT_SITE_URL+'user/unsubscribe-newletter?subscriber_email='+email
			emailaction				=	EmailAction.objects.filter(action="send_newsletter").first()
			emailTemplates			=	EmailTemplates.objects.filter(action = 'send_newsletter').first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			rep_Array=[email,website_url,unsubscribelink]
			massage_body  = emailTemplates.body
			# website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			x = range(len(constant))
			for i in x:
				massage_body=re.sub(constant[i], rep_Array[i], massage_body)
			massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)

			htmly     = get_template('common/email.html')
			plaintext = get_template('common/email.txt')

			html_content = htmly.render(context		=	{
				"body":massage_body,
				"website_url":website_url,
				"site_title":site_title
			})
			sendEmail(request,subject,html_content,email)
			
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Your_email_has_been_subscribed_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

class PrivateFeed(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		#print(user_language)
		validationErrors	=	{}
		if request.POST.get("title") == None or request.POST.get("title") == "":
			validationErrors["title"]	=	_("The_title_field_is_required")
		
		if request.POST.get("description") == None or request.POST.get("description") == "":
			validationErrors["description"]	=	_("The_description_field_is_required")

		if len(request.FILES) == 0:
			validationErrors["image"]	=	_("The_image_field_is_required")
		elif len(request.FILES) > 0:
			file = request.FILES["image"].name
			extension = file.split(".")[-1].lower()
			if not extension in PRIVATE_FEED_VALID_IMAGE_EXTENSIONS:
				validationErrors["image"]	=	_("The_image_is_not_a_valid_image_Please_upload_a_valid_image_Valid_extensions_are_jpg,jpeg,png,gif,mp4,webm,avi,mpeg,mov,3gp")
			
		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year
				
			if request.FILES.get("image"):
				image = request.FILES.get("image")
				filename = image.name.split(".")[0].lower().replace(" ","-")
				extension = image.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				attachment = str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(image, "private_feed_images/"+attachment)


			if extension in VALID_IMAGE_EXTENSIONS:
				uploaded_file_type	=	"photo"
				is_converted		=	1
			else:
				uploaded_file_type	=	"video"
				is_converted		=	0
				
			if request.POST.get("schedule_date") == None or request.POST.get("schedule_date") == "" or request.data.get('schedule_date',"") == "null":
				status		=	"draft"
			else:
				status		=	"schedule"

			Obj					=	PrivateFeedModel()
			Obj.title			=	request.data.get('title')
			Obj.description		=	request.data.get('description')
			if request.data.get('schedule_date',"") == "null":
				Obj.schedule_date	=	""
			else :
				Obj.schedule_date	=	request.data.get('schedule_date',"")

			Obj.image				=	str(currentMonth)+str(currentYear)+"/"+newfilename
			Obj.status				=	status
			Obj.uploaded_file_type	=	uploaded_file_type
			Obj.is_converted		=	is_converted
			Obj.user_id				=	request.user.id
			Obj.save()

			if extension in VALID_IMAGE_EXTENSIONS:
				content = {
					"success": True,
					"data":[],
					"msg":_("Private feed has been added successfully.")
				}
				return Response(content)
			else:
				content = {
					"success": True,
					"data":[],
					"msg":_("Your private feed video is under process. You can see your post after video is successfully processed.")
				}
				return Response(content)
			
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		DB = PrivateFeedModel.objects.filter(user_id=request.user.id).filter(is_converted=1)
		DBCount = PrivateFeedModel.objects.filter(user_id=request.user.id).filter(is_converted=1)
		if request.GET.get('search_string'):
			search_string = request.GET.get('search_string')
			DB = DB.filter(Q(title__icontains=search_string) | Q(description__icontains=search_string))
			DBCount = DBCount.filter(Q(title__icontains=search_string) | Q(description__icontains=search_string))


		if request.GET.get('status'):
			search_string = request.GET.get('status').strip()
			DB = DB.filter(status=search_string)
			DBCount = DBCount.filter(status=search_string)

		recordPerPge	=	10
		order_by	=	request.GET.get('order_by',"created_at")
		direction	=	request.GET.get('direction',"DESC")
		if direction == "DESC":
			DB = DB.order_by("-"+order_by)
		else:
			DB = DB.order_by(order_by)

		PrivateFeedsTotal	=	DBCount.count()
		page = request.GET.get('page', 1)
		paginator = Paginator(DB, recordPerPge)
		try:
			results = paginator.page(page)
		except PageNotAnInteger:
			results = paginator.page(1)
		except EmptyPage:
			results = paginator.page(paginator.num_pages)

		PrivateFeeds = list(results)  # important: convert the QuerySet to a list object
		
		private_feeds	=	[]
		if PrivateFeeds:
			for PrivateFeed1 in PrivateFeeds:
				PrivateFeed								=	{}
				PrivateFeed["id"]						=	PrivateFeed1.id
				PrivateFeed["title"]					=	PrivateFeed1.title
				PrivateFeed["image"]					=	settings.PRIVATE_FEED_IMAGE_URL + PrivateFeed1.image
				PrivateFeed["uploaded_file_type"]		=	PrivateFeed1.uploaded_file_type
				if(PrivateFeed1.uploaded_file_type == "video"):
					PrivateFeed["mp4video_path"]			=	settings.PRIVATE_FEED_IMAGE_URL + PrivateFeed1.image.replace("jpg","mp4")
					PrivateFeed["webmvideo_path"]			=	settings.PRIVATE_FEED_IMAGE_URL + PrivateFeed1.image.replace("jpg","webm")
				else:
					PrivateFeed["mp4video_path"]			=	""
					PrivateFeed["webmvideo_path"]			=	""
					
				PrivateFeed["description"]				=	PrivateFeed1.description
				PrivateFeed["schedule_date"]			=	PrivateFeed1.schedule_date
				PrivateFeed["status"]					=	PrivateFeed1.status
				PrivateFeed["created_at"]				=	PrivateFeed1.created_at
				private_feeds.append(PrivateFeed)
				
		content = {
			"success": True,
			"data":private_feeds,
			"msg":"",
			"PrivateFeedsTotal":PrivateFeedsTotal,
			"recordPerPge":recordPerPge,
		}
		return Response(content)
			


	def put(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		#print(user_language)
		validationErrors	=	{}
		if request.POST.get("private_feed_id") == None or request.POST.get("private_feed_id") == "":
			validationErrors["private_feed_id"]	=	_("The_private_feed_id_field_is_required")

		if request.POST.get("title") == None or request.POST.get("title") == "":
			validationErrors["title"]	=	_("The_title_field_is_required")
		
		if request.POST.get("description") == None or request.POST.get("description") == "":
			validationErrors["description"]	=	_("The_description_field_is_required")
		extension	=	""
		if len(request.FILES) > 0:
			file = request.FILES["image"].name
			extension = file.split(".")[-1].lower()
			if not extension in PRIVATE_FEED_VALID_IMAGE_EXTENSIONS:
				validationErrors["image"]	=	_("The_image_is_not_a_valid_image_Please_upload_a_valid_image_Valid_extensions_are_jpg,jpeg,png,gif,mp4,webm,avi,mpeg,mov,3gp")
			
		if not validationErrors:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.POST.get("private_feed_id")).filter(user_id=request.user.id).first()
			if PrivateFeedDetail:
				newfilename	=	""
				if len(request.FILES) > 0:
					currentMonth = datetime.datetime.now().month
					currentYear = datetime.datetime.now().year
						
					if request.FILES.get("image"):
						image = request.FILES.get("image")
						filename = image.name.split(".")[0].lower().replace(" ","-")
						extension = image.name.split(".")[-1].lower()
						newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
						attachment = str(currentMonth)+str(currentYear)+"/"+newfilename
						Upload.upload_image_on_gcp(image, "private_feed_images/"+attachment)

				if request.POST.get("schedule_date") == None or request.POST.get("schedule_date") == "" or request.data.get('schedule_date',"") == "null":
					status		=	"draft"
				else:
					status		=	"schedule"
					
				if extension in VALID_IMAGE_EXTENSIONS:
					uploaded_file_type	=	"photo"
					is_converted		=	1
				else:
					uploaded_file_type	=	"video"
					is_converted		=	0

				Obj					=	PrivateFeedDetail
				Obj.title			=	request.data.get('title')
				Obj.description		=	request.data.get('description')
				if request.data.get('schedule_date',"") == "null":
					Obj.schedule_date	=	""
				else :
					Obj.schedule_date	=	request.data.get('schedule_date',"")

				if newfilename != "":
					Obj.image			=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				if(extension != ""):
					Obj.uploaded_file_type	=	uploaded_file_type
					Obj.is_converted		=	is_converted
				
				Obj.status			=	status
				Obj.save()

				if extension == "" or extension in VALID_IMAGE_EXTENSIONS:
					content = {
						"success": True,
						"data":[],
						"msg":_("Private feed has been updated successfully.")
					}
					return Response(content)
				else:
					content = {
						"success": True,
						"data":[],
						"msg":_("Your private feed video is under process. You can see your post after video is successfully processed.")
					}
					return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Private_feed_id_does_not_exists")
				}
				return Response(content)	
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			

	def delete(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET.get("private_feed_id") == None or request.GET.get("private_feed_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.GET.get("private_feed_id")).filter(user_id=request.user.id).first()
			if PrivateFeedDetail:
				PrivateFeedModel.objects.filter(id=request.GET.get("private_feed_id")).filter(user_id=request.user.id).delete()
				content = {
					"success": True,
					"data":[],
					"msg":_("Private_feed_removed_successfully")
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Private_feed_id_does_not_exists")
				}	

		return Response(content)

class PublishPrivateFeed(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		#print(user_language)
		validationErrors	=	{}
		if request.GET.get("private_feed_id") == None or request.GET.get("private_feed_id") == "":
			validationErrors["private_feed_id"]	=	_("The_private_feed_id_is_required")

		if not validationErrors:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.GET.get("private_feed_id")).filter(user_id=request.user.id).filter(status="draft").first()

			if PrivateFeedDetail:
				Obj					=	PrivateFeedDetail
				Obj.status			=	"publish"
				Obj.save()

				content = {
					"success": True,
					"data":[],
					"msg":_("Your_profile_has_been_published_successfully")
				}
				return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Private_feed_id_does_not_exists")
				}
				return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

class modelPrivateFeed(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		if request.GET.get("model_id") == None or request.GET.get("model_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			if request.GET.get("file_type") == "photo":
				DB 			= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish').filter(uploaded_file_type='photo')
				DBCount  	= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish').filter(uploaded_file_type='photo')
			if request.GET.get("file_type") == "video":
				DB 			= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish').filter(uploaded_file_type='video')
				DBCount  	= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish').filter(uploaded_file_type='video')
			if request.GET.get("file_type") == "all":
				DB 			= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish')
				DBCount  	= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish')
			
			userDetail	= User.objects.filter(id=request.GET.get("model_id")).filter(is_deleted=0).first()
			recordPerPge	=	10
			if userDetail.is_private_feed == 1:
				if request.GET.get('search'):
					search_string = request.GET.get('search').strip()
					DB = DB.filter(Q(title__icontains=search_string) | Q(description__icontains=search_string))
					DBCount = DBCount.filter(Q(title__icontains=search_string) | Q(description__icontains=search_string))
				
				order_by	=	request.GET.get('order_by',"created_at")
				direction	=	request.GET.get('direction',"DESC")
				if direction == "DESC":
					DB = DB.order_by("-"+order_by)
				else:
					DB = DB.order_by(order_by)
					
				PrivateFeedsTotal	=	DBCount.count()
				page = request.GET.get('page', 1)
				paginator = Paginator(DB, recordPerPge)
				try:
					results = paginator.page(page)
				except PageNotAnInteger:
					results = paginator.page(1)
				except EmptyPage:
					results = paginator.page(paginator.num_pages)

				PrivateFeeds = list(results)  # important: convert the QuerySet to a list object
				
				subscripDetail	=   UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(model_user_id=request.GET.get("model_id")).filter(model_subscription__social_account='private_feed').filter(is_subscription_cancelled=0).first()
				if subscripDetail and subscripDetail.plan_type == "recurring":
					today_date = str(datetime.datetime.today().date())+" 00:00:00"
					expiry_time = str(subscripDetail.expiry_date)+" 23:59:59"
					if expiry_time > today_date:
						is_private_feed_subscribed = 1
					else:
						is_private_feed_subscribed = 0
						
				elif subscripDetail and subscripDetail.plan_type == "one_time":
					is_private_feed_subscribed = 1
				else:
					is_private_feed_subscribed = 0
				
				
				ModelImage = ModelImages.objects.filter(user_id=request.GET.get("model_id")).first()
				if ModelImage:
					profile_image					=	settings.MODEL_IMAGE_URL+ModelImage.image_url
				else:
					profile_image					=	settings.MEDIA_URL+"dummy.jpg"
					
				private_feeds	=	[]
				if PrivateFeeds:
					for PrivateFeed1 in PrivateFeeds:
						PrivateFeed								=	{}
						PrivateFeed["title"]					=	PrivateFeed1.title
						
						
						PrivateFeed["uploaded_file_type"]		=	PrivateFeed1.uploaded_file_type
						if(PrivateFeed1.uploaded_file_type == "video" and request.user.id != "" and is_private_feed_subscribed == 1):
							PrivateFeed["mp4video_path"]			=	settings.PRIVATE_FEED_IMAGE_URL+PrivateFeed1.image.replace("jpg","mp4")
							PrivateFeed["webmvideo_path"]			=	settings.PRIVATE_FEED_IMAGE_URL+PrivateFeed1.image.replace("jpg","webm")
						else:
							PrivateFeed["mp4video_path"]			=	""
							PrivateFeed["webmvideo_path"]			=	""
						
						if(request.user.id != "" and is_private_feed_subscribed == 1):
							PrivateFeed["image"]					=	settings.PRIVATE_FEED_IMAGE_URL+PrivateFeed1.image
							PrivateFeed["description"]				=	PrivateFeed1.description
						else:
							PrivateFeed["image"]					=	profile_image
							PrivateFeed["description"]				=	"Subscribe to view this content."
						
						PrivateFeed["id"]						=	PrivateFeed1.id
						PrivateFeed["created_at"]				=	PrivateFeed1.created_at
						private_feeds.append(PrivateFeed)
						
				total_photos 	= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish').filter(uploaded_file_type='photo').count()
				total_videos 	= PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(uploaded_file_type='video').filter(status='publish').count()
				content = {
					"success": True,
					"data":private_feeds,
					"total_photos":total_photos,
					"total_videos":total_videos,
					"total_feed_count":PrivateFeedsTotal,
					"msg":"",
					"is_private_feed_subscribed":is_private_feed_subscribed,
					"PrivateFeedsTotal":PrivateFeedsTotal,
					"recordPerPge":recordPerPge,
				}
			else:
				content = {
					"success": True,
					"data":[],
					"msg":"",
					"is_private_feed_subscribed":1,
					"PrivateFeedsTotal":0,
					"total_photos":0,
					"total_videos":0,
					"total_feed_count":0,
					"recordPerPge":recordPerPge,
				}
			
		return Response(content)
			
class getSubscriptionList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		subList	=   UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).all()
		
		if subList:
			allSubList	=	[]
			for sub in subList:
				#return HttpResponse(sub.model_subscription_id.social_account)
				sub_data								=	{}
				planDetail = ModelSubscriptions.objects.filter(id=sub.model_subscription_id).filter(is_deleted=0).first()
				sub_data["plan_type"]					=	planDetail.social_account
				sub_data["total_spend"]					=	sub.amount
				sub_data["user_name"]					=	sub.sub_name
				sub_data["join_date"]					=	sub.created_at
				sub_data["expiry_date"]					=	'18/10/2020'
				sub_data["status"]						=	'New'
				allSubList.append(sub_data)
			content = {
				"success": True,
				"data":allSubList,
				"msg":_("Subscribers_listed_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_Subscriber_found")
			}
			return Response(content)

class ListReportReason(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		activeReportReason = DropDownManager.objects.filter(dropdown_type="report-reason").filter(is_active=1).all().values("id")
		reasons = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=activeReportReason).filter(language_code=user_language).all().values('name',"dropdown_manger_id")  # or simply .values() to get all fields
		reasons = list(reasons)  # important: convert the QuerySet to a list object
		content = {
			"success": True,
			"data":reasons,
			"msg":""
		}
		return Response(content)

class ReportReason(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("model_user_id") == None or request.POST.get("model_user_id") == "":
			validationErrors["model_user_id"]	=	_("The_model_id_field_is_required")
		
		if request.POST.get("reason_description") == None or request.POST.get("reason_description") == "":
			validationErrors["reason_description"]	=	_("The_report_reason_field_is_required")

		if request.POST.get("dropdown_manager_id") == None or request.POST.get("dropdown_manager_id") == "":
			validationErrors["dropdown_manager_id"]	=	_("The_dropdownmanager_id_field_is_required")
			
		if not validationErrors:
			Obj							=	ReportReasonModel()
			Obj.model_user_id			=	request.POST.get('model_user_id')
			Obj.reason_description		=	request.POST.get('reason_description')
			Obj.dropdown_manager_id		=	request.POST.get("dropdown_manager_id")
			Obj.user_id					=	request.user.id
			Obj.save()

			content = {
				"success": True,
				"data":[],
				"msg":_("Model_successfully_reported")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)



# class getUserSubscriptionPlanList(generics.ListAPIView):
	# permission_classes = (permissions.IsAuthenticated,)
	# def get(self, request, *args, **kwargs):
		# if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			# user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		# else :
			# user_language = "en"
		# translation.activate(user_language)
		
		# user_role = request.user.user_role_id
		# if user_role == 3:
			# DB			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='active').filter(~Q(plan_type__model_status=2))
			# if request.GET.get('username') and request.GET.get('username') !='':
				# username = request.GET.get('username').strip()
				# DB = DB.filter(Q(username__icontains=username) | Q(email__icontains=username) | Q(user__username__icontains=username))

		# else:
			# DB			=	UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='active').filter(~Q(plan_type__model_status=2))
			# if request.GET.get('username') and request.GET.get('username') !='':
				# username = request.GET.get('username').strip()
				# DB = DB.filter(model_user__model_name=username)

		# status  = ''
		# allReportList			 =	[]
		# if request.GET.get('status') and request.GET.get('status') !='':
			# status = request.GET.get('status').strip()
			# if status == 'new':
				# #return HttpResponse(str(datetime.date.today())+" 23:59:59")
				# DB = DB.filter(plan_status = "active")
			# elif status == "report":
				# reportedAccountCount	 =	ReportReasonModel.objects.filter(model_user_id=request.user.id).all().count()
				# reportedAccountDetail	 =	ReportReasonModel.objects.filter(model_user_id=request.user.id).all()	
				# if reportedAccountDetail:
					# for report in reportedAccountDetail:
						# sub_report						=		{}
						# sub_report["subscriber_name"]	=		report.user.username
						# sub_report["subscriber_first_name_last_name"]	=		report.user.first_name+report.user.last_name
						# sub_report["report_reason"]		=		report.reason_description
						# sub_report["report_date"]		=		report.created_at
						# allReportList.append(sub_report)
					
			# else :
				# DB = DB.filter(plan_status = "expire")

		# if request.GET.get('subscription_type'):
			# subscription_type = request.GET.get('subscription_type').strip()
			# if subscription_type == 'instagram':
				# instaUsers = ModelSubscriptions.objects.filter(social_account='instagram').filter(is_deleted=0).filter(is_enabled=1).values("id")
				# DB = DB.filter(Q(model_subscription_id__in=instaUsers))
			# if subscription_type == 'snapchat':
				# snapUsers = ModelSubscriptions.objects.filter(social_account='snapchat').filter(is_deleted=0).filter(is_enabled=1).values("id")		
				# DB = DB.filter(Q(model_subscription_id__in=snapUsers))
			# if subscription_type == 'whatsapp':
				# whatsappUsers = ModelSubscriptions.objects.filter(social_account='whatsapp').filter(is_deleted=0).filter(is_enabled=1).values("id")
				# DB = DB.filter(Q(model_subscription_id__in=whatsappUsers))
			# if subscription_type == 'private_feed':
				# privateFeedUsers = ModelSubscriptions.objects.filter(social_account='private_feed').filter(is_deleted=0).filter(is_enabled=1).values("id")
				# DB = DB.filter(Q(model_subscription_id__in=privateFeedUsers))
			# if subscription_type == 'tips':
				# tipsUsers = ModelSubscriptions.objects.filter(social_account='tips').filter(is_deleted=0).filter(is_enabled=1).values("id")
				# DB = DB.filter(Q(model_subscription_id__in=tipsUsers))
			
		# order_by	=	request.GET.get('order_by',"created_at")
		# direction	=	request.GET.get('direction',"DESC")	
		# countTotel  = DB.count()
		
		# if direction == "DESC":
			# DB = DB.order_by("-"+order_by).all()
		# else:
			# DB = DB.order_by(order_by).all()	
		# recordPerPge	=	settings.READINGRECORDPERPAGE
		# #recordPerPge	=	15
		# page = request.GET.get('page', 1)
		# paginator = Paginator(DB, recordPerPge)
		# try:
			# results = paginator.page(page)
		# except PageNotAnInteger:
			# results = paginator.page(1)
		# except EmptyPage:
			# results = paginator.page(paginator.num_pages)
		# max_index = len(paginator.page_range)
		
		# allSubList	=	[]
		
		# if results:	
			# for sub in results:
				# if user_role == 3:
					# totalActiveCount = 	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='active').filter(~Q(plan_type__model_status=2)).count()
					# totalExpireCount = 	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='expire').filter(~Q(plan_type__model_status=2)).count()
					# totalCount		 =	totalActiveCount + totalExpireCount
					# amount 		= sub.price_in_model_currency
					# currency 	= request.user.default_currency
				# else:
					# totalActiveCount = 	UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='active').filter(~Q(plan_type__model_status=2)).count()
					# totalExpireCount = 	UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(user__is_deleted=0).filter(plan_type__is_deleted=0).filter(plan_status='expire').filter(~Q(plan_type__model_status=2)).count()
					# totalCount		 =	totalActiveCount + totalExpireCount
					# amount 		= sub.amount
					# currency 	= sub.plan_type.currency
				# ModelImage = ModelImages.objects.filter(user_id=sub.model_user_id).all()

				# sub_data								=	{}
				# sub_data["plan_id"]						=	sub.plan_type.id
				# sub_data["plan_type"]					=	sub.plan_type.plan_type
				# sub_data["offer_period_time"]			=	sub.plan_type.offer_period_time
				# sub_data["offer_period_type"]			=	sub.plan_type.offer_period_type
				# sub_data["social_account"]				=	sub.model_subscription.social_account
				# sub_data["total_spend"]					=	amount
				# if user_role == 3:
					# sub_data["user_name"]					=	sub.username
					# sub_data["email"]						=	sub.email
				# else:
					# sub_data["user_name"]					=	sub.model_user.username
					# sub_data["email"]						=	sub.model_user.email
				# sub_data["join_date"]					=	sub.created_at
				# sub_data["currency"]					=	currency
				# sub_data["expiry_date"]					=   sub.expiry_date
				# ExpiryDate 								= 	sub.expiry_date
				# sub_data["model_status"]				=   sub.plan_type.model_status
				# if sub.plan_status == 'expire':
					# sub_data["status"]						=	'Expire'
				# else:
					# sub_data["status"]						=	'New'

				# sub_data["model_name"]						=	sub.model_user.model_name
				# if ModelImage:
					# sub_data["profile_image"]				=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage[0].image_url
				# else:
					# sub_data["profile_image"]				=	settings.MEDIA_SITE_URL+"uploads/dummy.jpeg"
				
				# if sub.model_subscription.social_account	==	'snapchat':
					# sub_data["social_account_link"]			=	settings.SOCIALSNAPCHAT_LINK
				# if sub.model_subscription.social_account	==	'private_feed':
					# sub_data["social_account_link"]			=	settings.SOCIALPRIVATE_FEED_LINK
				# if sub.model_subscription.social_account	==	'whatsapp':
					# sub_data["social_account_link"]			=	settings.SOCIALWHATSAPP_LINK
				# if sub.model_subscription.social_account	==	'instagram':
					# sub_data["social_account_link"]			=	settings.SOCIALINSTAGRAM_LINK
				# allSubList.append(sub_data)
		# #return HttpResponse(allSubList)
		
		# if allSubList :
			# if allReportList:
				# content = {
						# "success": True,
						# "data":allSubList,
						# "report_data":allReportList,
						# "total_plan_count":totalCount,
						# "active_plan_count":totalActiveCount,
						# "report_count":reportedAccountCount,
						# "expire_plan_count":totalExpireCount,
						# "recordPerPge":recordPerPge,
						# "maxIndex":max_index,
						# "total_record":countTotel,
						# "msg":_("Subscribers_listed_successfully")
					# }
			# else:
				# content = {
						# "success": True,
						# "data":allSubList,
						# "report_data":[],
						# "report_count":0,
						# "total_plan_count":totalCount,
						# "active_plan_count":totalActiveCount,
						# "expire_plan_count":totalExpireCount,
						# "recordPerPge":recordPerPge,
						# "maxIndex":max_index,
						# "total_record":countTotel,
						# "msg":_("Subscribers_listed_successfully")
					# }
				
		# else:
			# content = {
				# "success": True,
				# "data":[],
				# "msg":_("No_Subscriber_found")
			# }
			
		# return Response(content)
		
class getUserSubscriptionPlanList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		plan_type	=	request.GET.get("plan_type","active")
		
		if(plan_type == "active"):
			subscribedModels = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(plan_status='active').filter(is_subscription_cancelled=0).values("model_user_id")
		else:
			subscribedModels = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(~Q(plan_status="active") | Q(is_subscription_cancelled=1)).values("model_user_id")
		
		DB = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(Q(id__in=subscribedModels))
		if request.GET.get('username'):
			DB 			= DB.filter(Q(model_name__icontains=request.GET.get('username')))
			
		ModelsProfiles = DB.all()
		ModelsProfiles = list(ModelsProfiles) 
		profiles	=	[]
		if ModelsProfiles:
			for Profile in ModelsProfiles:
				profile					=	{}
				profile["model_name"]	=	Profile.model_name
				profile["slug"]			=	Profile.slug
				profile["bio"]			=	Profile.bio
				profile["first_name"]					=	Profile.first_name
				profile["last_name"]					=	Profile.last_name
				profile["discount_percentage"]			=	Profile.highest_discount
				profile["amazon_wishlist_link"]			=	Profile.amazon_wishlist_link
				profile["private_snapchat_link"]		=	Profile.private_snapchat_link
				profile["public_instagram_link"]		=	Profile.public_instagram_link
				profile["public_snapchat_link"]			=	Profile.public_snapchat_link
				profile["twitter_link"]					=	Profile.twitter_link
				profile["youtube_link"]					=	Profile.youtube_link
				profile["user_id"]							=	Profile.id
				ModelImage = ModelImages.objects.filter(user_id=Profile.id).first()
				if ModelImage:
					profile["profile_image"]					=	settings.MODEL_IMAGE_URL+ModelImage.image_url
				else:
					profile["profile_image"]					=	settings.MEDIA_URL+"dummy.jpg"
					
					
				if(plan_type == "active"):
					planList = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(plan_status='active').filter(model_user_id=Profile.id).filter(is_subscription_cancelled=0).all()
				else:
					planList = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(~Q(plan_status="active") | Q(is_subscription_cancelled=1)).filter(model_user_id=Profile.id).all()
					
				allplanList	=	[]
				for planListDetail in planList:
					sub_data					=	{}
					sub_data["social_account"]	=	planListDetail.model_subscription.social_account
					if planListDetail.model_subscription.social_account == 'private_feed':
						modeldetail	=	User.objects.filter(id=planListDetail.model_subscription.user_id).first()
						email					=	modeldetail.email
						username				=	email.split('@')[0]
						sub_data["username"]	=	username	
					else:
						sub_data["username"]	=	planListDetail.model_subscription.username
						
					allplanList.append(sub_data)
				
				profile["planList"]		=	allplanList
				profiles.append(profile)
				
		
		activesubscribedModels = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(plan_status='active').filter(is_subscription_cancelled=0).values("model_user_id")
		
		notactivesubscribedModels = UserSubscriptionPlan.objects.filter(user_id=request.user.id).filter(~Q(plan_status="active") | Q(is_subscription_cancelled=1)).values("model_user_id")
		
		activeModelSubscriptions_count	=	User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(Q(id__in=activesubscribedModels)).count()
		expireModelSubscriptions_count	=	User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(Q(id__in=notactivesubscribedModels)).count()
		
		
		content = {
			"success": True,
			"data":profiles,
			"active_models":activeModelSubscriptions_count,
			"expired_models":expireModelSubscriptions_count,
			"msg":""
		}
		return Response(content)



class getUserTransactionList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		user_role = request.user.user_role_id
		DB = TransactionHistory.objects

		DB			=	DB.filter(user_id=request.user.id)
		if request.GET.get('registered_from'):
			DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		if request.GET.get('registered_to'):
			DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
			
		if request.GET.get('username'):
			DB 			= DB.filter(Q(model__model_name__icontains=request.GET.get('username')) | Q(model__username__icontains=request.GET.get('username')) | Q(model__email__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')))
		
		order_by	=	request.GET.get('order_by',"created_at")
		direction	=	request.GET.get('direction',"DESC")	
		countTotel  = DB.count()
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
			
		max_index = len(paginator.page_range)
		allSubList	=	[]
		if results:
			web_commission 		= settings.SITEWEBSITECOMMISSION
			SettingDetails = Setting.objects.filter(key="Site.websiteCommission").first()
			if SettingDetails:
				web_commission	=	SettingDetails.value
				
			for sub in results:
				sub_data								=	{}
				sub_data["offer_name"]					=	""
				sub_data["offer_description"]			=	""
				sub_data["social_account"]				=	""
				if sub.transaction_type=="subscription":
					sub_data["social_account"]				=	sub.model_subscription.social_account
					sub_data["offer_name"]					=	sub.user_subscription.offer_name
					sub_data["offer_description"]			=	sub.user_subscription.offer_description
				
					sub_data["model_name"]					=	sub.model.model_name
					sub_data["username"]					=	sub.model.username
					sub_data["email"]						=	sub.model.email

					if(sub.user_subscription.plan_type == "recurring"):
						if(str(sub.user_subscription.offer_period_type) == "week"):
							billed	=	"Weekly"
						if(str(sub.user_subscription.offer_period_type) == "month"):
							billed	=	"Monthly"
						if(str(sub.user_subscription.offer_period_type) == "year"):
							billed	=	"Yearly"
					else:
						billed	=	"One Time"
					
					sub_data["billed"]						=	billed
					if(sub.expiry_date == "0000-00-00" or sub.expiry_date == ""):
						sub_data["expiry_date"]			=	""
					else:
						sub_data["expiry_date"]			=	sub.expiry_date
						
					if(int(sub.is_subscription_cancelled) == int(1)):
						sub_data["status"]						=	"cancelled"
					elif(sub.user_subscription.plan_type == "one_time"):
						sub_data["status"]						=	"active"
					elif(sub.user_subscription.plan_type == "recurring"):
						today_date = str(datetime.datetime.today().date())
						if(sub.expiry_date >= today_date):
							sub_data["status"]						=	"active"
						else:
							sub_data["status"]						=	"expire"
							
				if sub.transaction_type=="tips":
					sub_data["model_name"]					=	sub.model.model_name
					sub_data["username"]					=	sub.tip_email
					sub_data["email"]						=	sub.tip_email
					sub_data["subscription_type"]		=	""
				else:
					sub_data["subscription_type"]		=	sub.model_subscription.social_account
					
				
					
				sub_data["transaction_date"]			=	sub.created_at
				sub_data["transaction_type"]			=	sub.transaction_type
				sub_data["transaction_id"]				=	sub.transaction_id
				sub_data["status"]						=	sub.status
				sub_data["id"]							=	sub.id
					
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":_("Transactions_listed_successfully")
						}
		else:
			content = {
				"success": True,
				"data":[],
				"msg":_("No_Subscriber_found")
			}	
		return Response(content)
		
class PayOutHistory(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		user_role = request.user.user_role_id
		
		DB = Payout.objects.filter(model_id=request.user.id)
		
		if request.GET.get('from'):
			DB 			= DB.filter(created_at__gte=request.GET.get('from')+" 00:00:00")
		if request.GET.get('to'):
			DB 			= DB.filter(created_at__lte=request.GET.get('to')+" 23:59:59")
		if request.GET.get('payment_method'):
			payment_method = request.GET.get('payment_method')
			DB 			= DB.filter(Q(payment_method__icontains=payment_method))
		
		
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
			
		max_index = len(paginator.page_range)
		allSubList	=	[]
		if results:
			for sub in results:
				if sub.is_paid == 1:
					status = 'Paid'
				else:
					status = 'Not Paid'
					
				sub_data								=	{}
				sub_data["payout_date"]					=	sub.created_at
				sub_data["status"]						=	status
				sub_data["billing_period_start"]		=	sub.start_date
				sub_data["billing_period_end"]			=	sub.end_date
				sub_data["gross_revenue"]				=	sub.gross_revenue
				sub_data["net_revenue"]					=	sub.net_revenue
				sub_data["payment_method"]				=	sub.payment_method
				if sub.pay_slip != "" and sub.pay_slip != "null" and sub.pay_slip != None: 
					sub_data["pay_slip"]					=	settings.PAYOUT_IMAGE_URL+sub.pay_slip
				else :
					sub_data["pay_slip"]					=	""
				allSubList.append(sub_data)
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":_("Payouts_listed_successfully")
						}
		else:
			content = {
				"success": True,
				"data":[],
				
				"msg":_("No_payouts_found")
			}	
		return Response(content)	
		
class ModelProfileImages(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		currentMonth = datetime.datetime.now().month
		currentYear = datetime.datetime.now().year

		if not validationErrors:
			images 							= request.FILES.getlist("images")
			orientations 					=   request.POST.getlist('orientations')
		
			if images:
				counter = 0
				for imge in images:
					
					myfile = imge
					filename = myfile.name.split(".")[0].lower()
					extension = myfile.name.split(".")[-1].lower()
					newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
					
					angle1 = 270
					angle2 = 90
					orientation = orientations[counter]
					model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
					if orientation == '6':
						Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
						image_path = os.path.join(settings.MODEL_IMAGE_URL)
						img = Image.open(image_path+model_image)
						img = img.rotate(angle1, expand=True)
						img.save(image_path+newfilename)
						img.close()

					elif orientation == '8':
						Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
						image_path = os.path.join(settings.MODEL_IMAGE_URL)
						img = Image.open(image_path+model_image)
						img = img.rotate(angle2, expand=True)
						img.save(image_path+newfilename)
						img.close()
					else:
						Upload.upload_image_on_gcp(myfile, "model_images/"+model_image)
					model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename

					
					counter  += 1
				imageDetail	=	{
						"images":model_image
					}
				content = {
				"success": True,
				"data": imageDetail,
				"msg":""
				}
			else:
				content = {
				"success": True,
				"data": "",
				"msg":""
			}

		return Response(content)



class ModelPaymentDetails(generics.CreateAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		model_id 	= request.user.id
		accDetails 	= AccountDetails.objects.filter(model_id=model_id).first()
		if accDetails:
			accountDetailList						=		[]
			if accDetails.payment_method == 'wire':
				sub_data							=		{}
				sub_data["bank_name"] 				= 		accDetails.bank_name
				sub_data["bank_address"] 			= 		accDetails.bank_address
				sub_data["swift_bic"] 				= 		accDetails.swift_bic
				sub_data["minimum_payout"] 			= 		accDetails.minimum_payout
				sub_data["country"] 				= 		accDetails.country
				sub_data["pay_to"] 					= 		accDetails.pay_to
				sub_data["iban"] 					= 		accDetails.iban
				sub_data["payment_method"]			=		accDetails.payment_method
				accountDetailList.append(sub_data)
				content = {
					"success": True,
					"data":accountDetailList,
					"msg":""
				}
			elif accDetails.payment_method == 'cheque':
				sub_data							=		{}
				sub_data["minimum_payout"] 			= 		accDetails.minimum_payout
				sub_data["name"] 					= 		accDetails.name
				sub_data["address"] 				= 		accDetails.address
				sub_data["contact_number"] 			= 		accDetails.contact_number
				sub_data["cheque_email"] 			= 		accDetails.cheque_email
				sub_data["payment_method"]			=		accDetails.payment_method
				accountDetailList.append(sub_data)
				content = {
					"success": True,
					"data":accountDetailList,
					"msg":""
				}

			elif accDetails.payment_method == 'paypal':
				sub_data							=		{}
				sub_data["paypal_email"] 			= 		accDetails.paypal_email
				sub_data["payment_method"]			=		accDetails.payment_method
				sub_data["minimum_payout"] 			= 		accDetails.minimum_payout
				
				accountDetailList.append(sub_data)

				content = {
					"success": True,
					"data":accountDetailList,
					"msg":""
				}
			else:
				content = {
					"success": True,
					"data":accountDetailList,
					"msg":""
				}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}
		
		return Response(content)
	
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		accountDetail	=	AccountDetails.objects.filter(model_id=request.user.id).first()

		if request.POST.get("payment_method") == None or request.POST.get("payment_method") == "":
			validationErrors["payment_method"]	=	"The payment method field is required"
		else:
			if request.POST.get("payment_method") == "wire":
				if request.POST.get("bank_name_wire") == None or request.POST.get("bank_name_wire") == "":
					validationErrors["bank_name_wire"]	=	"The bank name field is required."
				if request.POST.get("bank_address_wire") == None or request.POST.get("bank_address_wire") == "":
					validationErrors["bank_address_wire"]	=	"The bank address field is required."
				if request.POST.get("swift_code_wire") == None or request.POST.get("swift_code_wire") == "":
					validationErrors["swift_code_wire"]	=	"The swift code field is required."
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."
				if request.POST.get("pay_to") == None or request.POST.get("pay_to") == "":
					validationErrors["pay_to"]	=	"The pay to field is required."
				if request.POST.get("country") == None or request.POST.get("country") == "":
					validationErrors["country"]	=	"The country field is required."
				if request.POST.get("iban_wire") == None or request.POST.get("iban_wire") == "":
					validationErrors["iban_wire"]	=	"The iban field is required."
			if request.POST.get("payment_method") == "cheque":
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."
				if request.POST.get("name") == None or request.POST.get("name") == "":
					validationErrors["name"]	=	"The name field is required."
				if request.POST.get("cheque_email") == None or request.POST.get("cheque_email") == "":
					validationErrors["cheque_email"]	=	"The email field is required."
				if request.POST.get("address") == None or request.POST.get("address") == "":
					validationErrors["address"]	=	"The address field is required."
				if request.POST.get("contact_number") == None or request.POST.get("contact_number") == "":
					validationErrors["contact_number"]	=	"The contact number field is required."
			if request.POST.get("payment_method") == "paypal":
				if request.POST.get("paypal_email") == None or request.POST.get("paypal_email") == "":
					validationErrors["paypal_email"]	=	"The paypal email field is required."
				if request.POST.get("minimum_payout") == None or request.POST.get("minimum_payout") == "":
					validationErrors["minimum_payout"]	=	"The minimum payout field is required."

		if not validationErrors:
			if request.POST.get("payment_method")	==	"wire":
				if accountDetail:
					wireMethod							=	accountDetail
					wireMethod.payment_method			=	request.POST.get("payment_method")
					wireMethod.bank_name				=	request.POST.get("bank_name_wire")
					wireMethod.swift_bic				=	request.POST.get("swift_code_wire")
					wireMethod.bank_address				=	request.POST.get("bank_address_wire")
					wireMethod.country					=	request.POST.get("country")
					wireMethod.pay_to					=	request.POST.get("pay_to")
					wireMethod.minimum_payout			=	request.POST.get("minimum_payout")
					wireMethod.iban						=	request.POST.get("iban_wire")

					wireMethod.save()
				else:
					wireMethod							=	AccountDetails()
					wireMethod.payment_method			=	request.POST.get("payment_method")
					wireMethod.bank_name				=	request.POST.get("bank_name_wire")
					wireMethod.swift_bic				=	request.POST.get("swift_code_wire")
					wireMethod.bank_address				=	request.POST.get("bank_address_wire")
					wireMethod.country					=	request.POST.get("country")
					wireMethod.pay_to					=	request.POST.get("pay_to")
					wireMethod.minimum_payout			=	request.POST.get("minimum_payout")
					wireMethod.iban						=	request.POST.get("iban_wire")
					wireMethod.model_id					=	request.user.id

					wireMethod.save()
			if request.POST.get("payment_method")	==	"cheque":
				if accountDetail:
					chequeMethod							=	accountDetail
					chequeMethod.minimum_payout				=	request.POST.get("minimum_payout")
					chequeMethod.name						=	request.POST.get("name")
					chequeMethod.address					=	request.POST.get("address")
					chequeMethod.contact_number				=	request.POST.get("contact_number")
					chequeMethod.cheque_email				=	request.POST.get("cheque_email")
					chequeMethod.payment_method				=	request.POST.get("payment_method")
					chequeMethod.save()
				else:
					chequeMethod							=	AccountDetails()
					chequeMethod.minimum_payout				=	request.POST.get("minimum_payout")
					chequeMethod.name						=	request.POST.get("name")
					chequeMethod.address					=	request.POST.get("address")
					chequeMethod.contact_number				=	request.POST.get("contact_number")
					chequeMethod.cheque_email				=	request.POST.get("cheque_email")
					chequeMethod.payment_method				=	request.POST.get("payment_method")
					chequeMethod.model_id					=	request.user.id
					chequeMethod.save()
				
			if request.POST.get("payment_method")	==	"paypal":
				if accountDetail:
					paypalMethod							=	accountDetail
					paypalMethod.paypal_email				=	request.POST.get("paypal_email")
					paypalMethod.minimum_payout				=	request.POST.get("minimum_payout")
					paypalMethod.payment_method				=	request.POST.get("payment_method")
					paypalMethod.save()
				else:
					paypalMethod							=	AccountDetails()
					paypalMethod.paypal_email				=	request.POST.get("paypal_email")
					paypalMethod.minimum_payout				=	request.POST.get("minimum_payout")
					paypalMethod.payment_method				=	request.POST.get("payment_method")
					paypalMethod.model_id					=	request.user.id
					paypalMethod.save()
			content = {
				"success": True,
				"data":[],
				"msg":_("Payment_details_successfully_saved")
			}
				
				
			
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
		return Response(content)

class ListSettings(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		
		SOCIALTWITTER_LINK			=	""
		SettingDetails = Setting.objects.filter(key="Social.twitter_link").first()
		if SettingDetails:
			SOCIALTWITTER_LINK	=	SettingDetails.value
			
		SOCIALINSTAGRAM_LINK			=	""
		SettingDetails = Setting.objects.filter(key="Social.instagram_link").first()
		if SettingDetails:
			SOCIALINSTAGRAM_LINK	=	SettingDetails.value
			
		SOCIALSNAPCHAT_LINK			=	""
		SettingDetails = Setting.objects.filter(key="Social.snapchat_link").first()
		if SettingDetails:
			SOCIALSNAPCHAT_LINK	=	SettingDetails.value
			
			
		SOCIALFACEBOOK_LINK			=	""
		SettingDetails = Setting.objects.filter(key="Social.facebook_link").first()
		if SettingDetails:
			SOCIALFACEBOOK_LINK	=	SettingDetails.value
			
		settingSocialTwiter		= 	SOCIALTWITTER_LINK
		settingSocialInsta		= 	SOCIALINSTAGRAM_LINK
		settingSocialSnap		= 	SOCIALSNAPCHAT_LINK
		settingSocialFacebook	= 	SOCIALFACEBOOK_LINK

		content = {
			"success": True,
			"settingSocialTwiter":settingSocialTwiter,
			"settingSocialInsta":settingSocialInsta,
			"settingSocialSnap":settingSocialSnap,
			"settingSocialFacebook":settingSocialFacebook,
			"msg":""
		}
		return Response(content)

class DeleteAccount(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	_("The_password_field_is_required")
		else:
			password	=	len(request.POST.get("password"))
			if password < 8 :
				validationErrors["password"]	=	_("The_password_field_should_be_atleast_8_digits")
		if not validationErrors:
			curr_user_id	=	request.user.id
			userDetail		=	User.objects.filter(id=curr_user_id).first()
			if userDetail:
				currentpassword		=	request.user.password
				user				=	request.user

				if userDetail.user_role_id == 2:
					if request.POST.get("password"):
						password				=	request.POST.get("password","")
						checkPassword			=	check_password(password, currentpassword)

					if checkPassword:
						curr_user_id			=	str(curr_user_id)
						user					=	userDetail
						user.email				=	userDetail.email+'_deleted_'+curr_user_id
						user.username			=	userDetail.username+'_deleted_'+curr_user_id
						user.is_deleted			=	1
						userDetail.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Subscriber_removed_successfully")
						}
					else:
						validationErrors['password']	=	_("password_is_not_correct")
						content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
						# return Response(content)	
				else:
					password				=	request.POST.get("password","")
					matchCheck			=	check_password(password, currentpassword)
					if matchCheck:
						ModelCategories.objects.filter(user_id=curr_user_id).all().delete()
						ModelImages.objects.filter(user_id=curr_user_id).all().delete()
						curr_user_id	=	str(curr_user_id)
						user				=	userDetail
						user.email			=	userDetail.email+'_deleted_'+curr_user_id
						user.username		=	userDetail.username+'_deleted_'+curr_user_id
						user.is_deleted	=	1
						user.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Model_removed_successfully")
						}
					else:
						validationErrors['password']	=	_("password_is_not_correct")
						content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
						# return Response(content)
			else:	
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}
		else:
			content = {
					"success": False,
					"data":validationErrors,
					"msg":"Validation errors"
				}
		return Response(content)


# class UsersSubscribedModel(generics.ListAPIView):
# 	permission_classes = (permissions.IsAuthenticated,)
# 	def get(self, request, *args, **kwargs):
# 		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
# 			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
# 		else :
# 			user_language = "en"
# 		translation.activate(user_language)
# 		user_role = request.user.user_role_id
# 		if user_role == 3:
# 			yearStartDate 	= str(datetime.datetime.now().year)+"-01-01 00:00:00"
# 			yearEndDate 	= str(datetime.datetime.now().year)+"-12-31 23:59:59"
# 			yearDetailActive	= UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='active').filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).all()
			# yearDetailActiveCount	= UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='active').filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).all().count()
			# print(yearDetailActive)
			# print(yearDetailActiveCount)
			# return HttpResponse("hiiiiii")
			# yearDetailExpire	= UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='expire').filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).all().count()

			# monthStartDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-01 00:00:00"
			# monthEndDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-31 23:59:59"
			# monthDetailActive	= UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='active').filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()
			# monthDetailExpire	= UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='expire').filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()

			# date_str = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
			# date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')		
			# start_of_week = date_obj - timedelta(days=date_obj.weekday()) 	# Monday
			# end_of_week = start_of_week + timedelta(days=6)  				# Sunday
			# start_of_week = str(start_of_week.date())+" 00:00:00"
			# end_of_week = str(end_of_week.date())+" 23:59:59"
			# weekDetailActive = UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='active').filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).all().count()
			# weekDetailExpire = UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='expire').filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).all().count()

			# allTimedetailActive = UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='active').all().count()
			# allTimedetailExpire = UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(user__is_deleted=0).filter(plan_status='expire').all().count()

			# if yearDetailActive:
			# 	yearlyListActive	=	[]
			# 	for sub in yearDetailActive:
			# 		sub_data							=	{}
			# 		if sub.created_at:
			# 			total_subscriber	=	yearDetailActive.filter(created_at=sub.created_at)
			# 			sub_data["total_subscriber"]		=	total_subscriber.count()
			# 			sub_data["date"]					=	sub.created_at
			# 		yearlyListActive.append(sub_data)
			# if not yearDetailActive:
			# 	yearlyListActive	=	[]


			# if yearDetailExpire:
			# 	yearDetailExpire			=		yearDetailExpire

			# if monthDetailActive:
			# 	monthDetailActive			=		monthDetailActive

			# if monthDetailExpire:
			# 	monthDetailExpire			=		monthDetailExpire

			# if weekDetailActive:
			# 	weekDetailActive			=		weekDetailActive

			# if weekDetailExpire:
			# 	weekDetailExpire			=		weekDetailExpire

			# if allTimedetailActive:
			# 	allTimedetailActive			=		allTimedetailActive

			# if allTimedetailExpire:
			# 	allTimedetailExpire			=		allTimedetailExpire

			# content = {
			# 	"success": True,
			# 	"yearlyActive":yearlyListActive,
				# "yearlyExpire":yearDetailExpire,
				# "monthlyActive":monthDetailActive,
				# "monthlyExpire":monthDetailExpire,
				# "weeklyActive":weekDetailActive,
				# "weeklyExpire":weekDetailExpire,
				# "allTimeActive":allTimedetailActive,
				# "allTimeExpire":allTimedetailExpire,
		# 		"msg":""
		# 	}

		# return Response(content)




				
def mailSnapUsernameChanged(request,snap_username):
	subscriptionDetail		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(model_subscription__social_account='snapchat').filter(user__is_deleted=0).filter(plan_status='active').all()
	if subscriptionDetail:
		for sub in subscriptionDetail:
			user_email			=	sub.user.email
			model_username		=	sub.model_user.model_name
			emailaction			=	EmailAction.objects.filter(action="model_snapchat_username_changed").first()
			emailTemplates		=	EmailTemplates.objects.filter(action ='model_snapchat_username_changed').first()
			constant = list()
			data = (emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject=emailTemplates.subject
			massage_body  = emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE
			rep_Array=[user_email,model_username,snap_username]
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
			sendEmail(request,subject,html_content,user_email)
	return True


class ModelSubscriptionStatusActive(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		planDetails		=	ModelSubscriptionPlans.objects.filter(id=request.POST.get("plan_id")).first()
		if planDetails:
			model_status				=	request.POST.get("model_status")
			if model_status:
				statusObj				=	planDetails
				statusObj.model_status	=	model_status
				statusObj.save()
			
				content = {
					"success": True,
					"data":[],
					"msg":""
				}

			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}

		else:	
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		return Response(content)


class ModelSubscriptionStatusDeactive(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		planDetails		=	ModelSubscriptionPlans.objects.filter(id=request.POST.get("plan_id")).filter(is_deleted=0).first()
		if planDetails:
			model_status				=	request.POST.get("model_status")
			if model_status:
				statusObj				=	planDetails
				statusObj.model_status	=	model_status
				statusObj.save()
			
				content = {
					"success": True,
					"data":[],
					"msg":""
				}

			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}

		else:	
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		return Response(content)







class ModelUserSubscribeGraph(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)

	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		#-----------current week date-------------
		responseDataArr	=	[]
		if request.GET.get("graphtype"):
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"week":
				today = datetime.date.today()
				week_array	=	[]

				for i in range(0 - today.weekday(), 7 - today.weekday()):
					sub_data	=	{}
					perdayWeek	=	today + datetime.timedelta(days=i)
					perdayWeek	=	str(perdayWeek)
					#---------------user subscription---------------------
					weekModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=perdayWeek+" 00:00:00").filter(created_at__lte=perdayWeek+" 23:59:59").all().count()

					#---------------subscription expires---------------------
					weekSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=perdayWeek+" 00:00:00").filter(expiry_date__lte=perdayWeek+" 23:59:59").all().count()

					sub_data['date'] 	= today + datetime.timedelta(days=i)
					sub_data['user_subscription']	= weekModelSubcriptions
					sub_data['subscription_expire']	= weekSubcriptionExpires
					responseDataArr.append(sub_data)
	


		# #-----------current month date------------
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"month":
				year = date.today().year
				month = date.today().month
				month_array	=	[]
				day_array	=	[]
				num_days = calendar.monthrange(year, month)[1]
				for day in range(1, num_days+1):
					day_array.append(day)

				for dayi in day_array:
					sub_data=	{}
					day	=	str(dayi)
					year =	str(year)
					month=	str(month)
					if len(month) < 2:
						month	=	"0"+month
					if len(day)	<2:
						day	=	"0"+day

					perdayMonth	=	year+'-'+month+'-'+day
					#---------------user subscription-----------------------
					monthModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=perdayMonth+" 00:00:00").filter(created_at__lte=perdayMonth+" 23:59:59").all().count()

					#---------------subscription expires---------------------
					monthSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=perdayMonth+" 00:00:00").filter(expiry_date__lte=perdayMonth+" 23:59:59").all().count()

					sub_data['date'] 	= year+'-'+month+'-'+day
					sub_data['user_subscription']	= monthModelSubcriptions
					sub_data['subscription_expire']	= monthSubcriptionExpires
					responseDataArr.append(sub_data)



		# #------------current year date--------------
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"year":
				year_array	=	[]
				year = date.today().year
				for i in range(1,13):
					sub_data	=	{}
					month = i
					monthStartDate = str(datetime.datetime.now().year)+"-"+str(month)+"-01 00:00:00"
					endDate	=	calendar.monthrange(year, month)[1]
					endDate	=	str(endDate)
					monthEndDate = str(datetime.datetime.now().year)+"-"+str(month)+"-"+endDate+" 23:59:59"
					#---------------user subscription-----------------------
					yearModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()

					#---------------subscription expires---------------------
					yearSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=monthStartDate).filter(expiry_date__lte=monthEndDate).all().count()

					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data['user_subscription']	= yearModelSubcriptions
					sub_data['subscription_expire']	= yearSubcriptionExpires
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data['user_subscription']	= yearModelSubcriptions
						sub_data['subscription_expire']	= yearSubcriptionExpires
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data['user_subscription']	= yearModelSubcriptions
						sub_data['subscription_expire']	= yearSubcriptionExpires
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data['user_subscription']	= yearModelSubcriptions
						sub_data['subscription_expire']	= yearSubcriptionExpires
					responseDataArr.append(sub_data)



		# #------------all time dates--------------
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"alltime":
				year_arr	=	[]
				year = datetime.date.today() - datetime.timedelta(days=3*365)
				year = year.year
				counter = 3
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						dates_three_year_ago	=	str(year)+'-'+'0'+str(month)
						if dates_three_year_ago ==	str(year)+"-010":
							dates_three_year_ago	=	str(year)+"-10"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						end_date = dates_three_year_ago+"-"+endDate+" 23:59:59"
						datetime_object = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						#---------------user subscription-----------------------
						alltimeModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()

						#---------------subscription expires---------------------
						alltimeSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=three_month_ago_date).filter(expiry_date__lte=end_date).all().count()

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]				=	str(year)+"-10"
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						else:
							sub_data["date"]				=	dates_three_year_ago
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						responseDataArr.append(sub_data)
					counter +=1	

				year = datetime.date.today() - datetime.timedelta(days=2*365)
				year = year.year
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						dates_three_year_ago	=	str(year)+'-'+'0'+str(month)
						if dates_three_year_ago ==	str(year)+"-010":
							dates_three_year_ago	=	str(year)+"-10"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						end_date = dates_three_year_ago+"-"+endDate+" 23:59:59"
						datetime_object = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						#---------------user subscription-----------------------
						alltimeModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()

						#---------------subscription expires---------------------
						alltimeSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=three_month_ago_date).filter(expiry_date__lte=end_date).all().count()

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]				=	str(year)+"-10"
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						else:
							sub_data["date"]				=	dates_three_year_ago
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						responseDataArr.append(sub_data)
					counter +=1
				year = datetime.date.today() - datetime.timedelta(days=1*365)
				year = year.year
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						dates_three_year_ago	=	str(year)+'-'+'0'+str(month)
						if dates_three_year_ago ==	str(year)+"-010":
							dates_three_year_ago	=	str(year)+"-10"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						end_date = dates_three_year_ago+"-"+endDate+" 23:59:59"
						datetime_object = datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						#---------------user subscription-----------------------
						alltimeModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()

						#---------------subscription expires---------------------
						alltimeSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=three_month_ago_date).filter(expiry_date__lte=end_date).all().count()

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]				=	str(year)+"-10"
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						else:
							sub_data["date"]				=	dates_three_year_ago
							sub_data['user_subscription']	= alltimeModelSubcriptions
							sub_data['subscription_expire']	= alltimeSubcriptionExpires
						responseDataArr.append(sub_data)
					counter +=1
	
		content = {
			"success": True,
			"data":responseDataArr,
			"msg":""
		}
		return Response(content)



class BannerSlider(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		sliderData = SliderImage.objects.filter(is_active=1).order_by("order").all()

		if sliderData:
			sliderDict = []
			for img in sliderData:
				slideList								=		{} 
				slideList["slider_title"]				=		img.title
				slideList["slider_description"]			=		img.description
				slideList["slider_order"]				=		img.order
				slideList["slider_image"]				=		settings.SLIDER_IMAGE_URL+img.slider
				sliderDict.append(slideList)

			content = {
				"success": True,
				"data":sliderDict,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}
		
				
		return Response(content)


class GetSystemIp(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		hostname = socket.gethostname()    
		IPAddr = socket.gethostbyname(hostname)
		
		content = {
				"success": True,
				"data":get_client_ip(request),
				"msg":""
			}

		return Response(content)

	
class unsubscribeNeswletter(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.AllowAny,)
	def delete(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET.get('subscriber_email'):
			subscriber_email = request.GET.get('subscriber_email')
			if subscriber_email	==	request.GET.get('subscriber_email'):
				if request.GET.get('subscriber_email') == None or request.GET.get('subscriber_email')  == "":
					content = {
						"success": False,
						"data":[],
						"msg":_("Invalid_request")
					}
				else:
					removeNewsletterSubscriber = NewsletterSubscriber.objects.filter(email=request.GET.get('subscriber_email')).first()
					if removeNewsletterSubscriber:
						NewsletterSubscriber.objects.filter(email=request.GET.get('subscriber_email')).delete()
						content = {
							"success": True,
							"data":[],
							"msg":_("Your_are_successfully_unsubscribed_from_newsletters")
						}
					else:
						content = {
							"success": False,
							"data":[],
							"msg":_("Subscriber_does_not_exists")
						}
				
		return Response(content)


class ValidateforgotPassword(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	_("This_email_is_not_valid")
			else:
				if not User.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	_("This_email_does_not_exists")

			
		if not validationErrors:
			email 								= 	request.POST.get("email", "")
			strEmail 							= 	str(email)+str(int(datetime.datetime.now().timestamp()))
			res 								= 	hashlib.md5(strEmail.encode())
			forgotpassword_string 				= 	res.hexdigest() 
			forgotpassword_user					=	User.objects.filter(email=email).first()
			forgotpassword_user.forgot_password_string	=	forgotpassword_string
			forgotpassword_user.save()

			email 								=	email
			link								=  	settings.FRONT_SITE_URL+'user/reset-password/'+forgotpassword_string
			emailaction							=	EmailAction.objects.filter(action="forgot_password").first()
			emailTemplates						=	EmailTemplates.objects.filter(action = 'forgot_password').first()
			constant 							=	list()
			data								= 	(emailaction.option.split(','))
			for obj in data:
				constant.append("{"+ obj +"}")
			subject			=	emailTemplates.subject
			rep_Array		=	[email,link]
			massage_body  	= 	emailTemplates.body
			website_url		=	settings.FRONT_SITE_URL
			site_title		=	settings.SITETITLE

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

			content = {
				"success": True,
				"data":[],
				"msg":_("Your_reset_password_request_has_been_registered_successfully_Please_check_your_email_to_reset_your_password")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)


class ResetPassword(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("newpassword") == None or request.POST.get("newpassword") == "":
			validationErrors["newpassword"]	=	_("The_password_field_is_required")

		
		if request.POST.get("forgot_password_string") == None or request.POST.get("forgot_password_string") == "":
			validationErrors["forgot_password_string"]	=	_("The_forgot_password_string_field_is_required")
		else:
			if not User.objects.filter(forgot_password_string=request.POST.get("forgot_password_string")).exists():
				validationErrors["forgot_password_string"]	=	_("The_forgot_password_string_does_not_exists")

			
		if not validationErrors:
			forgot_password_string 				= 	request.POST.get("forgot_password_string", "")
			reset_password_user					=	User.objects.filter(forgot_password_string=forgot_password_string).first()
			reset_password_user.password		=	make_password(request.POST.get("newpassword"))
			reset_password_user.save()

			resetPasswordObj						=		User.objects.filter(id=reset_password_user.id).first()
			resetPasswordObj.forgot_password_string	=		""
			resetPasswordObj.save()


			content = {
				"success": True,
				"data":[],
				"msg":_("Your_password_resets_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)


class BlockText(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		blockData = Block.objects.filter(page_slug="Text-Block").filter(is_active=1).order_by("block_order").values("id")

		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).filter(language_code=user_language).all()  # or simply .values() to get all fields
		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					# blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					# blockList["slug"]					=	BlockObj.block.slug
					blocks.append(blockList)
			content = {
				"success": True,
				"data":blocks,
				"msg":""
			}
		else:
			content = {
				"success": False,
				"data":[],
				"msg":_("No_data_found")
			}	
		return Response(content)


class ReferSlugApi(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.POST.get('modelSlug') == None or request.POST.get('modelSlug') == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			modelSlug = request.POST.get('modelSlug')
			userSlug = User.objects.filter(is_deleted=0).filter(is_approved=1).filter(slug=modelSlug)
			if userSlug:
				content = {
					"success": True,
					"data":[],
					"msg":_("Successfullysaved")
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("No Slug Found")
				}
		return Response(content)


		
class PaymentProcessing(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		# if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
		# 	user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		# else :
		# 	user_language = "en"
		# translation.activate(user_language)
		# response = requests.get(auth=auth)
		response = requests.get('http://127.0.0.1:8000/api/v1/payment-processing', auth=HTTPBasicAuth('payment-processing', 'pass'))
		print(response)
	
		content = {
		"success": True,
		"data": "",
		"msg":""
		}
		return Response(content)

class MasterLogin(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET.get('slug') == None or request.GET.get('slug') == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			slug = request.GET.get("slug")
			user = User.objects.filter(slug=slug).filter(is_deleted=0).first()
			if user:
				if user.login_with_model == 1:
					ModelImage = ModelImages.objects.filter(user_id=user.id).first()
					if ModelImage:
						profile_image					=	settings.MODEL_IMAGE_URL+ModelImage.image_url
					else:
						profile_image					=	""
					userDetail	=	{
						"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status,"profile_image":profile_image
					}
					content = {
					"success": True,
					"token":jwt_encode_handler(jwt_payload_handler(user)),
					"data": userDetail,
					"msg":""
					}
					user.login_with_model = 0
					user.save()
				else:
					content = {
					"success": False,
					"token":jwt_encode_handler(jwt_payload_handler(user)),
					"data": [],
					"msg":_("Invalid_request")
					}
			else:
				content = {
					"success": False,
					"data": [],
					"msg":_("Invalid_request")
					}
		return Response(content)
		
		
class FaqText(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
			
		translation.activate(user_language)
		
		validationErrors	=	{}
		if request.GET.get("slug") == None or request.GET.get("slug") == "":
			validationErrors["slug"]	=	_("The_slug_field_is_required")
			
		if not validationErrors:
			faqData = Faq.objects.filter(is_active=1).filter(pagename=request.GET.get("slug")).values("id")
			if faqData:
				faqDesc 	= FaqDescription.objects.filter(faq_id__in=faqData).filter(language_code=user_language).all()  # or simply .values() to get all fields
			
				blocks	=	[]
				if faqDesc:
					for faqObj in faqDesc:
						faqList							=	{}
						# blockList["block_name"]				=	BlockObj.block_name
						faqList["question"]				=	faqObj.question
						faqList["answer"]				=	faqObj.answer
						faqList["id"]				=	faqObj.id
						# blockList["slug"]				=	BlockObj.block.slug
						blocks.append(faqList)
	
				content = {
					"success": True,
					"data":blocks,
					"msg":""
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("No_data_found")
				}	
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
		return Response(content)


class SiteContentImages(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		if request.GET.get('slug') == None or request.GET.get('slug') == "":
			content = {
				"success": False,
				"data":[],
				"msg":_("Invalid_request")
			}
		else:
			slug = request.GET.get("slug")
			blockData = Block.objects.filter(slug=slug).filter(is_active=1).first()

			if blockData:
				blockImage = settings.BLOCK_IMAGE_URL+blockData.image
	
				content = {
					"success": True,
					"data":blockImage,
					"msg":""
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("No_data_found")
				}
		
		return Response(content)
		
		
class DeActivateAccount(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if request.POST.get("type") == None or request.POST.get("password") == "":
			validationErrors["type"]	=	_("The_type_field_is_required")
		if not validationErrors:
			curr_user_id	=	request.user.id
			userDetail		=	User.objects.filter(id=curr_user_id).first()
			if userDetail:
				currentpassword		=	request.user.password
				user				=	request.user
				if request.POST.get("type") == 'permanent':
					if userDetail.user_role_id == 2:
						curr_user_id			=	str(curr_user_id)
						user					=	userDetail
						user.email				=	userDetail.email+'_deleted_'+curr_user_id
						user.username			=	userDetail.username+'_deleted_'+curr_user_id
						user.is_deleted			=	1
						user.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Subscriber_removed_successfully")
						}

					else:
						ModelCategories.objects.filter(user_id=curr_user_id).all().delete()
						ModelImages.objects.filter(user_id=curr_user_id).all().delete()
						curr_user_id	=	str(curr_user_id)
						user				=	userDetail
						user.email			=	userDetail.email+'_deleted_'+curr_user_id
						user.username		=	userDetail.username+'_deleted_'+curr_user_id
						user.is_deleted	=	1
						user.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Subscriber_removed_successfully")
						}
				else:
					if userDetail.user_role_id == 2:
						user					=	userDetail
						user.is_active			=	0
						user.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Subscriber_removed_successfully")
						}

					else:
						user				=	userDetail
						user.is_active		=	0
						user.save()

						content = {
							"success": True,
							"data":[],
							"msg":_("Subscriber_removed_successfully")
						}

			else:	
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid_request")
				}
		else:
			content = {
					"success": False,
					"data":validationErrors,
					"msg":"Validation errors"
				}
		return Response(content)
		
		
class HomepageProfileApi(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id	
		homepageProfile										=   User.objects.filter(id=user_id).first()
		if homepageProfile.is_homepage_profile == 1 or homepageProfile.is_homepage_profile == '1':
			homepageProfile.is_homepage_profile = 0
			homepageProfile.save()
		else:
			homepageProfile.is_homepage_profile = 1
			homepageProfile.save()
		
		content = {
			"success": True,
			"data":[],
			"msg":_("Homepage_Profile_updated_sucessfully")
		}
		return Response(content)
		

		
class EditPaymentMethodApi(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)		
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	_("The_old_password_field_is_required")

		else:
			lengthPass	=	len(request.POST.get("password"))
			if lengthPass < 8 :
				validationErrors["password"]	=	_("The_old_password_field_should_be_atleast_8_digits")
		user_id 			= 	request.user.id	

		if not validationErrors:
			currentpassword		=	request.user.password
			password			=	request.POST.get("password")
			matchcheck= check_password(password, currentpassword)
			if matchcheck:
				content = {
					"success": True,
					"data":[],
					"msg":_("Password_is_matched_correctly")
				}
			else:
				validationErrors["password"]	=	_("Old_password_is_not_correct")
				content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
				}
			
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
				}
		return Response(content)
			
class NewExpiredSubscribers(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		#-----------current week date-------------
		responseDataArr	=	[]
		if request.GET.get("graphtype"):
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"week":
				week_array	=	[]
				current_date = date.today()
				current_date = str(current_date)
				dt = datetime.datetime.strptime(current_date, "%Y-%m-%d")
				start = dt - timedelta(days=dt.weekday())
				end = start +timedelta(6)
				tillLastWeek	=	start - timedelta(1)
				tillLastWeek	=	tillLastWeek.strftime('%Y-%m-%d')
				start_date = start.strftime('%Y-%m-%d')
				end_date = end.strftime('%Y-%m-%d')
				
				sub_data						=	{}
				#---------------user subscription---------------------
				weekModelSubcriptions			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=start_date+" 00:00:00").filter(created_at__lte=end_date+" 23:59:59").all().count()
				#---------------subscription expires---------------------
				weekSubcriptionExpires			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=start_date+" 00:00:00").filter(expiry_date__lte=end_date+" 23:59:59").all().count()
			
				#----------------Total Subscriber---------------------------------
				weekTotalSubcriptions			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status="active").all().count()
				lastWeekTotalSubcriptions		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__lte=tillLastWeek+" 23:59:59").filter(plan_status="active").all().count()
				try:
					weekPercentage					=	(lastWeekTotalSubcriptions-weekTotalSubcriptions/lastWeekTotalSubcriptions)*100
					weekPercentage=round(float(weekPercentage,2))
				except ZeroDivisionError as error:
					weekPercentage   				=	0
				sub_data['new_subscribers']		= weekModelSubcriptions
				sub_data['expired_subscribers']	= weekSubcriptionExpires
				sub_data['total_subscribers']	= weekTotalSubcriptions
				sub_data['week_percentage']		= weekPercentage
				responseDataArr.append(sub_data)
	


		# #-----------current month date------------
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"month":
				year = str(date.today().year)
				month = str(date.today().month)
				day			=	"01"
				if len(month) < 2:
					month	=	"0"+month

				startdayMonth	=	year+'-'+month+'-'+day
				year	=	int(year)
				month	=	int(month)
				endDate	=	calendar.monthrange(year, month)[1]
				endDate	=	str(endDate)
				enddayMonth	=	str(year)+"-"+str(month)+"-"+str(endDate)

				#---------------user subscription-----------------------
				monthModelSubcriptions			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=startdayMonth+" 00:00:00").filter(created_at__lte=enddayMonth+" 23:59:59").all().count()

				#---------------subscription expires---------------------
				monthSubcriptionExpires			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=startdayMonth+" 00:00:00").filter(expiry_date__lte=enddayMonth+" 23:59:59").all().count()
				
				#----------------Total Subscriber---------------------------------
				monthTotalSubcriptions			=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status="active").all().count()
				sub_data						=	{}
				sub_data['new_subscribers']		= 	monthModelSubcriptions
				sub_data['expired_subscribers']	= 	monthSubcriptionExpires
				sub_data['total_subscribers']	= 	monthTotalSubcriptions
				sub_data['month_percentage']	= 	50
				responseDataArr.append(sub_data)



		# #------------current year date--------------
			graphtype	=	request.GET.get("graphtype")
			if graphtype	==	"year":
				year 			= str(date.today().year)
				startDateYear	=	year+"-"+"01"+"-"+"01"
				endDateYear		=	year+"-"+"12"+"-"+"31"
				#---------------user subscription------------------------------
				yearModelSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=startDateYear+" 00:00:00").filter(created_at__lte=endDateYear+" 23:59:59").all().count()

				#---------------subscription expires---------------------------
				yearSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(expiry_date__gte=startDateYear+" 00:00:00").filter(expiry_date__lte=endDateYear+" 23:59:59").all().count()
				#-----------------------------Total Subscriber-----------------
				yearTotalSubcriptions	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status="active").all().count()

				sub_data						=	{}
				sub_data['new_subscribers']		= 	yearModelSubcriptions
				sub_data['expired_subscribers']	= 	yearSubcriptionExpires
				sub_data['total_subscribers']	= 	yearTotalSubcriptions
				sub_data['year_percentage']		= 	50
				responseDataArr.append(sub_data)

	
		content = {
			"success": True,
			"data":responseDataArr,
			"msg":""
		}
		return Response(content)
		
		

class MainProfileImage(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)		
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		if len(request.FILES) == 0:
			validationErrors["main_image"]	=	_("The_image_field_is_required")
		elif len(request.FILES) > 0:
			file = request.FILES["main_image"].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["main_image"]	=	_("The_image_is_not_a_valid_image_Please_upload_a_valid_image_Valid_extensions_are_jpg,jpeg,png,gif")
		
		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year

			if request.FILES.get("main_image"):
				image = request.FILES.get("main_image")
				filename = image.name.split(".")[0].lower().replace(" ","-")
				extension = image.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				attachment = str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(image, "model_images/"+attachment)
				
				
			userDetail							=		User.objects.filter(id=request.user.id).first()
			userDetail.main_image				=		str(currentMonth)+str(currentYear)+"/"+newfilename
			userDetail.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Your_profile_image_has_been_added_successfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
			

class PrivateFeedEnable(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id	
		privateFeedCheck							=   User.objects.filter(id=user_id).first()
		if privateFeedCheck.is_private_feed == 1:
			privateFeedCheck.is_private_feed = 0
			privateFeedCheck.save()
		else:
			privateFeedCheck.is_private_feed = 1
			privateFeedCheck.save()
		
		content = {
			"success": True,
			"data":[],
			"msg":_("Private_feed_updated_sucessfully.")
		}
		return Response(content)

		
class cancelledPlan(generics.CreateAPIView):
	permission_classes = (permissions.IsAuthenticated,)		
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
			
		translation.activate(user_language)
		
		validationErrors	=	{}
		if request.POST.get("id") == None or request.POST.get("id") == "":
			validationErrors["id"]	=	_("id field is required.")
			
		if request.POST.get("feedback") == None or request.POST.get("feedback") == "":
			validationErrors["feedback"]	=	_("feedback field is required.")
			
		if request.POST.get("stay_connected") == None or request.POST.get("stay_connected") == "":
			validationErrors["stay_connected"]	=	_("stay_connected field is required.")
			
		if not validationErrors:
			TransactionHistory1 = TransactionHistory.objects.filter(id=request.POST.get("id")).filter(user_id=request.user.id).first()
			if TransactionHistory1:
				obj    							=   TransactionHistory.objects.filter(id=request.POST.get("id")).first()
				obj.is_subscription_cancelled	=	1
				obj.subscription_cancelled_on	=	datetime.datetime.now()
				obj.save()
				
				obj    =   UserSubscriptionPlan.objects.filter(id=TransactionHistory1.user_subscription.id).first()
				obj.is_subscription_cancelled		=	1
				obj.subscription_cancelled_on	=	datetime.datetime.now()
				obj.feedback	=	request.POST.get("feedback")
				obj.stay_connected 	=	request.POST.get("stay_connected")
				obj.expiry_date 	=	datetime.datetime.now()
				obj.plan_status 	=	'expire'
				obj.save()
				
				
				content = {
					"success": True,
					"data":[],
					"msg":_("Your plan has been cancelled successfully.")
				}
				return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":_("Invalid Accesss.")
				}
				return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			



class ModelVerificationImages(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}
		currentMonth = datetime.datetime.now().month
		currentYear = datetime.datetime.now().year

		if not validationErrors:
			gifi_image  = ''
			gibi_image  = ''
			pnti_image	= ''
			pntiwdp_image = ''
			if request.FILES.get("government_id_front_image"):
				gifiFile = request.FILES.get("government_id_front_image")
				filename = gifiFile.name.split(".")[0].lower()
				extension = gifiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gifiFile, "model_images/"+gifi_image)
				imageDetail	=	{
						"gifi":gifi_image,
						"gibi":"",
						"pnti":"",
						"pntiwdp":"",
					}
				
			if request.FILES.get("government_id_back_image"):
				gibiFile = request.FILES.get("government_id_back_image")
				filename = gibiFile.name.split(".")[0].lower()
				extension = gibiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(gibiFile, "model_images/"+gibi_image)
				imageDetail	=	{
						"gifi":"",
						"gibi":gibi_image,
						"pnti":"",
						"pntiwdp":"",
					}
				
			if request.FILES.get("photo_next_to_id"):
				pntiFile = request.FILES.get("photo_next_to_id")
				filename = pntiFile.name.split(".")[0].lower()
				extension = pntiFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension
				pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiFile, "model_images/"+pnti_image)
				imageDetail	=	{
						"gifi":"",
						"gibi":"",
						"pnti":pnti_image,
						"pntiwdp":"",
					}
				
			if request.FILES.get("photo_next_to_id_with_dated_paper"):
				pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
				filename = pntiwdpFile.name.split(".")[0].lower()
				extension = pntiwdpFile.name.split(".")[-1].lower()
				newfilename = str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))+"."+extension	
				pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				Upload.upload_image_on_gcp(pntiwdpFile, "model_images/"+pntiwdp_image)
					
				imageDetail	=	{
						"gifi":"",
						"gibi":"",
						"pnti":"",
						"pntiwdp":pntiwdp_image,
					}
			content = {
			"success": True,
			"data": imageDetail,
			"msg":""
			}
			

		return Response(content)




class ModelPersonalInformation(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		validationErrors	=	{}

		if not validationErrors:
				
			NewUserObj 										= 	User.objects.filter(id=request.user.id).first()
			NewUserObj.first_name							=	request.POST.get("first_name","")
			NewUserObj.last_name							=	request.POST.get("last_name","")
			NewUserObj.previous_first_name					=	request.POST.get("previous_first_name","")
			NewUserObj.previous_last_name					=	request.POST.get("previous_last_name","")
			NewUserObj.date_of_birth						=	request.POST.get("date_of_birth","")
			NewUserObj.gender								=	request.POST.get("gender","")
			NewUserObj.country								=	request.POST.get("country","")
			NewUserObj.address_line_1						=	request.POST.get("address_line_1","")
			NewUserObj.address_line_2						=	request.POST.get("address_line_2","")
			NewUserObj.city									=	request.POST.get("city","")
			NewUserObj.postal_code							=	request.POST.get("postal_code","")
			NewUserObj.skype_number							=	request.POST.get("skype_number","")
			NewUserObj.default_currency						=	request.POST.get("default_currency","")
			NewUserObj.save()
				
			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
			
class ModelVerificationInformation(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		validationErrors	=	{}
		if not validationErrors:
			NewUserObj 										= 	User.objects.filter(id=request.user.id).first()
			NewUserObj.government_id_number					=	request.POST.get("government_id_number","")
			NewUserObj.government_id_expiration_date		=	request.POST.get("government_id_expiration_date","")
			NewUserObj.government_id_front_image			=	request.POST.get("government_id_front_image","")
			NewUserObj.government_id_back_image				=	request.POST.get("government_id_back_image","")
			NewUserObj.photo_next_to_id						=	request.POST.get("photo_next_to_id","")
			NewUserObj.photo_next_to_id_with_dated_paper	=	request.POST.get("photo_next_to_id_with_dated_paper","")
			NewUserObj.save()
			
			ModelImage = ModelImages.objects.filter(user_id=request.user.id).all()
			if ModelImage:
				profile_image					=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
			else:
				profile_image					=	""
				
			user = User.objects.filter(id=request.user.id).first()
			userDetail	=	{
				"email":user.email,"user_role_id":user.user_role_id,"first_name":user.first_name,"last_name":user.last_name,"from_date":user.from_date,"address_line_2":user.address_line_2,"city":user.city,"age":user.age,"hair":user.hair,"eyes":user.eyes,"gender":user.gender,"date_of_birth":user.date_of_birth,"address_line_1":user.address_line_1,"amazon_wishlist_link":user.amazon_wishlist_link,"bio":user.bio,"height":user.height,"model_name":user.model_name,"postal_code":user.postal_code,"previous_first_name":user.previous_first_name,"previous_last_name":user.previous_last_name,"private_snapchat_link":user.private_snapchat_link,"public_instagram_link":user.public_instagram_link,"public_snapchat_link":user.public_snapchat_link,"skype_number":user.skype_number,"twitter_link":user.twitter_link,"weight":user.weight,"youtube_link":user.youtube_link,"youtube_video_url":user.youtube_video_url,"default_currency":user.default_currency,"rank":user.rank,"rank_status":user.rank_status,"profile_image":profile_image
			}
			content = {
				"success": True,
				"data":userDetail,
				"token":jwt_encode_handler(jwt_payload_handler(user)),
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
class UpdateModelSubscriptionPlan(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		if request.POST.get("subscription") == None or request.POST.get("subscription") == "":
			validationErrors["subscription"]	=	_("The_subscription_field_is_required")
		
		user_id = request.user.id	
		if not validationErrors:
			subscription_dict = request.POST.get("subscription")
			discount_arr = []
			selectedplanids	=	[]
			if subscription_dict:
				subscription_dict = json.loads(subscription_dict)
				for subdata in subscription_dict:
					if subdata:
						if subscription_dict[subdata]['is_enabled'] == True:
							is_enabled = 1
						else:
							is_enabled = 0

						if subdata	==	'snapchat' and subscription_dict[subdata]['username']:
							subcriptionData = ModelSubscriptions.objects.filter(user_id=user_id).filter(social_account=subdata).first()
							if subcriptionData:
								subUsername = subscription_dict[subdata]['username']
								if subUsername !=	subcriptionData.username:
									subObj 					= subcriptionData
									subObj.username 		= subUsername
									subObj.save()
									mailSnapUsernameChanged(request,subUsername)
								
						alreadyModelSubscriptions 	= ModelSubscriptions.objects.filter(user_id=request.user.id).filter(social_account=subdata).filter(is_deleted=0).first()
						if alreadyModelSubscriptions:
							subObj 					= alreadyModelSubscriptions
							subObj.user_id 			= user_id
							subObj.social_account 	= subdata
							subObj.username 		= subscription_dict[subdata]['username']
							subObj.is_enabled 		= is_enabled
							subObj.save()
						else:
							subObj 					= ModelSubscriptions()
							subObj.user_id 			= user_id
							subObj.social_account 	= subdata
							subObj.username 		= subscription_dict[subdata]['username']
							subObj.is_enabled 		= is_enabled
							subObj.save()
						
						subId = subObj.id
						today_date = str(datetime.datetime.today().date())+" 00:00:00"
						if subdata !="tips" and is_enabled == 1 and len(subscription_dict[subdata]['plans']) > 0:	
							for planData in subscription_dict[subdata]['plans']:
								subscription_plan_id 	= planData["subscription_plan_id"] 
								plan_type 				= planData["plan_type"]
								offer_period_time 		= planData["offer_period_time"]
								offer_period_type 		= planData["offer_period_type"]
								price 					= planData["price"]
								description 			= planData["description"]
								offer_name 				= planData["offer_name"]
								is_discount_enabled 	= planData["is_discount_enabled"]
								discount 				= planData["discount"]
								is_permanent_discount 	= planData["is_permanent_discount"] 
								from_discount_date 		= planData["from_discount_date"] 
								to_discount_date 		= planData["to_discount_date"] 
								is_apply_to_rebills 	= planData["is_apply_to_rebills"] 
									
								price = isDecimal(price)
								discount = isDecimal(discount)
								is_discount_enabled = isNum(is_discount_enabled)
								is_permanent_discount = isNum(is_permanent_discount)
								is_apply_to_rebills = isNum(is_apply_to_rebills)
								
								if is_discount_enabled and decimal.Decimal(discount) > 0:
									discounted_price = decimal.Decimal(price)-((decimal.Decimal(price)*decimal.Decimal(discount))/100)
									discounted_price = round(float(discounted_price),2)
									is_discount_enabled = 1
									discount_arr.append(discount)
									discount_arr = [Decimal(x) for x in discount_arr]
								else:
									is_discount_enabled = 0
									discounted_price = price
									
								
								if is_permanent_discount:
									is_permanent_discount = 1
								else:
									is_permanent_discount = 0
									
								if is_apply_to_rebills:
									is_apply_to_rebills = 1
								else:
									is_apply_to_rebills = 0
									
								if plan_type == "recurring":	
									if from_discount_date != "" and from_discount_date > today_date:
										is_discount_enabled = 0		
									
								if subscription_plan_id  != 0:
									plansObj = ModelSubscriptionPlans.objects.filter(id=subscription_plan_id).filter(model_subscription_id=subObj.id).filter(is_deleted=0).first()
									plansObj.user_id 							= request.user.id
									plansObj.model_subscription_id 				= subId
									plansObj.plan_type 							= plan_type
									plansObj.offer_period_time 					= offer_period_time
									plansObj.offer_period_type 					= offer_period_type
									plansObj.price 								= price
										
									plansObj.discounted_price 					= discounted_price
									plansObj.currency 							= request.user.default_currency
									plansObj.offer_name 						= offer_name
									plansObj.description 						= description
									plansObj.is_discount_enabled 				= is_discount_enabled
									
									plansObj.discount 						= discount
									plansObj.from_discount_date 			= from_discount_date
									
									if to_discount_date:
										plansObj.to_discount_date 					= to_discount_date
										
									plansObj.is_permanent_discount 				= is_permanent_discount
									plansObj.is_apply_to_rebills 				= is_apply_to_rebills
									plansObj.save()
									selectedplanids.append(plansObj.id)
									selectedplanids = [Decimal(x) for x in selectedplanids]
								else:
									plansObj = ModelSubscriptionPlans()
									plansObj.user_id 							=  request.user.id
									plansObj.model_subscription_id 				= subId
									plansObj.plan_type 							= plan_type
									plansObj.offer_period_time 					= offer_period_time
									plansObj.offer_period_type 					= offer_period_type
									plansObj.price 								= price
										
									plansObj.discounted_price 					= discounted_price
									plansObj.currency 							= request.user.default_currency
									plansObj.offer_name 						= offer_name
									plansObj.description 						= description
									plansObj.is_discount_enabled 				= is_discount_enabled
									
									plansObj.discount 						= discount
									plansObj.from_discount_date 			= from_discount_date
									
									if to_discount_date:
										plansObj.to_discount_date 					= to_discount_date
										
									plansObj.is_permanent_discount 				= is_permanent_discount
									plansObj.is_apply_to_rebills 				= is_apply_to_rebills
									plansObj.save()
									
									selectedplanids.append(plansObj.id)
									selectedplanids = [Decimal(x) for x in selectedplanids]
											
															
				if len(discount_arr)!=0:
					high_discount	=	max(discount_arr)
					User.objects.filter(id=request.user.id).update(highest_discount=high_discount)
				else:
					discount_arr = []
					
				if len(selectedplanids)!=0:
					ModelSubscriptionPlans.objects.exclude(id__in=selectedplanids).filter(user_id=request.user.id).update(is_deleted=1)

			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			


class UpdateModelProfileStep1(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		user_id 		= 	request.user.id	
		userDetails		=   User.objects.filter(user_role_id=3).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		images			=	request.POST.getlist("images")

		if not userDetails:
			validationErrors["user"]	=	_("Invalid_request")


		if not validationErrors:
			lastUserId										=	user_id
			NewUserObj										=   userDetails
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year
			slug = (request.POST.get("model_name","")).lower()
			if User.objects.filter(slug=slug).exists():
				slug = (request.POST.get("model_name","")+str(userDetails.id)).lower()
			
			slug	=	slug.replace(" ","-")

			if request.POST.get("model_name") != None:
				NewUserObj.model_name							=	request.POST.get("model_name")
			if request.POST.get("bio") != None:
				NewUserObj.bio									=	request.POST.get("bio")
			NewUserObj.slug										=	slug
			NewUserObj.save()	

			images 								= 	request.POST.get("images")
			images = json.loads(images)
			if images:
				for img in images:
					if(img['id'] == ""):
						Modelimgs							=	ModelImages()
						Modelimgs.image_url					=	img['img_url']
						Modelimgs.user_id					=	lastUserId
						Modelimgs.save()
					else:
						modelImages1		=	ModelImages.objects.filter(id=img['id']).first()
						if modelImages1:				
							Modelimgs							=	modelImages1
							Modelimgs.image_url 				= 	img['img_url']
							Modelimgs.user_id					=	lastUserId
							Modelimgs.save()
							
							
			ModelImage = ModelImages.objects.filter(user_id=lastUserId).all()
			if ModelImage:
				profile_image					=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
			else:
				profile_image					=	""

			content = {
				"success": True,
				"data":[],
				"profile_image":profile_image,
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
			
			
			
class UpdateModelProfileStep2(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		user_id 		= request.user.id	
		userDetails		=   User.objects.filter(user_role_id=3).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		
		
		if not userDetails:
			validationErrors["user"]	=	_("Invalid_request")
		
		
		if not validationErrors:
			lastUserId										=	user_id
			NewUserObj										=   userDetails
			
			if request.POST.get("best_known_for") != None:
				NewUserObj.best_known_for						=	request.POST.get("best_known_for")
			if request.POST.get("private_snapchat_link") != None:
				NewUserObj.private_snapchat_link				=	request.POST.get("private_snapchat_link")
			if request.POST.get("public_snapchat_link") != None:
				NewUserObj.public_snapchat_link					=	request.POST.get("public_snapchat_link")
			if request.POST.get("public_instagram_link") != None:
				NewUserObj.public_instagram_link				=	request.POST.get("public_instagram_link")
			if request.POST.get("twitter_link") != None:
				NewUserObj.twitter_link							=	request.POST.get("twitter_link")
			if request.POST.get("youtube_link") != None:
				NewUserObj.youtube_link							=	request.POST.get("youtube_link")
			if request.POST.get("amazon_wishlist_link") != None:
				NewUserObj.amazon_wishlist_link					=	request.POST.get("amazon_wishlist_link")
			if request.POST.get("age") != None:
				NewUserObj.age									=	request.POST.get("age")
			if request.POST.get("from_date") != None:
				NewUserObj.from_date							=	request.POST.get("from_date")
			if request.POST.get("height") != None:
				NewUserObj.height								=	request.POST.get("height")
			if request.POST.get("weight") != None:
				NewUserObj.weight								=	request.POST.get("weight")
			if request.POST.get("hair") != None:
				NewUserObj.hair									=	request.POST.get("hair")
			if request.POST.get("eyes") != None:
				NewUserObj.eyes									=	request.POST.get("eyes")
			if request.POST.get("youtube_video_url") != None:
				NewUserObj.youtube_video_url					=	request.POST.get("youtube_video_url")

			NewUserObj.save()
					
			categories 					=   request.POST.get('categories')
			if categories != None and categories != "":
				ModelCategories.objects.filter(user_id=request.user.id).delete()
				categories = categories.split(',')
				for category in categories:
					ModelCategoriesInfo							=	ModelCategories()
					ModelCategoriesInfo.dropdown_manager_id 	= 	category
					ModelCategoriesInfo.user_id 				= 	lastUserId
					ModelCategoriesInfo.save()
					
					
			additional_link 								= 	request.POST.get("additional_link")
			additional_link = json.loads(additional_link)
			if additional_link:
				AdditionalLinks.objects.filter(model_id=request.user.id).all().delete()
				for detail in additional_link:
					link	=	detail['link']					
					name	=	detail['name']
					ModelAdditionalLinks					=	AdditionalLinks()
					ModelAdditionalLinks.link 				= 	link
					ModelAdditionalLinks.name 				= 	name
					ModelAdditionalLinks.model_id			=	request.user.id
					ModelAdditionalLinks.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)

			
class editProfile(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id
		userDetail = User.objects.filter(id=user_id).filter(is_deleted=0).first()
		if userDetail:
			if userDetail.user_role_id == 2:
				ModelDetail = model_to_dict(userDetail)
			else:
				ModelDetail = User.objects.filter(id=user_id).filter(is_deleted=0).first()
				ModelDetail = model_to_dict(ModelDetail)
				if ModelDetail:
					ModelImage = ModelImages.objects.filter(user_id=ModelDetail["id"]).all()
					if ModelImage:
						images	=	[]
						for ProfileImage in ModelImage:
							imgList = {}
							imgList['img_url'] = settings.MODEL_IMAGE_URL+ProfileImage.image_url
							imgList['id'] 		= ProfileImage.id
							images.append(imgList)
						ModelDetail["profile_image"]	=	settings.MODEL_IMAGE_URL+ModelImage[0].image_url
						ModelDetail["images"]			=	images
					else:
						ModelDetail["profile_image"]	=	settings.MEDIA_URL+"dummy.jpeg"
						ModelDetail["images"]			=	""
						
						
					ModelCat = ModelCategories.objects.filter(user_id=ModelDetail["id"]).all()
					#ModelCat = list(ModelCat)
					
					catDataList = []
					if ModelCat:
						for catData in ModelCat:
							catListData = {}
							catListData['name'] = catData.dropdown_manager.name
							catListData['id'] = catData.dropdown_manager_id
							catDataList.append(catListData)
						ModelDetail["categories"] = catDataList
					else:
						ModelDetail["categories"] = catDataList

					ModelAdditionalLinks = AdditionalLinks.objects.filter(model_id=ModelDetail["id"]).all()
					additionalDataList = []
					if ModelAdditionalLinks:
						for linkData in ModelAdditionalLinks:
							additionalListData = {}
							additionalListData['id'] = linkData.id
							additionalListData['name'] = linkData.name
							additionalListData['link'] = linkData.link
							additionalDataList.append(additionalListData)
							
					ModelDetail["additional_links"] = additionalDataList
					
			content = {
				"success": True,
				"data12":ModelDetail,
				"msg":""
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data12":[],
				"msg":_("Invalid_requst")
			}
			return Response(content)
			
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		validationErrors	=	{}

		if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
			if request.POST.get("oldpassword") == None or request.POST.get("oldpassword") == "":
				validationErrors["oldpassword"]	=	_("The_old_password_field_is_required")
			else:
				lengthOldpass	=	len(request.POST.get("oldpassword"))
				if lengthOldpass < 8 :
					validationErrors["oldpassword"]	=	_("The_old_password_field_should_be_atleast_8_digits")

			if request.POST.get("newpassword") == None or request.POST.get("newpassword") == "":
				validationErrors["newpassword"]	=	_("The_new_password_field_is_required")
			else:

				lengthNewpass	=	len(request.POST.get("newpassword"))
				if lengthNewpass < 8 :
					validationErrors["newpassword"]	=	_("The_new_password_field_should_be_atleast_8_digits")

			if request.POST.get("confirmpassword") == None or request.POST.get("confirmpassword") == "":
				validationErrors["confirmpassword"]	=	_("The_confirm_password_field_is_required")
			else:
				if request.POST.get("confirmpassword") != request.POST.get("newpassword"):
					validationErrors["confirmpassword"]	=	_("The_confirm_password_and_new_password_does_not_match")

		user_id 		= request.user.id	
		userDetails		=   User.objects.filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		
		
		if not userDetails:
			validationErrors["user"]	=	_("Invalid_request")
		
		
		if not validationErrors:
			currentpassword										=	request.user.password
			if userDetails:
				NewUserObj										=   userDetails
				NewUserObj.skype_number							=	request.POST.get("skype_number")
				NewUserObj.model_name							=	request.POST.get("model_name")
				NewUserObj.phone_number							=	request.POST.get("phone_number")
				if request.POST.get("newpassword"):
					oldpassword			=	request.POST.get("oldpassword")
					newpassword			=	request.POST.get("newpassword")
					matchcheck= check_password(oldpassword, currentpassword)
					if request.POST.get("key_name")	== "1" or request.POST.get("key_name")	== 1:
						if matchcheck:
							NewUserObj.password							=	make_password(request.POST.get("newpassword", ""))
							NewUserObj.save()
							content = {
								"success": True,
								"data":[],
								"msg":_("Password_has_been_changed_successfully_please_login_again")
							}
							return Response(content)
						if not matchcheck:
							validationErrors["oldpassword"]	=	_("Old_password_is_not_correct")
							content = {
							"success": False,
							"data":validationErrors,
							"msg":"Validation errors"
							}
							return Response(content)
				NewUserObj.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":_("Profile_updated_sucessfully")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
            
            

class modelSubscriberPlanList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		subscribedModels = UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_tick_marked=0).all()
		profiles	=	[]
		if subscribedModels:
			for Profile in subscribedModels:
				if Profile.plan_status == 'active' and int(Profile.is_subscription_cancelled) == int(0):
					profile									=	{}
					profile["id"]							=	Profile.id
					profile["social_account"]				=	Profile.model_subscription.social_account
					profile["subscriber_name"]				=	Profile.username
					profile["plan_purchase_date"]			=	Profile.created_at
					if Profile.amount:
						if (decimal.Decimal(Profile.amount) > decimal.Decimal(0)):
							profile["plan_amount"]					=	round(Profile.amount,2)
						else:
							profile["plan_amount"]				=	0.00
					else:
						profile["plan_amount"]				=	0.00
					profile["is_flaged"]					=	Profile.is_flaged
					profile["plan_status"]					=	Profile.plan_status
					profile["plan_type"]					=	Profile.plan_type
					profile["offer_period_time"]			=	Profile.offer_period_time
					profile["offer_period_type"]			=	Profile.offer_period_type
					profiles.append(profile)
				elif Profile.plan_status == 'expire' or int(Profile.is_subscription_cancelled) == int(1):
					profile									=	{}
					profile["id"]							=	Profile.id
					profile["social_account"]				=	Profile.model_subscription.social_account
					profile["subscriber_name"]				=	Profile.username
					profile["plan_purchase_date"]			=	Profile.created_at

					if Profile.amount:
						if (decimal.Decimal(Profile.amount) > decimal.Decimal(0)):
							profile["plan_amount"]					=	round(Profile.amount,2)
						else:
							profile["plan_amount"]				=	0.00
					else:
						profile["plan_amount"]				=	0.00
					profile["is_flaged"]					=	Profile.is_flaged
					profile["plan_status"]					=	"expire"
					profile["plan_type"]					=	Profile.plan_type
					profile["offer_period_time"]			=	Profile.offer_period_time
					profile["offer_period_type"]			=	Profile.offer_period_type
					if(int(Profile.is_subscription_cancelled) == 1):
						profile["expired_date"]					=	Profile.subscription_cancelled_on
					else:
						profile["expired_date"]					=	Profile.expiry_date
						
					profiles.append(profile)
		
		
		content = {
			"success": True,
			"data":profiles,
			"msg":""
		}
		return Response(content)
            

class isFlagedApi(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
	
		flagDetails	=   UserSubscriptionPlan.objects.filter(id=request.POST.get("id")).first()
		flagDetails.is_flaged = 1
		flagDetails.save()


		admin_email			=	""
		SettingDetails = Setting.objects.filter(key="Site.flag").first()
		if SettingDetails:
			admin_email	=	SettingDetails.value
		
		
		model_name			=	flagDetails.model_user.model_name
		subscriber_username =	flagDetails.username
		social_account		=	flagDetails.model_subscription.social_account
		purchased_year		=	str(flagDetails.created_at.year)
		purchased_month		=	str(flagDetails.created_at.month)
		if len(purchased_month) < 2:
			purchased_month	=	"0" + purchased_month
		else:
			purchased_month	=	purchased_month
		purchased_day		=	str(flagDetails.created_at.day)
		purchased_hour		=	str(flagDetails.created_at.hour)
		purchased_minute	=	str(flagDetails.created_at.minute)
		purchased_second	=	str(flagDetails.created_at.second)
		purchased_on		=	purchased_year + "-" + purchased_month + "-" + purchased_day + " " + purchased_hour + ":" + purchased_minute + ":" + purchased_second
	
		currency			=	flagDetails.model_user.default_currency
		amount				=	str(flagDetails.amount)
		emailaction			=	EmailAction.objects.filter(action="flag_email").first()
		emailTemplates		=	EmailTemplates.objects.filter(action ='flag_email').first()
		constant = list()
		data = (emailaction.option.split(','))
		for obj in data:
			constant.append("{"+ obj +"}")
		subject=emailTemplates.subject
		massage_body  	= emailTemplates.body

		website_url		=	settings.FRONT_SITE_URL
		site_title		=	settings.SITETITLE
		rep_Array=[model_name,subscriber_username,social_account,amount,currency,purchased_on]
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
		sendEmail(request,subject,html_content,admin_email)

		content = {
			"success": True,
			"data":[],
			"msg":""
		}
		return Response(content)



class isTickMark(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
	
		tickDetails					=   UserSubscriptionPlan.objects.filter(id=request.POST.get("id")).first()
		tickDetails.is_tick_marked	=	1
		tickDetails.save()


		
		content = {
			"success": True,
			"data":[],
			"msg":""
		}
		return Response(content)
	

	
def isNum(value):
	try:
		int(value)
		return value
	except ValueError:
		return 0
	
def isDecimal(value):
	try:
		decimal.Decimal(value)
		return round(decimal.Decimal(value),2)
	except:
		return 0