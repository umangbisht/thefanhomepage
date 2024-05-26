from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,ModelFollower,ModelNotificationSetting,UserSubscriptionPlan,PrivateFeedModel,TransactionHistory,TipMe,ModelViews,LastPayoutDate,Payout,TopFan,PaymentGatewayErrors,FinalizedTransaction
from apps.cmspages.models import CmsPage,CmsPageDescription
from apps.newsletters.models import NewsletterSubscriber
from apps.api.models import ReportReasonModel,currencyRate
from apps.slider.models import SliderImage
from apps.supports.models import Support
from apps.blocks.models import Block,BlockDescription
from apps.dropdownmanger.models import DropDownManagerDescription,DropDownManager
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
from apps.settings.models import Setting
import decimal
import os
import datetime, calendar
import requests
from requests.auth import HTTPBasicAuth
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
from dateutil.relativedelta import relativedelta
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
from datetime import date,timedelta
from apps.common.views import commonMail



class TipMeApi(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
			
		translation.activate(user_language)
		
		validationErrors	=	{}
		if request.POST.get("model_user_id") == None or request.POST.get("model_user_id") == "":
			validationErrors["model_user_id"]	=	_("The_model_id_field_is_required")
			
		if request.POST.get("currency") == None or request.POST.get("currency") == "" or request.POST.get("currency")=="null":
			validationErrors["currency"]	=	_("The_currency_field_is_required")
			
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		if request.POST.get("amount") == None or request.POST.get("amount") == "":
			validationErrors["amount"]	=	_("The_amount_field_is_required")
			
		if request.POST.get("message") == None or request.POST.get("message") == "":
			validationErrors["message"]	=	_("The_message_field_is_required")
			
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
			 
		if request.user.id:
			loginuserid	=	request.user.id
		else:
			loginuserid	=	1
			
		if not validationErrors:
			amount  = 	decimal.Decimal(request.POST.get("amount",0))
			amount	=	round(amount,2)
			
			modelDetails	= 	User.objects.filter(id=request.POST.get('model_user_id')).first()
			order_id		=	random.randint(1000000000000000000,9223372036854775806)
			
			context	=	{"model_name":modelDetails.model_name,"amount":amount,"currency":modelDetails.default_currency,"order_id":order_id,"card_number":request.POST.get("cardNumber",""),"exp_year":request.POST.get("expiry_year",""),"exp_month":request.POST.get("expiry_month",""),"cvc":request.POST.get("cvv",""),"holder":request.POST.get("account_holder","")}
			address = settings.PAYMENT_GATEWAY_CREATE_PAYMENT_PATH
			r	=	requests.post(address, data=context)
			response		=	json.loads(r.content.decode('utf-8'))
			transaction_id	=	""
			if response["status"] and response["status"] == "success":
				if response["response"] and response["response"]["status"] == "approved":
					transaction_id	=	response["response"]["id"]
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

					paymentErroraObj  									= 	PaymentGatewayErrors()
					if(int(loginuserid) != 0):
						paymentErroraObj.user_id 								=   loginuserid
					
					paymentErroraObj.username 						= 	""
						
					paymentErroraObj.email 								= 	request.POST.get("email",'')
					paymentErroraObj.amount 							= 	request.POST.get("amount",'')
					paymentErroraObj.price_in_model_currency 			= 	priceInModelCurrency
					paymentErroraObj.plan_type_id 						= 	""
					paymentErroraObj.model_user_id 						= 	request.POST.get("model_user_id")
					paymentErroraObj.subscription_desc 					= 	""
					paymentErroraObj.expiry_date 							= 	None
					paymentErroraObj.plan_status 							= 	""
					paymentErroraObj.plan_validity						=	""
					paymentErroraObj.transaction_id						=	""
					paymentErroraObj.transaction_payment_id				=	""
					
					
					paymentErroraObj.user_subscription_plan_description				=	""
					paymentErroraObj.plan_type				=	""
					paymentErroraObj.offer_period_time		=	""
					paymentErroraObj.offer_period_type		=	""
					paymentErroraObj.is_discount_enabled		=	0	
					paymentErroraObj.discount					=	0		
					paymentErroraObj.from_discount_date		=	""	
					paymentErroraObj.to_discount_date			=	""		
					paymentErroraObj.is_permanent_discount	=	0		
					paymentErroraObj.is_apply_to_rebills		=	0	
					paymentErroraObj.planprice				=	0		
					paymentErroraObj.discounted_price			=	0
					paymentErroraObj.response				=	r.content
					paymentErroraObj.transaction_type		=	"tips"
					paymentErroraObj.save()
					content = {
						"success": False,
						"data":[],
						"msg":"Your payment has been failed. Please try again."
					}
					return Response(content)
			else:

				priceInModelCurrency = 0						

				paymentErroraObj  									= 	PaymentGatewayErrors()
				if(int(loginuserid) != 0):
					paymentErroraObj.user_id 								=   loginuserid
					
				paymentErroraObj.username 						= 	""
					
				paymentErroraObj.email 								= 	request.POST.get("email",'')
				paymentErroraObj.amount 							= 	request.POST.get("amount",'')
				paymentErroraObj.price_in_model_currency 			= 	priceInModelCurrency
				paymentErroraObj.plan_type_id 						= 	""
				paymentErroraObj.model_user_id 						= 	request.POST.get("model_user_id")
				paymentErroraObj.subscription_desc 					= 	""
				paymentErroraObj.expiry_date 							= 	None
				paymentErroraObj.plan_status 							= 	""
				paymentErroraObj.plan_validity						=	""
				paymentErroraObj.transaction_id						=	""
				paymentErroraObj.transaction_payment_id				=	""
				
				paymentErroraObj.user_subscription_plan_description				=	""
				paymentErroraObj.plan_type				=	""
				paymentErroraObj.offer_period_time		=	""
				paymentErroraObj.offer_period_type		=	""
				paymentErroraObj.is_discount_enabled		=	0	
				paymentErroraObj.discount					=	0		
				paymentErroraObj.from_discount_date		=	""	
				paymentErroraObj.to_discount_date			=	""		
				paymentErroraObj.is_permanent_discount	=	0		
				paymentErroraObj.is_apply_to_rebills		=	0	
				paymentErroraObj.planprice				=	0		
				paymentErroraObj.discounted_price			=	0
				paymentErroraObj.response				=	r.content
				paymentErroraObj.transaction_type		=	"tips"
				paymentErroraObj.save()
				content = {
					"success": False,
					"data":[],
					"msg":_("Your payment has been failed. Please try again.")
				}
				return Response(content)
				
				
			modelDetails=User.objects.filter(id=request.POST.get('model_user_id')).first()
			tipInfo = request.POST.get("currency")
			#priceDetail = currencyRate.objects.filter(from_currency=tipInfo).filter(to_currency=modelDetails.default_currency).first()
			priceInModelCurrency = 0
			# return HttpResponse(priceInModelCurrency)
			Obj							=	TipMe()
			Obj.model_user_id			=	request.POST.get('model_user_id')
			if(int(loginuserid) != 0):
				Obj.user_id		            =	loginuserid
				
			Obj.amount		            =	request.POST.get('amount')
			Obj.currency        		=	request.POST.get("currency")
			Obj.message            		=	request.POST.get("message")
			Obj.price_in_model_currency = 	priceInModelCurrency
			Obj.email            		=	request.POST.get("email")
			Obj.save()

			transactionObj										=	TransactionHistory()
			if(int(loginuserid) != 0):
				transactionObj.user_id								=	loginuserid
				
			transactionObj.model_id								=	Obj.model_user_id
			transactionObj.amount								=	Obj.amount
			transactionObj.price_in_model_currency				=	priceInModelCurrency
			transactionObj.transaction_date						=	datetime.date.today()
			#transactionObj.model_subscription_id				=	'0'
			#transactionObj.plan_id								=	'0'
			transactionObj.tips_id								=	Obj.id
			transactionObj.transaction_type						= 	'tips'
			transactionObj.payment_type							= 	'tips'
			transactionObj.currency     						= 	Obj.currency
			transactionObj.transaction_id						=	transaction_id
			transactionObj.status								=	'success'
			transactionObj.tip_email							=	Obj.email
			
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
			arrayData = {}
			arrayData["currency"]   =   Obj.currency
			arrayData["amount"]     =   Obj.amount

			
			tipeDetails 					= 	TipMe.objects.filter(id=Obj.id).first()
			tipeDetails.transaction_id		=	transactionObj.transaction_id
			tipeDetails.save()
			commonMail(request, "TIP_RECIVED",Obj.model_user_id, Obj.email,arrayData )

			content = {
				"success": True,
				"data":[],
				"transaction_id":transaction_id,
				"amount":amount,
				"in_currency":modelDetails.default_currency,
				"msg":_("Tips_successfully_saved")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)	
			
class TipMeApifinalize(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
			
		translation.activate(user_language)
		
		validationErrors	=	{}
		if request.POST.get("model_user_id") == None or request.POST.get("model_user_id") == "":
			validationErrors["model_user_id"]	=	_("The_model_id_field_is_required")
			
		if request.POST.get("currency") == None or request.POST.get("currency") == "" or request.POST.get("currency")=="null":
			validationErrors["currency"]	=	_("The_currency_field_is_required")
			
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	_("The_email_field_is_required")
		if request.POST.get("amount") == None or request.POST.get("amount") == "":
			validationErrors["amount"]	=	_("The_amount_field_is_required")
			
		if request.POST.get("message") == None or request.POST.get("message") == "":
			validationErrors["message"]	=	_("The_message_field_is_required")
			
		if request.POST.get("payment_id") == None or request.POST.get("payment_id") == "":
			validationErrors["payment_id"]	=	_("The_payment_id_field_is_required")
			
			
		if request.user.id:
			loginuserid	=	request.user.id
		else:
			loginuserid	=	1
			
			
		if not validationErrors:
			payment_id= request.POST.get("payment_id",'')
			authorize_data= request.POST.get("authorize_data",'')
			amount  = 	decimal.Decimal(request.POST.get("amount",0))
			amount	=	round(amount,2)
			
			modelDetails	= 	User.objects.filter(id=request.POST.get('model_user_id')).first()
			order_id		=	random.randint(1000000000000000000,9223372036854775806)
			
			FinalizedTransactionInfo	= 	FinalizedTransaction.objects.filter(transaction_id=payment_id).first()
			if FinalizedTransactionInfo:
				if(FinalizedTransactionInfo.status == "approved"):
					transaction_id			=	payment_id
					transaction_payment_id	=	payment_id
					FinalizedTransaction.objects.filter(transaction_id=transaction_id).all().delete()
				else:
					priceInModelCurrency = 0						

					paymentErroraObj  									= 	PaymentGatewayErrors()
					if(int(loginuserid) != 0):
						paymentErroraObj.user_id 								=   loginuserid
						
					paymentErroraObj.username 						= 	""
						
					paymentErroraObj.email 								= 	request.POST.get("email",'')
					paymentErroraObj.amount 							= 	request.POST.get("amount",'')
					paymentErroraObj.price_in_model_currency 			= 	priceInModelCurrency
					paymentErroraObj.plan_type_id 						= 	""
					paymentErroraObj.model_user_id 						= 	request.POST.get("model_user_id")
					paymentErroraObj.subscription_desc 					= 	""
					paymentErroraObj.expiry_date 							= 	None
					paymentErroraObj.plan_status 							= 	""
					paymentErroraObj.plan_validity						=	""
					paymentErroraObj.transaction_id						=	""
					paymentErroraObj.transaction_payment_id				=	""
					
					
					paymentErroraObj.user_subscription_plan_description				=	""
					paymentErroraObj.plan_type				=	""
					paymentErroraObj.offer_period_time		=	""
					paymentErroraObj.offer_period_type		=	""
					paymentErroraObj.is_discount_enabled		=	0	
					paymentErroraObj.discount					=	0		
					paymentErroraObj.from_discount_date		=	""	
					paymentErroraObj.to_discount_date			=	""		
					paymentErroraObj.is_permanent_discount	=	0		
					paymentErroraObj.is_apply_to_rebills		=	0	
					paymentErroraObj.planprice				=	0		
					paymentErroraObj.discounted_price			=	0
					paymentErroraObj.response				=	FinalizedTransactionInfo.errors
					paymentErroraObj.transaction_type		=	"tips"
					paymentErroraObj.save()
					content = {
						"success": False,
						"data":[],
						"msg":"Your payment has been failed. Please try again."
					}
					return Response(content)
			else:
				priceInModelCurrency = 0						

				paymentErroraObj  									= 	PaymentGatewayErrors()
				if(int(loginuserid) != 0):
					paymentErroraObj.user_id 								=   loginuserid
					
				paymentErroraObj.username 						= 	""
					
				paymentErroraObj.email 								= 	request.POST.get("email",'')
				paymentErroraObj.amount 							= 	request.POST.get("amount",'')
				paymentErroraObj.price_in_model_currency 			= 	priceInModelCurrency
				paymentErroraObj.plan_type_id 						= 	""
				paymentErroraObj.model_user_id 						= 	request.POST.get("model_user_id")
				paymentErroraObj.subscription_desc 					= 	""
				paymentErroraObj.expiry_date 							= 	None
				paymentErroraObj.plan_status 							= 	""
				paymentErroraObj.plan_validity						=	""
				paymentErroraObj.transaction_id						=	""
				paymentErroraObj.transaction_payment_id				=	""
				
				
				paymentErroraObj.user_subscription_plan_description				=	""
				paymentErroraObj.plan_type				=	""
				paymentErroraObj.offer_period_time		=	""
				paymentErroraObj.offer_period_type		=	""
				paymentErroraObj.is_discount_enabled		=	0	
				paymentErroraObj.discount					=	0		
				paymentErroraObj.from_discount_date		=	""	
				paymentErroraObj.to_discount_date			=	""		
				paymentErroraObj.is_permanent_discount	=	0		
				paymentErroraObj.is_apply_to_rebills		=	0	
				paymentErroraObj.planprice				=	0		
				paymentErroraObj.discounted_price			=	0
				paymentErroraObj.response				=	"Transaction Not Found"
				paymentErroraObj.transaction_type		=	"tips"
				paymentErroraObj.save()
				content = {
					"success": False,
					"data":[],
					"msg":"Your payment has been failed. Please try again."
				}
				return Response(content)
				
				
			modelDetails=User.objects.filter(id=request.POST.get('model_user_id')).first()
			tipInfo = request.POST.get("currency")
			#priceDetail = currencyRate.objects.filter(from_currency=tipInfo).filter(to_currency=modelDetails.default_currency).first()
			priceInModelCurrency = 0
			# return HttpResponse(priceInModelCurrency)
			Obj							=	TipMe()
			Obj.model_user_id			=	request.POST.get('model_user_id')
			if(int(loginuserid) != 0):
				Obj.user_id		            =	loginuserid
				
			Obj.amount		            =	request.POST.get('amount')
			Obj.currency        		=	request.POST.get("currency")
			Obj.message            		=	request.POST.get("message")
			Obj.price_in_model_currency = 	priceInModelCurrency
			Obj.email            		=	request.POST.get("email")
			Obj.save()

			transactionObj										=	TransactionHistory()
			if(int(loginuserid) != 0):
				transactionObj.user_id								=	loginuserid
				
			transactionObj.model_id								=	Obj.model_user_id
			transactionObj.amount								=	Obj.amount
			transactionObj.price_in_model_currency				=	priceInModelCurrency
			transactionObj.transaction_date						=	datetime.date.today()
			#transactionObj.model_subscription_id				=	'0'
			#transactionObj.plan_id								=	'0'
			transactionObj.tips_id								=	Obj.id
			transactionObj.transaction_type						= 	'tips'
			transactionObj.payment_type							= 	'tips'
			transactionObj.currency     						= 	Obj.currency
			transactionObj.transaction_id						=	transaction_id
			transactionObj.status								=	'success'
			transactionObj.tip_email							=	Obj.email
			
			
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
			arrayData = {}
			arrayData["currency"]   =   Obj.currency
			arrayData["amount"]     =   Obj.amount

			
			tipeDetails 					= 	TipMe.objects.filter(id=Obj.id).first()
			tipeDetails.transaction_id		=	transactionObj.transaction_id
			tipeDetails.save()
			commonMail(request, "TIP_RECIVED",Obj.model_user_id, Obj.email,arrayData )

			content = {
				"success": True,
				"data":[],
				"transaction_id":transaction_id,
				"amount":amount,
				"in_currency":modelDetails.default_currency,
				"msg":_("Tips_successfully_saved")
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)	

class modelDashboardBiggestFan(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		results = TransactionHistory.objects.filter(model_id=request.user.id).exclude(payment_type='refunds').filter(status="success").filter(user__is_deleted=0).values('user_subscription__email','user__id','user__model_name','tip_email').annotate(total_spend=Sum('amount')).order_by("-total_spend").all()[:1]
		allSubList	=	[]
		if results:
			for sub in results:
				fanInfo	=	TransactionHistory.objects.filter(user_id=sub["user__id"]).filter(model_id=request.user.id).filter(status="success").order_by("id").first()
			
				sub_data								=	{}
				if sub["user_subscription__email"]:
					email						=	sub["user_subscription__email"]
					username 					=	email.split('@')[0]
					sub_data["name_user"]		=	username
				else:
					email						=	sub["tip_email"]
					username 					=	email.split('@')[0]
					sub_data["name_user"]		=	username
				if sub["total_spend"]:
					if (decimal.Decimal(sub["total_spend"]) > decimal.Decimal(0)):
						sub_data["total_spend"]				=	round(sub["total_spend"],2)
					else:
						sub_data["total_spend"]				=	0
				else:
					sub_data["total_spend"]				=	0
				sub_data["user_id"]						=	sub["user__id"]
				sub_data["in_currency"]					=	request.user.default_currency
				sub_data["join_on"]						=	fanInfo.created_at
				allSubList.append(sub_data)
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"msg":_("")
						}
		else:
			content = {
				"success": False,
				"data":[],
				
				"msg":_("No_fans_found")
			}	
		return Response(content)
		
		
		
class modelDashboardTopTenBiggestFan(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		results = TransactionHistory.objects.filter(model_id=request.user.id).exclude(payment_type='refunds').filter(status="success").filter(user__is_deleted=0).values('user_subscription__email','user__id','user__model_name','tip_email').annotate(total_spend=Sum('amount')).order_by("-total_spend").all()[:10]
		allSubList	=	[]
		if results:
			for sub in results:
				fanInfo	=	TransactionHistory.objects.filter(user_id=sub["user__id"]).filter(model_id=request.user.id).filter(status="success").order_by("id").first()
			
				sub_data								=	{}
				if sub["user_subscription__email"]:
					email						=	sub["user_subscription__email"]
					username 					=	email.split('@')[0]
					sub_data["name_user"]		=	username
				else:
					email						=	sub["tip_email"]
					username 					=	email.split('@')[0]
					sub_data["name_user"]		=	username
				if sub["total_spend"]:
					if (decimal.Decimal(sub["total_spend"]) > decimal.Decimal(0)):
						sub_data["total_spend"]					=	round(sub["total_spend"],2)
					else:
						sub_data["total_spend"]				=	0
				else:
					sub_data["total_spend"]				=	0
				sub_data["user_id"]						=	sub["user__id"]
				sub_data["in_currency"]					=	request.user.default_currency
				sub_data["join_on"]						=	fanInfo.created_at
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"msg":_("Top_fans_listed_successfully")
						}
		else:
			content = {
				"success": False,
				"data":[],
				
				"msg":_("No_fans_found")
			}	
		return Response(content)
		
class modelRevenue(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		date_str = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
		date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')	
		
		start_of_week = date_obj - timedelta(days=date_obj.weekday()) 	# Monday
		end_of_week = start_of_week + timedelta(days=6)  				# Sunday
		start_of_week = str(start_of_week.date())+" 00:00:00"
		end_of_week = str(end_of_week.date())+" 23:59:59"

		weekTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).all().aggregate(Sum('amount'))
		weekTotal = weekTransaction['amount__sum']
		if weekTotal:
			weekTransaction_commission	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).all().aggregate(Sum('commission'))
			weekTotal_commission = weekTransaction_commission['commission__sum']
			if (decimal.Decimal(weekTotal_commission) > decimal.Decimal(0)):
				weekTotal_commission = round(weekTotal_commission,2)
			else:
				weekTotal_commission = 0
				
			if (decimal.Decimal(weekTotal) > decimal.Decimal(0)):
				weekTotal = round(decimal.Decimal(weekTotal)-decimal.Decimal(weekTotal_commission),2)
			else:
				weekTotal = 0
		else:
			weekTotal = 0

		year = date.today().year
		month =	date.today().month
		monthStartDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-01 00:00:00"
		endDate	=	calendar.monthrange(year, month)[1]
		endDate	=	str(endDate)
		monthEndDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+endDate +" 23:59:59"
		
		monthTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
		monthTotal = monthTransaction['amount__sum']
		if monthTotal:
			monthTransaction_commission	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().aggregate(Sum('commission'))
			monthTotal_commission = monthTransaction_commission['commission__sum']
			if monthTotal_commission:
				if (decimal.Decimal(monthTotal_commission) > decimal.Decimal(0)):
					monthTotal_commission = round(monthTotal_commission,2)
				else:
					monthTotal_commission = 0

			if (decimal.Decimal(monthTotal) > decimal.Decimal(0)):
				monthTotal = round(decimal.Decimal(monthTotal)-decimal.Decimal(monthTotal_commission),2)
			else:
				monthTotal = 0
		else:
			monthTotal = 0


		yearStartDate 	= str(datetime.datetime.now().year)+"-01-01 00:00:00"
		endDate	=	calendar.monthrange(year, month)[1]
		endDate	=	str(endDate)
		yearEndDate 	= str(datetime.datetime.now().year)+"-12-"+endDate+ " 23:59:59"
		
		yearTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).all().aggregate(Sum('amount'))
		yearTotal = yearTransaction['amount__sum']
		if yearTotal:
			yearTransaction_commission	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).all().aggregate(Sum('commission'))
			yearTotal_commission = yearTransaction_commission['commission__sum']
			if yearTotal_commission:
				if (decimal.Decimal(yearTotal_commission) > decimal.Decimal(0)):
					yearTotal_commission = round(yearTotal_commission,2)
				else:
					yearTotal_commission = 0
		
			if (decimal.Decimal(yearTotal) > decimal.Decimal(0)):
				yearTotal = round(decimal.Decimal(yearTotal)-decimal.Decimal(yearTotal_commission),2)
			else:
				yearTotal = 0
		else:
			yearTotal = 0


		allTimeTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).all().aggregate(Sum('amount'))
		allTimeTotal = allTimeTransaction['amount__sum']
		if allTimeTotal:
			allTimeTransaction_commission	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).all().aggregate(Sum('commission'))
			allTimeTotal_commission = allTimeTransaction_commission['commission__sum']
			if allTimeTotal_commission:
				if (decimal.Decimal(allTimeTotal_commission) > decimal.Decimal(0)):
					allTimeTotal_commission = round(allTimeTotal_commission,2)
				else:
					allTimeTotal_commission = 0
		
			if (decimal.Decimal(allTimeTotal) > decimal.Decimal(0)):
				allTimeTotal = round(decimal.Decimal(allTimeTotal)-decimal.Decimal(allTimeTotal_commission),2)
			else:
				allTimeTotal = 0
		else:
			allTimeTotal = 0

		content = {
			"success": True,
			"weekTotal":weekTotal,
			"monthTotal":monthTotal,
			"yearTotal":yearTotal,
			"allTimeTotal":allTimeTotal,
			"in_currency":request.user.default_currency,
			"msg":""
		}
		return Response(content)	
		
