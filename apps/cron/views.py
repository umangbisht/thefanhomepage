from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,UserSubscriptionPlan,LastPayoutDate,TransactionHistory,Payout, PrivateFeedModel
from apps.newsletters.models import ScheduledNewsletter, ScheduledNewsletterSubscriber
from apps.api.models import ReportReasonModel,currencyRate
from apps.dropdownmanger.models import DropDownManager 
from apps.emailtemplates.models import EmailTemplates
from apps.emailtemplates.models import EmailAction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode # Python 3
from django.db.models import Q
from django.template.loader import get_template
import os
import random
from apps.settings.models import Setting
import datetime
import requests
import operator
import json
from django.core.mail import send_mail, BadHeaderError,EmailMessage,EmailMultiAlternatives
from django.core.files.storage import FileSystemStorage
import re
import decimal
from django.utils.html import strip_tags
from django.template import Context
from django.db.models import Count,Sum
from django.conf import settings
from PIL import Image
from decimal import Decimal
from datetime import date,timedelta
from apps.common.views import commonMail,sendEmail
from google.cloud import storage


# Create your views here.
def subscriptionExpires(request):
	subscripexpireDetail	=   UserSubscriptionPlan.objects.filter(expiry_date__lte = datetime.datetime.now()).filter(plan_status = "active").filter(plan_type = "recurring").all().order_by('-id')[:5]
	if len(subscripexpireDetail) > int(0):
		for sub in subscripexpireDetail:
			modelInfo	=   User.objects.filter(id = sub.model_user_id).first()
			if(modelInfo):
				if(int(sub.is_apply_to_rebills) == int(1)):
					amount  = 	decimal.Decimal(sub.amount)
					amount	=	round(amount,2)
				else:
					amount  = 	decimal.Decimal(sub.planprice)
					amount	=	round(amount,2)
				
				order_id =	random.randint(1000000000000000000,9223372036854775806)
			
				context	=	{"model_name":modelInfo.model_name,"amount":amount,"currency":modelInfo.default_currency,"order_id":order_id,"payment_id":sub.transaction_id}
				address = settings.PAYMENT_GATEWAY_RECURRING_PAYMENT_PATH
				r	=	requests.post(address, data=context)
				response		=	json.loads(r.content.decode('utf-8'))
				transaction_id	=	""
				transaction_payment_id	=	""
				if response["status"] and response["status"] == "success":
					if response["response"] and response["response"]["status"] == "approved":
						transaction_id	=	response["response"]["id"]
						transaction_payment_id	=	response["response"]["id"]
						
						today = datetime.date.today()
						if sub.offer_period_type == 'week':
							expiry_date					=	today+datetime.timedelta(days=(int(sub.offer_period_time)*7))
						elif sub.offer_period_type == 'month':
							expiry_date					=	today+datetime.timedelta(days=(int(sub.offer_period_time)*30))
						else:
							expiry_date					=	today+datetime.timedelta(days=(int(sub.offer_period_time)*365.25))
						
						obj    				=   UserSubscriptionPlan.objects.filter(id=sub.id).first()
						obj.expiry_date		=	expiry_date
						obj.save()
						
						transactionObj										=	TransactionHistory()
						transactionObj.user_id								=	sub.user_id
						transactionObj.model_id								=	sub.model_user_id
						transactionObj.amount								=	amount
						transactionObj.expiry_date							=	expiry_date
						transactionObj.price_in_model_currency				=	0
						transactionObj.transaction_date						=	datetime.date.today()
						transactionObj.model_subscription_id				=	sub.model_subscription_id
						transactionObj.plan_id								=	0
						transactionObj.payment_type							= 	'rebills'
						transactionObj.transaction_type						= 	'subscription'
						transactionObj.transaction_id						=	transaction_id
						transactionObj.status								=	'success'
						transactionObj.currency								=	modelInfo.default_currency
						transactionObj.user_subscription_id					=	sub.id
						
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
					else:
						obj    				=   UserSubscriptionPlan.objects.filter(id=sub.id).first()
						obj.plan_status		=	"expire"
						obj.save()
						arrayData						=	{}
						arrayData['socialAccount']		=	sub.model_subscription.social_account
						arrayData['currency']			=	modelInfo.default_currency
						arrayData['price']				=	str(amount)
						arrayData['subscriber_username']				=	sub.username
						commonMail(request,"PLAN_EXPIRE",sub.model_user_id,sub.user_id,arrayData)
				else:
					obj    				=   UserSubscriptionPlan.objects.filter(id=sub.id).first()
					obj.plan_status		=	"expire"
					obj.save()
					
					arrayData						=	{}
					arrayData['socialAccount']		=	sub.model_subscription.social_account
					arrayData['currency']			=	modelInfo.default_currency
					arrayData['price']				=	str(amount)
					arrayData['subscriber_username']				=	sub.username
					commonMail(request,"PLAN_EXPIRE",sub.model_user_id,sub.user_id,arrayData)
			else:
				obj    				=   UserSubscriptionPlan.objects.filter(id=sub.id).first()
				obj.plan_status		=	"expire"
				obj.save()
		
	return HttpResponse("hhiiii")
	