class modelBasicInfo(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		ModelImage = ModelImages.objects.filter(user_id=request.user.id).all()
		if ModelImage:
			profile_image					=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage[0].image_url
		else:
			profile_image					=	""
					
		totalFollowers = ModelFollower.objects.filter(model_id=request.user.id).all().count()
		ModelViewscount = ModelViews.objects.filter(model_id=request.user.id).all().count()
		PayoutDate = LastPayoutDate.objects.filter(model_id=request.user.id).order_by("-id").first()
		
		before21days 		=	PayoutDate.last_payout_date-timedelta(days=21)
		before14days 		=	PayoutDate.last_payout_date-timedelta(days=14)
		
		PayoutAmount = TransactionHistory.objects.exclude(payment_type='refunds').filter(model_id=request.user.id).filter(status="success").filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))

		if PayoutAmount['amount__sum']:
			if (decimal.Decimal(PayoutAmount['amount__sum']) > decimal.Decimal(0)):
				PayoutCommissionTotal	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(model_id=request.user.id).filter(status="success").filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
				commission_amount  = PayoutCommissionTotal['commission__sum']
				next_payout_amount =PayoutAmount['amount__sum'] - commission_amount
				next_payout_amount = round(next_payout_amount,2)
			else:
				next_payout_amount = 0
		else:
			next_payout_amount = 0
			
		userDetail	=	{
			"slug":request.user.slug,"email":request.user.email,"user_role_id":request.user.user_role_id,"first_name":request.user.first_name,"last_name":request.user.last_name,"model_name":request.user.model_name,"user_id":request.user.id,"default_currency":request.user.default_currency,"rank":request.user.rank,"rank_status":request.user.rank_status,"profile_image":profile_image,"is_homepage_profile":request.user.is_homepage_profile,"total_followers":totalFollowers,"payment_date":PayoutDate.last_payout_date,"next_payout_start_date":PayoutDate.last_payout_date - datetime.timedelta(days=21),"next_payout_end_date":PayoutDate.last_payout_date - datetime.timedelta(days=15),"next_payout_amount":next_payout_amount,"profile_view_count":ModelViewscount
		}
				
		content = {
			"success": True,
			"details":userDetail,
			"msg":""
		}
		return Response(content)