# Create your views here.
def checkDiscountEnabledDisabled(request):
	## Start Discount 
	startDiscountPlans	=   ModelSubscriptionPlans.objects.filter(from_discount_date__lte=date.today()).filter(to_discount_date__gte=date.today()).filter(is_discount_enabled = 0).filter(plan_type='recurring').all()
	if startDiscountPlans:
		for sub in startDiscountPlans:
			if sub.from_discount_date and sub.to_discount_date:
				subObj 							= ModelSubscriptionPlans.objects.filter(id=sub.id).first()
				subObj.is_discount_enabled 		= 1
				subObj.save()
			
	##end Discount
	startDiscountPlans	=   ModelSubscriptionPlans.objects.filter(from_discount_date__lte=date.today()).filter(to_discount_date__lte=date.today()).filter(is_discount_enabled = 1).filter(plan_type='recurring').all()
	if startDiscountPlans:
		for sub in startDiscountPlans:
			if sub.from_discount_date and sub.to_discount_date:
				subObj 							= ModelSubscriptionPlans.objects.filter(id=sub.id).first()
				subObj.is_discount_enabled 		= 0
				subObj.save()		
	return HttpResponse("hhiiii")

def generatePayout(request):
	before21days 		=	str(datetime.date.today()-timedelta(days=21))+" 00:00:00"
	before14days 		=	str(datetime.date.today()-timedelta(days=15))+" 23:59:59"
	nextpaymentdate 	=	datetime.date.today()+timedelta(days=7)
	currentDate  		= 	datetime.date.today()

	currentDate_1  		= 	str(datetime.date.today())+" 00:00:00"
	currentDate_2  		= 	str(datetime.date.today())+" 23:59:59"
	payoutbefore21days	=	LastPayoutDate.objects.filter(last_payout_date__gte=currentDate_1).filter(last_payout_date__lte=currentDate_2).all()
	if payoutbefore21days:
		for payout in payoutbefore21days:
			modelDetails 		=	User.objects.filter(id=payout.model_id).filter(is_deleted=0).first()
			if modelDetails:
				#modelPaymentDetail	=	AccountDetails.objects.filter(model_id=payout.id).first()
				#Total Transaction
				totalTransaction		=	TransactionHistory.exclude(payment_type='refunds').objects.filter(model_id=modelDetails.id).filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))
				
				#Total Commission
				
				totalCommission		=	TransactionHistory.exclude(payment_type='refunds').objects.filter(model_id=modelDetails.id).filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
				#return HttpResponse(totalCommission['commission__sum'])
				if totalTransaction:
					totalAmount 							= 	totalTransaction['amount__sum']
					totalcommissionAmont 					= 	totalCommission['commission__sum']
					if totalAmount == None or totalAmount =='' or totalAmount == 0:
						totalAmount = 0
					if totalcommissionAmont == None or totalcommissionAmont =='' or totalcommissionAmont == 0:
						totalcommissionAmont = 0
					#return HttpResponse(totalAmount)
					
					if totalAmount != None and totalAmount > 0:
						
						net_amount					=	decimal.Decimal(totalAmount)-decimal.Decimal(totalcommissionAmont)
						
						###Ribill amount######
						totalRebillGross		=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='rebills').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))
						
						totalRebillcommission		=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='rebills').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
						
						totalRebillGrossAmount 		= totalRebillGross['amount__sum']
						totalRebillCommissionAmount = totalRebillcommission['commission__sum']
						if totalRebillGrossAmount == None or totalRebillGrossAmount =='' or totalRebillGrossAmount == 0:
							totalRebillGrossAmount = 0
						if totalRebillCommissionAmount == None or totalRebillCommissionAmount =='' or totalRebillCommissionAmount == 0:
							totalRebillCommissionAmount = 0
						
						
						
						
						totalRebillNetAmount 		= decimal.Decimal(totalRebillGrossAmount)-decimal.Decimal(totalRebillCommissionAmount)
						
						###Joins amount######
						totalJoinGross			=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='joins').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))
						
						totalJoincommission		=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='joins').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
						
						totalJoinGrossAmount 		= totalJoinGross['amount__sum']
						totalJoinCommissionAmount 	= totalJoincommission['commission__sum']
						
						if totalJoinGrossAmount == None or totalJoinGrossAmount =='' or totalJoinGrossAmount == 0:
							totalJoinGrossAmount = 0
						if totalJoinCommissionAmount == None or totalJoinCommissionAmount =='' or totalJoinCommissionAmount == 0:
							totalJoinCommissionAmount = 0
						totalJoinNetAmount 			= decimal.Decimal(totalJoinGrossAmount)-decimal.Decimal(totalJoinCommissionAmount)
						
						###Tips amount######
						totalTipsGross			=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='tips').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))
						
						totalTipscommission		=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='tips').filter(status='success').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
						
						totalTipsGrossAmount 		= totalTipsGross['amount__sum']
						totalTipsCommissionAmount 	= totalTipscommission['commission__sum']
						if totalTipsGrossAmount == None or totalTipsGrossAmount =='' or totalTipsGrossAmount == 0:
							totalTipsGrossAmount = 0
						if totalTipsCommissionAmount == None or totalTipsCommissionAmount =='' or totalTipsCommissionAmount == 0:
							totalTipsCommissionAmount = 0
						totalTipsNetAmount 			= decimal.Decimal(totalTipsGrossAmount)-decimal.Decimal(totalTipsCommissionAmount)
						
						
						
						###refunds amount######
						totalRefundsGross			=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='refunds').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('amount'))
						
						totalrefundscommission		=	TransactionHistory.objects.filter(model_id=modelDetails.id).filter(payment_type='refunds').filter(transaction_date__gte=before21days).filter(transaction_date__lte=before14days).all().aggregate(Sum('commission'))
						
						totalRefundsGrossAmount 		= totalRefundsGross['amount__sum']
						totalRefundsCommissionAmount 	= totalrefundscommission['commission__sum']
						if totalRefundsGrossAmount == None or totalRefundsGrossAmount =='' or totalRefundsGrossAmount == 0:
							totalRefundsGrossAmount = 0
						if totalRefundsCommissionAmount == None or totalRefundsCommissionAmount =='' or totalRefundsCommissionAmount == 0:
							totalRefundsCommissionAmount = 0
						totalRedfuncdNetAmount 			= decimal.Decimal(totalRefundsGrossAmount)-decimal.Decimal(totalRefundsCommissionAmount)
						

						paymodel					=	Payout()
						paymodel.model_id			=	modelDetails.id
						paymodel.start_date			=	before21days
						paymodel.end_date			=	before14days
						paymodel.period				=	1
						paymodel.gross_revenue		=	totalAmount
						paymodel.net_revenue		=	net_amount
						paymodel.commission_amount	=	totalcommissionAmont
						paymodel.rebill_gross_revenue =	totalRebillGrossAmount
						paymodel.rebill_net_revenue	=	totalRebillNetAmount
						paymodel.rebill_commission	=	totalRebillCommissionAmount
						paymodel.join_gross_revenue	=	totalJoinGrossAmount
						paymodel.join_net_revenue	=	totalJoinNetAmount
						paymodel.join_commission	=	totalJoinCommissionAmount
						paymodel.tip_gross_revenue	=	totalTipsGrossAmount
						paymodel.tip_net_revenue	=	totalTipsCommissionAmount
						paymodel.tip_commission		=	totalTipsNetAmount
						paymodel.refunds_gross_revenue	=	totalRefundsGrossAmount
						paymodel.refunds_net_revenue	=	totalRefundsCommissionAmount
						paymodel.refunds_commission		=	totalRedfuncdNetAmount
						
						
						paymodel.currency			=	modelDetails.default_currency
						paymodel.pay_slip			=	""
						paymodel.is_paid			=	0
						paymodel.save()
						
				updateLastPayout						=	LastPayoutDate.objects.filter(model_id=modelDetails.id).first()
				if updateLastPayout:
					updateLastPayout.last_payout_date	=	nextpaymentdate
					updateLastPayout.save()
				
	return HttpResponse("saved in payouts")
	
def saveCurrencyPrice(request):
	defaultCurrency = settings.GLOBAL_CONSTANT_CURRENCY
	for currency in defaultCurrency:
		response = requests.get(
			'https://api.coinbase.com/v2/exchange-rates?currency='+currency,
			params={},
			headers={'Content-Type': 'application/json'},
		)
		json_response = response.json()
		#return HttpResponse(json_response)
		if int(response.status_code) == 200:
			rates	=	json_response["data"]["rates"]
			if len(rates) > 0:
				for priceInfo in rates:
					if(priceInfo in defaultCurrency):
						currentPriceInfo = currencyRate.objects.filter(from_currency=currency).filter(to_currency=priceInfo).first()
						if currentPriceInfo:
							currentPriceInfo.price = rates[priceInfo]
							currentPriceInfo.save()
						else:
							currencyRateObj 				= currencyRate()
							currencyRateObj.from_currency   = currency
							currencyRateObj.to_currency   	= priceInfo
							currencyRateObj.price   		= rates[priceInfo]
							currencyRateObj.save()
	return HttpResponse("saved in payouts")
	
def updateModelSiteRank(request):
	allModels = User.objects.filter(user_role_id=3).filter(is_approved=1).filter(is_verified=1).filter(is_deleted=0).all()
	beforeSevendays 		=	datetime.date.today()-timedelta(days=7)
	currentDate  			= datetime.date.today()

	if allModels:
		rank_list								=	{}
		for model in allModels:
			totalamountTransaction = TransactionHistory.objects.filter(status='success').filter(model_id=model.id).filter(created_at__gte=beforeSevendays).all().aggregate(Sum('amount'))
			totalAmount = totalamountTransaction['amount__sum']
			if totalAmount:
				totalAmount = totalAmount
			else:
				totalAmount = 0
				
			if totalAmount > 0:
				currentPriceInfo = currencyRate.objects.filter(from_currency=model.default_currency).filter(to_currency="USD").first()
				totelIncomeInUsd = float(currentPriceInfo.price)*int(totalAmount)
			else:
				totelIncomeInUsd = 0
			rank_list[model.id] = totelIncomeInUsd
				
					
		rank_list = sorted(rank_list.items(), key=lambda kv: kv[1],reverse=True)	
		rankCount = 1
		for rank in rank_list:
			lastRankDetail 		= User.objects.filter(id=rank[0]).first()
			lastRank            = lastRankDetail.rank
			currentRank 		= 	rankCount
			#return HttpResponse(currentRank)
			rank_status = ''
			if int(lastRank) < int(currentRank):
				rank_status = 'down'
			elif int(lastRank) > int(currentRank):
				rank_status = 'up'
			else:
				rank_status = 'stable'
			
			rankCount = rankCount+1 
			#save rank
			lastRankDetail.rank 		= currentRank
			lastRankDetail.rank_status 	= rank_status
			lastRankDetail.save()
	return HttpResponse("saved in payouts")