class modelTransactionHistory(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		
		totalGrossRevenue	=	0
		totalNetRevenue	=	0
		allTimeTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id)

		user_role = request.user.user_role_id
		DB = TransactionHistory.objects

		DB			=	DB.filter(model_id=request.user.id)
		if request.GET.get('registered_from'):
			DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
			allTimeTransaction	=	allTimeTransaction.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		if request.GET.get('registered_to'):
			DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
			allTimeTransaction	=	allTimeTransaction.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
		if request.GET.get('username'):
			DB 			= DB.filter(Q(user_subscription__username__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')) | Q(tip_email__icontains=request.GET.get('username')))
			allTimeTransaction	=	allTimeTransaction.filter(Q(user_subscription__username__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')) | Q(tip_email__icontains=request.GET.get('username')))
		
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
		

		allTimeTransaction1	=	allTimeTransaction.all().aggregate(Sum('amount'))
		allTimeTotal = allTimeTransaction1['amount__sum']
		
		allTimeTransaction_commission	=	allTimeTransaction.all().aggregate(Sum('commission'))
		allTimeTotal_commission = allTimeTransaction_commission['commission__sum']
		
	
		if allTimeTotal:
			if allTimeTotal_commission:
				totalGrossRevenue	=	round(decimal.Decimal(allTimeTotal),2)
				totalNetRevenue		=	round(decimal.Decimal(allTimeTotal)-decimal.Decimal(allTimeTotal_commission),2)
				
			else:
				totalGrossRevenue	=	round(decimal.Decimal(allTimeTotal),2)
				totalNetRevenue		=	round(decimal.Decimal(allTimeTotal),2)
		
		
		if results:
			for sub in results:
				sub_data								=	{}
				sub_data["offer_name"]					=	""
				sub_data["offer_description"]			=	""
				sub_data["social_account"]				=	""
				if sub.transaction_type=="subscription":
					sub_data["social_account"]				=	sub.model_subscription.social_account
					sub_data["offer_name"]					=	sub.user_subscription.offer_name
					sub_data["offer_description"]			=	sub.user_subscription.offer_description
				
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
				else:
					sub_data["billed"]						=	"Tips"
					
				if sub.transaction_type=="tips":
					sub_data["subscriber_name"]		=	sub.tip_email
				else:
					sub_data["subscriber_name"]		=	sub.user_subscription.username
					
				sub_data["status"]						=	sub.status
				sub_data["transaction_date"]			=	sub.created_at
				sub_data["transaction_id"]				=	sub.transaction_id
				if sub.transaction_type !="tips":
					if(sub.payment_type == "rebills"):
						sub_data["descriptions"]				=	"Rebills"
					elif(sub.payment_type == "tips"):
						sub_data["descriptions"]				=	"Tips"
					elif(sub.payment_type == "joins"):
						sub_data["descriptions"]				=	"Joins"
				elif sub.transaction_type=="tips":
					sub_data["descriptions"]				=	"Tips"
				
				sub_data["id"]							=	sub.id
				if sub.amount != "" or sub.amount != None:
					if (decimal.Decimal(sub.amount) > decimal.Decimal(0)):
						sub_data["gross_revenue"]				=	round(sub.amount,2)
					else:
						sub_data["gross_revenue"]		=	0
				else:
					sub_data["gross_revenue"]		=	0
				sub_data["in_currency"]				=	request.user.default_currency
				
				sub_data["net_revenue"]				=	round(decimal.Decimal(sub.amount)-decimal.Decimal(sub.commission),2)
				
		
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"totalGrossRevenue":totalGrossRevenue,
						"totalNetRevenue":totalNetRevenue,
						"msg":_("Transactions_listed_successfully")
						}
		else:
			content = {
				"success": True,
				"data":[],
				"totalGrossRevenue":0,
				"totalNetRevenue":0,
				"msg":_("")
			}	
		return Response(content)
		
class modelPayoutHistory(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		user_role = request.user.user_role_id
		DB = Payout.objects.filter(is_paid=1)

		DB			=	DB.filter(model_id=request.user.id)
		if request.GET.get('registered_from'):
			DB 			= DB.filter(created_at__gte=request.GET.get('registered_from')+" 00:00:00")
		if request.GET.get('registered_to'):
			DB 			= DB.filter(created_at__lte=request.GET.get('registered_to')+" 23:59:59")
			
		#if request.GET.get('username'):
			#DB 			= DB.filter(Q(user__username__icontains=request.GET.get('username')) | Q(user__email__icontains=request.GET.get('username')) | Q(transaction_id__icontains=request.GET.get('username')) | Q(tip_email__icontains=request.GET.get('username')))
		
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
			for sub in results:
				sub_data								=	{}
				sub_data["id"]								=	sub.id
				sub_data["payment_date"]					=	sub.payment_date
				sub_data["payment_type"]					=	sub.payment_method
				sub_data["start_date"]						=	sub.start_date
				sub_data["end_date"]						=	sub.end_date
				if sub.net_revenue:
					if (decimal.Decimal(sub.net_revenue) > decimal.Decimal(0)):
						sub_data["net_revenue"]						=	round(sub.net_revenue,2)
					else:
						sub_data["net_revenue"]					=	0
				else:
					sub_data["net_revenue"]					=	0

				if sub.gross_revenue:
					if (decimal.Decimal(sub.gross_revenue) > decimal.Decimal(0)):
						sub_data["gross_revenue"]					=	round(sub.gross_revenue,2)
					else:
						sub_data["gross_revenue"]				=	0
				else:
					sub_data["gross_revenue"]				=	0

				if sub.commission_amount:
					if (decimal.Decimal(sub.commission_amount) > decimal.Decimal(0)):
						sub_data["commission_amount"]				=	round(sub.commission_amount,2)
					else:
						sub_data["commission_amount"]			=	0
				else:
					sub_data["commission_amount"]			=	0
				sub_data["status"]							=	'Successfull'

				if sub.rebill_gross_revenue:
					if (decimal.Decimal(sub.rebill_gross_revenue) > decimal.Decimal(0)):
						sub_data["rebill_gross_revenue"]			=	round(sub.rebill_gross_revenue,2)
					else:
						sub_data["rebill_gross_revenue"]		=	0
				else:
					sub_data["rebill_gross_revenue"]		=	0

				if sub.rebill_commission:
					if (decimal.Decimal(sub.rebill_commission) > decimal.Decimal(0)):
						sub_data["rebill_commission"]				=	round(sub.rebill_commission,2)
					else:
						sub_data["rebill_commission"]			=	0
				else:
					sub_data["rebill_commission"]			=	0
				
				if sub.rebill_net_revenue:
					if (decimal.Decimal(sub.rebill_net_revenue) > decimal.Decimal(0)):
						sub_data["rebill_net_revenue"]				=	round(sub.rebill_net_revenue,2)
					else:
						sub_data["rebill_net_revenue"]			=	0
				else:
					sub_data["rebill_net_revenue"]			=	0
				
				if sub.join_gross_revenue:
					if (decimal.Decimal(sub.join_gross_revenue) > decimal.Decimal(0)):
						sub_data["join_gross_revenue"]				=	round(sub.join_gross_revenue,2)
					else:
						sub_data["join_gross_revenue"]			=	0	
				else:
					sub_data["join_gross_revenue"]			=	0	

				if sub.join_net_revenue:
					if (decimal.Decimal(sub.join_net_revenue) > decimal.Decimal(0)):
						sub_data["join_net_revenue"]				=	round(sub.join_net_revenue,2)
					else:
						sub_data["join_net_revenue"]			=	0
				else:
					sub_data["join_net_revenue"]			=	0

				if sub.join_commission:
					if (decimal.Decimal(sub.join_commission) > decimal.Decimal(0)):
						sub_data["join_commission"]					=	round(sub.join_commission,2)
					else:
						sub_data["join_commission"]				=	0
				else:
					sub_data["join_commission"]				=	0

				if sub.tip_gross_revenue:
					if (decimal.Decimal(sub.tip_gross_revenue) > decimal.Decimal(0)):
						sub_data["tip_gross_revenue"]				=	round(sub.tip_gross_revenue,2)
					else:
						sub_data["tip_gross_revenue"]			=	0
				else:
					sub_data["tip_gross_revenue"]			=	0

				if sub.tip_net_revenue:
					if (decimal.Decimal(sub.tip_net_revenue) > decimal.Decimal(0)):
						sub_data["tip_net_revenue"]					=	round(sub.tip_net_revenue,2)
					else:
						sub_data["tip_net_revenue"]					=	0
				else:
					sub_data["tip_net_revenue"]					=	0
				
				if sub.tip_commission:
					if (decimal.Decimal(sub.tip_commission) > decimal.Decimal(0)):
						sub_data["tip_commission"]					=	round(sub.tip_commission,2)
					else:
						sub_data["tip_commission"]					=	0
				else:
					sub_data["tip_commission"]					=	0
					
					
					
				if sub.refunds_gross_revenue:
					if (decimal.Decimal(sub.refunds_gross_revenue) > decimal.Decimal(0)):
						sub_data["refunds_gross_revenue"]				=	round(sub.refunds_gross_revenue,2)
					else:
						sub_data["refunds_gross_revenue"]			=	0
				else:
					sub_data["refunds_gross_revenue"]			=	0

				if sub.refunds_net_revenue:
					if (decimal.Decimal(sub.refunds_net_revenue) > decimal.Decimal(0)):
						sub_data["refunds_net_revenue"]					=	round(sub.refunds_net_revenue,2)
					else:
						sub_data["refunds_net_revenue"]					=	0
				else:
					sub_data["refunds_net_revenue"]					=	0
				
				if sub.refunds_commission:
					if (decimal.Decimal(sub.refunds_commission) > decimal.Decimal(0)):
						sub_data["refunds_commission"]					=	round(sub.refunds_commission,2)
					else:
						sub_data["refunds_commission"]					=	0
				else:
					sub_data["refunds_commission"]					=	0
					
					
					
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":""
						}
		else:
			content = {
				"success": True,
				"data":[],
				"msg":_("")
			}	
		return Response(content)
		
class modelSplitData(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		if (request.GET.get('filter_by') and request.GET.get('filter_by') == 'week'):
			date_str = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
			date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')	
			
			start_of_week = date_obj - timedelta(days=date_obj.weekday()) 	# Monday
			end_of_week = start_of_week + timedelta(days=6)  				# Sunday
			start_of_week = str(start_of_week.date())+" 00:00:00"
			end_of_week = str(end_of_week.date())+" 23:59:59"

			recurringPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='recurring').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).count()
			
			oneTimePlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='one_time').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).count()
		elif request.GET.get('filter_by') and request.GET.get('filter_by') == 'month':	
			year = date.today().year
			month =	date.today().month
			monthStartDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-01 00:00:00"
			endDate	=	calendar.monthrange(year, month)[1]
			endDate	=	str(endDate)
			monthEndDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+endDate +" 23:59:59"
			
			recurringPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='recurring').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).count()
			
			oneTimePlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='one_time').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).count()
			
		elif request.GET.get('filter_by') and request.GET.get('filter_by') == 'year':	
			yearStartDate 	= str(datetime.datetime.now().year)+"-01-01 00:00:00"
			endDate	=	calendar.monthrange(year, month)[1]
			endDate	=	str(endDate)
			yearEndDate 	= str(datetime.datetime.now().year)+"-12-"+endDate+ " 23:59:59"
			
			recurringPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='recurring').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).count()
			
			oneTimePlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='one_time').filter(is_subscription_cancelled = 0).filter(plan_status="active").filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).count()
			
		else:	
			recurringPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='recurring').filter(is_subscription_cancelled = 0).filter(plan_status="active").count()
			
			oneTimePlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_type='one_time').filter(is_subscription_cancelled = 0).filter(plan_status="active").count()

		content = {
			"success": True,
			"recurringPlans":recurringPlans,
			"oneTimePlans":oneTimePlans,
			"msg":""
		}
		return Response(content)
		
class modelActiveSubscribers(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		totalActiveCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_subscription_cancelled = 0).filter(plan_status="active").all().count()
		totalExpiredCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire")).all().count()
		totalReportedCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_flaged=1).all().count()
					
		DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_subscription_cancelled = 0).filter(plan_status="active")
		
		if request.GET.get('username'):
			DB 			= DB.filter(username__icontains=request.GET.get('username'))
			
		if request.GET.get('social_account'):
			DB 			= DB.filter(model_subscription__social_account=request.GET.get('social_account'))
		
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
			for sub in results:
				sub_data								=	{}
				totalSpend	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(model_subscription_id=sub.model_subscription_id).filter(user_id=sub.user_id).all().aggregate(Sum('amount'))
			
				if(sub.plan_type == "recurring"):
					if(str(sub.offer_period_type) == "week"):
						billed	=	"Weekly"
					if(str(sub.offer_period_type) == "month"):
						billed	=	"Monthly"
					if(str(sub.offer_period_type) == "year"):
						billed	=	"Yearly"
				else:
					billed	=	"One Time"
				
				
				sub_data["billed"]						=	billed
			
				sub_data["id"]							=	sub.id
				sub_data["offer_name"]					=	sub.offer_name
				sub_data["offer_description"]			=	sub.offer_description
				
				sub_data["user_name"]					=	sub.username
				sub_data["joined_on"]					=	sub.created_at
				sub_data["expiry_date"]					=	sub.expiry_date
				sub_data["billed"]						=	billed
				sub_data["status"]						=	"Active"
				sub_data["type"]						=	sub.model_subscription.social_account
				if totalSpend['amount__sum']:
					if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
						sub_data["total_spend"]				=	round(totalSpend['amount__sum'],2)
					else:
						sub_data["total_spend"]				=	totalSpend['amount__sum']
				else:
					sub_data["total_spend"]				=	totalSpend['amount__sum']
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"totalActiveCount":totalActiveCount,
						"totalExpiredCount":totalExpiredCount,
						"totalReportedCount":totalReportedCount,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":""
						}
		else:
			content = {
				"success": True,
				"data":[],
				"totalActiveCount":totalActiveCount,
				"totalExpiredCount":totalExpiredCount,
				"totalReportedCount":totalReportedCount,
				"msg":_("")
			}	
		return Response(content)
		