def publishPrivateFeed(request):
	schedulePrivateFeed	=   PrivateFeedModel.objects.filter(schedule_date__lte = datetime.datetime.now() ).filter(status = "schedule").all()
	if schedulePrivateFeed:
		for sub in schedulePrivateFeed:
			sub_id					=	sub.id
			obj    				=	PrivateFeedModel.objects.filter(id=sub_id).first()
			obj.status			=	"publish"
			obj.save()
			
	return HttpResponse("hhiiii")

def sendNewsletters(request):
	sendScheduledNewsletter	=   ScheduledNewsletter.objects.filter(scheduled_date__lte = datetime.datetime.now()).filter(is_send=0).all()
	if sendScheduledNewsletter:
		for sub in sendScheduledNewsletter:
			scheduledNewsletterSubscribers	=	ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=sub.id).filter(status=0).all()
			if scheduledNewsletterSubscribers:
				for newsletter in scheduledNewsletterSubscribers:
					emailaction				=	EmailAction.objects.filter(action="send_newsletter").first()
					email			=	newsletter.email
					subject			=	sub.subject
					massage_body  	= 	sub.body
					website_url		=	settings.FRONT_SITE_URL
					site_title		=	settings.SITETITLE
					unsubscribelink	=  		settings.FRONT_SITE_URL+'unsubscribe-newletter?subscriber_email='+email
					constant = list()
					data = (emailaction.option.split(','))
					for obj in data:
						constant.append("{"+ obj +"}")
					rep_Array=[email,website_url,unsubscribelink]
					x = range(len(constant))
					for i in x:
						massage_body=re.sub(constant[i], rep_Array[i], massage_body)
					massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
					htmly     = get_template('cron/email.html')
					plaintext = get_template('cron/email.txt')

					html_content = htmly.render(context		=	{
						"body":massage_body,
						"website_url":website_url,
						"site_title":site_title
					})
					sendEmail(request,subject,html_content,email)
					mail_on		=	datetime.datetime.now()

					Obj			=	newsletter
					Obj.status	=	1
					Obj.save()

					sentOn = newsletter
					if sentOn.status == 1:
						sentOn.mail_on = mail_on
					else:
						sentOn.mail_on = ''
					sentOn.save()

			countSentmail	=	ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=sub.id).filter(status=1).all().count()
			countTotal		=	ScheduledNewsletterSubscriber.objects.filter(scheduled_newsletter_id=sub.id).all().count()
			if countSentmail == countTotal:
				obj2			=	sub
				obj2.is_send	=	1
				obj2.save()

	return HttpResponse("hhiiii")
	