class modelExpiredSubscribers(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		totalActiveCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_subscription_cancelled = 0).filter(plan_status="active").all().count()
		totalExpiredCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire")).all().count()
		totalReportedCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_flaged=1).all().count()
					
		DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire"))
		
		if request.GET.get('username'):
			DB 			= DB.filter(username__icontains=request.GET.get('username'))
			
		if request.GET.get('social_account'):
			DB 			= DB.filter(model_subscription__social_account=request.GET.get('social_account'))
		
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
			for sub in results:
				sub_data								=	{}
				totalSpend	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(model_subscription_id=sub.model_subscription_id).filter(user_id=sub.user_id).all().aggregate(Sum('amount'))
			
				if(sub.plan_type == "recurring"):
					if(str(sub.offer_period_type) == "week"):
						billed	=	"Weekly"
					if(str(sub.offer_period_type) == "month"):
						billed	=	"Monthly"
					if(str(sub.offer_period_type) == "year"):
						billed	=	"Yearly"
				else:
					billed	=	"One Time"
				
				
				sub_data["billed"]						=	billed
			
				sub_data["id"]							=	sub.id
				sub_data["offer_name"]					=	sub.offer_name
				sub_data["offer_description"]			=	sub.offer_description
				sub_data["user_name"]					=	sub.username
				sub_data["joined_on"]					=	sub.created_at
				sub_data["expiry_date"]					=	sub.expiry_date
				sub_data["billed"]						=	billed
				sub_data["status"]						=	"Expired"
				sub_data["type"]						=	sub.model_subscription.social_account

				if totalSpend['amount__sum']:
					if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
						sub_data["total_spend"]					=	round(totalSpend['amount__sum'],2)
					else:
						sub_data["total_spend"]			=	0
				else:
					sub_data["total_spend"]				=	0
				sub_data["feedback"]					=	sub.feedback
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"totalActiveCount":totalActiveCount,
						"totalExpiredCount":totalExpiredCount,
						"totalReportedCount":totalReportedCount,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":""
						}
		else:
			content = {
				"success": True,
				"data":[],
				"totalActiveCount":totalActiveCount,
				"totalExpiredCount":totalExpiredCount,
				"totalReportedCount":totalReportedCount,
				"msg":_("")
			}	
		return Response(content)
		
class modelreportedSubscribers(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)

		totalActiveCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_subscription_cancelled = 0).filter(plan_status="active").all().count()
		totalExpiredCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(Q(is_subscription_cancelled=1) | Q(plan_status="expire")).all().count()
		totalReportedCount	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_flaged=1).all().count()
					
		DB 				=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(is_flaged=1)
		
		if request.GET.get('username'):
			DB 			= DB.filter(username__icontains=request.GET.get('username'))
			
		if request.GET.get('social_account'):
			DB 			= DB.filter(model_subscription__social_account__icontains=request.GET.get('social_account'))
		
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
			for sub in results:
				sub_data								=	{}
				totalSpend	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(model_subscription_id=sub.model_subscription_id).filter(user_id=sub.user_id).all().aggregate(Sum('amount'))
			
				if(sub.plan_type == "recurring"):
					if(str(sub.offer_period_type) == "week"):
						billed	=	"Weekly"
					if(str(sub.offer_period_type) == "month"):
						billed	=	"Monthly"
					if(str(sub.offer_period_type) == "year"):
						billed	=	"Yearly"
				else:
					billed	=	"One Time"
				
				
				sub_data["billed"]						=	billed
			
				sub_data["id"]							=	sub.id
				sub_data["offer_name"]					=	sub.offer_name
				sub_data["offer_description"]			=	sub.offer_description
				sub_data["user_name"]					=	sub.username
				sub_data["joined_on"]					=	sub.created_at
				sub_data["expiry_date"]					=	sub.expiry_date
				sub_data["billed"]						=	billed
				sub_data["status"]						=	"Reported"
				sub_data["type"]						=	sub.model_subscription.social_account
				if totalSpend['amount__sum']:
					if (decimal.Decimal(totalSpend['amount__sum']) > decimal.Decimal(0)):
						sub_data["total_spend"]					=	round(totalSpend['amount__sum'],2)
					else:
						totalSpend['amount__sum']		=	0
				else:
					totalSpend['amount__sum']			=	0
				allSubList.append(sub_data)
				
		if allSubList:			
			content = {
						"success": True,
						"data":allSubList,
						"totalActiveCount":totalActiveCount,
						"totalExpiredCount":totalExpiredCount,
						"totalReportedCount":totalReportedCount,
						"recordPerPge":recordPerPge,
						"recordPerPge":recordPerPge,
						"maxIndex":max_index,
						"msg":""
						}
		else:
			content = {
				"success": True,
				"data":[],
				"totalActiveCount":totalActiveCount,
				"totalExpiredCount":totalExpiredCount,
				"totalReportedCount":totalReportedCount,
				"msg":_("")
			}	
		return Response(content)
		