import os
def ConvertedVideoPrivateFeed(request):
	privateFeed	=   PrivateFeedModel.objects.filter(is_converted = 0).filter(uploaded_file_type = "video").order_by('-id').first()
	if privateFeed:
		currentMonth = datetime.datetime.now().month
		currentYear = datetime.datetime.now().year
		folder = 'media/uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
		folder_directory = 'uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
		if not os.path.exists(folder):
			os.mkdir(folder)
			
		file_name 		= str(int(datetime.datetime.now().timestamp()))+str(random.randint(0,922337))
		mp4filename		=	str(currentMonth)+str(currentYear)+"/"+file_name+".mp4";
		webmfilename	=	str(currentMonth)+str(currentYear)+"/"+file_name+".webm";
		jpegfilename	=	str(currentMonth)+str(currentYear)+"/"+file_name+".jpg";
		

		"""Uploads a file to the bucket."""
		bucket_name = "my_tfh_local_bucket"
		source_file_name = "F:/Date UI.png"
		destination_blob_name = "media/pingdate.png"

		storage_client = storage.Client.from_service_account_json(json_credentials_path='credential.json')
		bucket = storage_client.bucket(bucket_name)
		blob = bucket.blob(destination_blob_name)

		blob.upload_from_filename(source_file_name)

	
		obj    				=	privateFeed
		obj.is_converted	=	1
		obj.image			=	jpegfilename
		obj.save()
			
	return HttpResponse("converted")