class modelNewExpiredSubscribers(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		
		newPlans		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).aggregate(Count('user_id'))
		#return HttpResponse(newPlans['user_id__count'])
		if request.GET.get('filter_by'):
			filter_by = request.GET.get('filter_by')
		else:
			filter_by = 'week'
		
		if (filter_by == 'week'):
			date_str = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
			date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')	
			
			start_of_week = date_obj - timedelta(days=date_obj.weekday()) 	# Monday
			end_of_week = start_of_week + timedelta(days=6)  				# Sunday
			start_of_week = str(start_of_week.date())+" 00:00:00"
			end_of_week = str(end_of_week.date())+" 23:59:59"

			newPlans		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=start_of_week).filter(created_at__lte=end_of_week).aggregate(Count('user_id'))
			
			expiredPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=start_of_week).filter(expiry_date__lte=end_of_week).aggregate(Count('user_id'))
			
		elif filter_by == 'month':	
			year = date.today().year
			month =	date.today().month
			monthStartDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-01 00:00:00"
			endDate	=	calendar.monthrange(year, month)[1]
			endDate	=	str(endDate)
			monthEndDate = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month)+"-"+endDate +" 23:59:59"
			
			
			newPlans		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).aggregate(Count('user_id'))
			
			expiredPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=monthStartDate).filter(expiry_date__lte=monthEndDate).aggregate(Count('user_id'))
			
		elif filter_by == 'year':	
			year = date.today().year
			month = date.today().month
			yearStartDate 	= str(datetime.datetime.now().year)+"-01-01 00:00:00"
			endDate	=	calendar.monthrange(year, month)[1]
			endDate	=	str(endDate)
			yearEndDate 	= str(datetime.datetime.now().year)+"-12-"+endDate+ " 23:59:59"
			
			newPlans		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=yearStartDate).filter(created_at__lte=yearEndDate).aggregate(Count('user_id'))
			
			expiredPlans	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=yearStartDate).filter(expiry_date__lte=yearEndDate).aggregate(Count('user_id'))
			
		total	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).aggregate(Count('user_id'))
		
		if decimal.Decimal(newPlans['user_id__count']) > decimal.Decimal(expiredPlans['user_id__count']):
			diffrence = decimal.Decimal(newPlans['user_id__count']) - decimal.Decimal(expiredPlans['user_id__count'])
			percentSign  = '+'
		elif decimal.Decimal(expiredPlans['user_id__count']) > decimal.Decimal(newPlans['user_id__count']):
			diffrence = decimal.Decimal(expiredPlans['user_id__count']) - decimal.Decimal(newPlans['user_id__count'])
			percentSign  = '-'
		else:
			diffrence = 0
			percentSign  = ''
			
		if diffrence > 0:
			if decimal.Decimal(newPlans['user_id__count']) > decimal.Decimal(expiredPlans['user_id__count']):
				percentDiffrence = round((decimal.Decimal(diffrence)/decimal.Decimal(newPlans['user_id__count']))*100,2)
			elif decimal.Decimal(expiredPlans['user_id__count']) > decimal.Decimal(newPlans['user_id__count']):
				percentDiffrence = round((decimal.Decimal(diffrence)/decimal.Decimal(expiredPlans['user_id__count']))*100,2)
		else:
			percentDiffrence = 0
			
		content = {
			"success": True,
			"new_plans":newPlans['user_id__count'],
			"expired_plans":expiredPlans['user_id__count'],
			"total_sub":total['user_id__count'],
			"percent_change":percentDiffrence,
			"percent_sign":percentSign,
			"msg":""
		}
		return Response(content)




class ListRevenueGraph(generics.ListAPIView):
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
					weekTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=perdayWeek+" 00:00:00").filter(created_at__lte=perdayWeek+" 23:59:59").all().aggregate(Sum('amount'))
					weekTotal = weekTransaction['amount__sum']
					if weekTotal:
						if (decimal.Decimal(weekTotal) > decimal.Decimal(0)):
							weekTotal = round(weekTotal,2)
						else:
							weekTotal = 0
					else:
						weekTotal = 0
					sub_data['date'] 	= today + datetime.timedelta(days=i)
					sub_data['amount']	= weekTotal
					responseDataArr.append(sub_data)
	


		# #-----------current month date------------
			
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
					monthTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=perdayMonth+" 00:00:00").filter(created_at__lte=perdayMonth+" 23:59:59").all().aggregate(Sum('amount'))
					monthTotal = monthTransaction['amount__sum']
					if monthTotal:
						if (decimal.Decimal(monthTotal) > decimal.Decimal(0)):
							monthTotal = round(monthTotal,2)
						else:
							monthTotal = 0
					else:
						monthTotal = 0


					sub_data['date'] 	= year+'-'+month+'-'+day
					sub_data['amount'] 	= monthTotal
					responseDataArr.append(sub_data)



		# #------------current year date--------------
		
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
					yearTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
					yearTotal = yearTransaction['amount__sum']
					if yearTotal:
						if (decimal.Decimal(yearTotal) > decimal.Decimal(0)):
							yearTotal = round(yearTotal,2)
						else:
							yearTotal = 0
					else:
						yearTotal = 0

					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data["amount"]	=	yearTotal
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data["amount"]	=	yearTotal
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data["amount"]	=	yearTotal
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data["amount"]	=	yearTotal
					responseDataArr.append(sub_data)



		# #------------all time dates--------------



			if graphtype	==	"alltime":
				year_array	=	[]
				year = date.today().year
				for i in range(1,13):
					sub_data	=	{}
					month = i
					monthStartDate = str(datetime.datetime.now().year)+"-"+str(month)+"-01 00:00:00"
					endDate	=	calendar.monthrange(year, month)[1]
					endDate	=	str(endDate)
					monthEndDate = str(datetime.datetime.now().year)+"-"+str(month)+"-"+endDate+" 23:59:59"
					yearTransaction	=	TransactionHistory.objects.exclude(payment_type='refunds').filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
					yearTotal = yearTransaction['amount__sum']
					if yearTotal:
						if (decimal.Decimal(yearTotal) > decimal.Decimal(0)):
							yearTotal = round(yearTotal,2)
						else:
							yearTotal = 0
					else:
						yearTotal = 0

					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data["amount"]	=	yearTotal
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data["amount"]	=	yearTotal
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data["amount"]	=	yearTotal
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data["amount"]	=	yearTotal
					responseDataArr.append(sub_data)

			
			'''if graphtype	==	"alltime":
				year_arr	=	[]
				year = datetime.date.today() - datetime.timedelta(days=3*365)
				year = year.year
				counter = 3
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						monthStartDate = str(year)+"-"+str(month)+"-01 00:00:00"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						monthEndDate = str(year)+"-"+str(month)+"-"+endDate+" 23:59:59"
						# print(monthEndDate)
						datetime_object = datetime.datetime.strptime(monthEndDate, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						alltimeTransaction	=	TransactionHistory.objects.filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
						print(three_month_ago_date)
						print(monthEndDate)
						alltimeTotal = alltimeTransaction['amount__sum']
						if alltimeTotal:
							alltimeTotal = round(float(alltimeTotal),2)
						else:
							alltimeTotal = 0

						sub_data["date"]	=	str(year)+'-'+'0'+str(month)
						sub_data["amount"]	=	alltimeTotal
						if sub_data["date"]	==	str(year)+"-010":
							sub_data["date"]	=	str(year)+"-10"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-011":
							sub_data["date"]	=	str(year)+"-11"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-012":
							sub_data["date"]	=	str(year)+"-12"
							sub_data["amount"]	=	alltimeTotal
						responseDataArr.append(sub_data)
					counter +=1	

				year = datetime.date.today() - datetime.timedelta(days=2*365)
				year = year.year
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						monthStartDate = str(year)+"-"+str(month)+"-01 00:00:00"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						monthEndDate = str(year)+"-"+str(month)+"-"+endDate+" 23:59:59"
						datetime_object = datetime.datetime.strptime(monthEndDate, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						alltimeTransaction	=	TransactionHistory.objects.filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
						alltimeTotal = alltimeTransaction['amount__sum']
						if alltimeTotal:
							alltimeTotal = round(float(alltimeTotal),2)
						else:
							alltimeTotal = 0
						sub_data["date"]	=	str(year)+'-'+'0'+str(month)
						sub_data["amount"]	=	alltimeTotal
						if sub_data["date"]	==	str(year)+"-010":
							sub_data["date"]	=	str(year)+"-10"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-011":
							sub_data["date"]	=	str(year)+"-11"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-012":
							sub_data["date"]	=	str(year)+"-12"
							sub_data["amount"]	=	alltimeTotal
						responseDataArr.append(sub_data)
					counter +=1
				year = datetime.date.today() - datetime.timedelta(days=1*365)
				year = year.year
				for i in range(1,13):
					if counter % 3 == 0:
						sub_data	=	{}
						month = i
						monthStartDate = str(year)+"-"+str(month)+"-01 00:00:00"
						endDate	=	calendar.monthrange(year, month)[1]
						endDate	=	str(endDate)
						monthEndDate = str(year)+"-"+str(month)+"-"+endDate+" 23:59:59"
						datetime_object = datetime.datetime.strptime(monthEndDate, '%Y-%m-%d %H:%M:%S')
						three_month_ago_date = datetime_object - relativedelta(months=3)
						alltimeTransaction	=	TransactionHistory.objects.filter(status='success').filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=monthEndDate).all().aggregate(Sum('amount'))
						alltimeTotal = alltimeTransaction['amount__sum']
						print(three_month_ago_date)
						print(monthEndDate)
						if alltimeTotal:
							alltimeTotal = round(float(alltimeTotal),2)
						else:
							alltimeTotal = 0
						sub_data["date"]	=	str(year)+'-'+'0'+str(month)
						sub_data["amount"]	=	alltimeTotal
						if sub_data["date"]	==	str(year)+"-010":
							sub_data["date"]	=	str(year)+"-10"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-011":
							sub_data["date"]	=	str(year)+"-11"
							sub_data["amount"]	=	alltimeTotal
						elif sub_data["date"]	==	str(year)+"-012":
							sub_data["date"]	=	str(year)+"-12"
							sub_data["amount"]	=	alltimeTotal
						responseDataArr.append(sub_data)
					counter +=1'''
	
		content = {
			"success": True,
			"data":responseDataArr,
			"msg":""
		}
		return Response(content)



class ModelProfileViewGraph(generics.ListAPIView):
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
					#----------model views--------------
					weekModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=perdayWeek+" 00:00:00").filter(created_at__lte=perdayWeek+" 23:59:59").all().count()
					sub_data['date'] 				= today + datetime.timedelta(days=i)
					sub_data['total_views']			= weekModelViews
					responseDataArr.append(sub_data)
	


		# #-----------current month date------------
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
					
					#----------model views--------------
					monthModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=perdayMonth+" 00:00:00").filter(created_at__lte=perdayMonth+" 23:59:59").all().count()
					sub_data['date'] 	= year+'-'+month+'-'+day
					sub_data['total_views']	= monthModelViews
					responseDataArr.append(sub_data)



		# #------------current year date--------------
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
					#----------model views--------------
					yearModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()
					
					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data['total_views']	= yearModelViews
					
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data['total_views']	= yearModelViews
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data['total_views']	= yearModelViews
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data['total_views']	= yearModelViews
					responseDataArr.append(sub_data)



		# #------------all time dates--------------
			if graphtype	==	"alltime":
				year_array	=	[]
				year = date.today().year
				for i in range(1,13):
					sub_data	=	{}
					month = i
					monthStartDate = str(datetime.datetime.now().year)+"-"+str(month)+"-01 00:00:00"
					endDate	=	calendar.monthrange(year, month)[1]
					endDate	=	str(endDate)
					monthEndDate = str(datetime.datetime.now().year)+"-"+str(month)+"-"+endDate+" 23:59:59"
					#----------model views--------------
					yearModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()
					
					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data['total_views']	= yearModelViews
					
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data['total_views']	= yearModelViews
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data['total_views']	= yearModelViews
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data['total_views']	= yearModelViews
					responseDataArr.append(sub_data)

			'''if graphtype	==	"alltime":
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
						#----------model views--------------
						alltimeModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()
						

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]	=	str(year)+"-10"
							sub_data['total_views']	= alltimeModelViews
						else:
							sub_data["date"]	=	dates_three_year_ago
							sub_data['total_views']	= alltimeModelViews
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
						#----------model views--------------
						alltimeModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]	=	str(year)+"-10"
							sub_data['total_views']	= alltimeModelViews
						else:
							sub_data["date"]	=	dates_three_year_ago
							sub_data['total_views']	= alltimeModelViews
							
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
						#----------model views--------------
						alltimeModelViews	=	ModelViews.objects.filter(model_id=request.user.id).filter(created_at__gte=three_month_ago_date).filter(created_at__lte=end_date).all().count()

						if dates_three_year_ago ==	str(year)+"-10":
							sub_data["date"]	=	str(year)+"-10"
							sub_data['total_views']	= alltimeModelViews
						else:
							sub_data["date"]	=	dates_three_year_ago
							sub_data['total_views']	= alltimeModelViews
							
						responseDataArr.append(sub_data)
					counter +=1'''
	
		content = {
			"success": True,
			"data":responseDataArr,
			"msg":""
		}
		return Response(content)




class NewExpiredSubscribersGraph(generics.ListAPIView):
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

					#-------------------- new subscribers ------------------------------------
					weekModelSubcriptions		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=perdayWeek+" 00:00:00").filter(created_at__lte=perdayWeek+" 23:59:59").all().count()
			
					#--------------------- expired subscribers ---------------------------------
					weekSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=perdayWeek+" 00:00:00").filter(expiry_date__lte=perdayWeek+" 23:59:59").all().count()

					sub_data['date'] 	= today + datetime.timedelta(days=i)
					sub_data['new_subscribers']	= weekModelSubcriptions
					sub_data['expired_subscribers']	= weekSubcriptionExpires
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

					#-------------------- new subscribers ------------------------------------
					monthModelSubcriptions		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=perdayMonth+" 00:00:00").filter(created_at__lte=perdayMonth+" 23:59:59").all().count()
			
					#--------------------- expired subscribers ---------------------------------
					monthSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=perdayMonth+" 00:00:00").filter(expiry_date__lte=perdayMonth+" 23:59:59").all().count()

					sub_data['date'] 	= year+'-'+month+'-'+day
					sub_data['new_subscribers']	= monthModelSubcriptions
					sub_data['expired_subscribers']	= monthSubcriptionExpires
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

					#-------------------- new subscribers ------------------------------------
					yearModelSubcriptions		=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(created_at__gte=monthStartDate).filter(created_at__lte=monthEndDate).all().count()
			
					#--------------------- expired subscribers ---------------------------------
					monthStartDate				=	datetime.datetime.strptime(monthStartDate, '%Y-%m-%d %H:%M:%S')
					monthEndDate				=	datetime.datetime.strptime(monthEndDate, '%Y-%m-%d %H:%M:%S')
					yearSubcriptionExpires	=	UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).filter(plan_status='expire').filter(expiry_date__gte=monthStartDate).filter(expiry_date__lte=monthEndDate).all().count()

					sub_data["date"]	=	str(year)+'-'+'0'+str(month)
					sub_data['new_subscribers']	= yearModelSubcriptions
					sub_data['expired_subscribers']	= yearSubcriptionExpires
					if sub_data["date"]	==	str(year)+"-010":
						sub_data["date"]	=	str(year)+"-10"
						sub_data['new_subscribers']	= yearModelSubcriptions
						sub_data['expired_subscribers']	= yearSubcriptionExpires
					elif sub_data["date"]	==	str(year)+"-011":
						sub_data["date"]	=	str(year)+"-11"
						sub_data['new_subscribers']	= yearModelSubcriptions
						sub_data['expired_subscribers']	= yearSubcriptionExpires
					elif sub_data["date"]	==	str(year)+"-012":
						sub_data["date"]	=	str(year)+"-12"
						sub_data['new_subscribers']	= yearModelSubcriptions
						sub_data['expired_subscribers']	= yearSubcriptionExpires
					responseDataArr.append(sub_data)
	
		content = {
			"success": True,
			"data":responseDataArr,
			"msg":""
		}
		return Response(content)



class CheckSubscribedPlanDetail(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		if request.META.get('HTTP_ACCEPT_LANGUAGE') != None:
			user_language = request.META.get('HTTP_ACCEPT_LANGUAGE')
		else :
			user_language = "en"
		translation.activate(user_language)
		user_id = request.user.id

		sub_type 		= 	request.POST.get("subscription_type",'')
		model_id 		= 	request.POST.get("model_id",'')
		subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).filter(plan_status='active').filter(is_subscription_cancelled=0)
			
		if subDetails:
			content = {
				"success": False,
				"data":[],
				"msg":_("You_have_already_Subscribe_for_this_plan")
			}
		else:
			content = {
				"success": True,
				"data":[],
				"msg":_("")
			}
		return Response(content)
