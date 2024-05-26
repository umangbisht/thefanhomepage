from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,ModelFollower,ModelNotificationSetting,UserSubscriptionPlan,PrivateFeedModel
from apps.cmspages.models import CmsPage,CmsPageDescription
from apps.newsletters.models import NewsletterSubscriber
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

# Get the JWT settings
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]

class LoginView(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid."

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	"The password field is required."

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
						"msg":"Invalid email and password."
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_active == 0:
					content = {
						"success": 3,
						"data":[],
						"msg":"Your account has been deactivated. Please contact to admin."
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_verified == 0:
					content = {
						"success": 2,
						"data":[],
						"msg":"Your account is not verified."
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				elif request.user.is_approved == 0 and request.user.user_role_id == 3:
					content = {
						"success": 3,
						"data":[],
						"msg":"Your profile is pending for approval."
					}
					return Response(content,status=status.HTTP_401_UNAUTHORIZED)
				else:
					userDetail	=	{
						"email":request.user.email,"user_role_id":request.user.user_role_id,"first_name":request.user.first_name,"last_name":request.user.last_name,"from_date":request.user.from_date,"address_line_2":request.user.address_line_2,"city":request.user.city,"age":request.user.age,"hair":request.user.hair,"eyes":request.user.eyes,"gender":request.user.gender,"date_of_birth":request.user.date_of_birth,"address_line_1	":request.user.address_line_1,"amazon_wishlist_link":request.user.amazon_wishlist_link,"bio":request.user.bio,"height":request.user.height,"model_name":request.user.model_name,"postal_code":request.user.postal_code,"previous_first_name":request.user.previous_first_name,"previous_last_name":request.user.previous_last_name,"private_snapchat_link":request.user.private_snapchat_link,"public_instagram_link":request.user.public_instagram_link,"public_snapchat_link":request.user.public_snapchat_link,"skype_number":request.user.skype_number,"twitter_link":request.user.twitter_link,"weight":request.user.weight,"youtube_link":request.user.youtube_link,"youtube_video_url":request.user.youtube_video_url
					}
					content = {
						"success": True,
						"msg":"You have login successfully.",
						"token":jwt_encode_handler(jwt_payload_handler(user)),
						"data":userDetail
					}
					return Response(content)
			else:
				content = {
					"success": 3,
					"data":[],
					"msg":"Invalid email and password."
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
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid."
			else:
				if User.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	"This email is already exists."

		if request.POST.get("confirm_email") == "":
			validationErrors["confirm_email"]	=	"The confirm email field is required."
		else:
			if request.POST.get("confirm_email") != request.POST.get("email"):
				validationErrors["confirm_email"]	=	"The email and confirm email field is not equal."

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	"The password field is required."

		if request.POST.get("user_role") == None or request.POST.get("user_role") == "":
			validationErrors["user_role"]	=	"The user role field is required."
		else:
			if request.POST.get("user_role") != "model" and request.POST.get("user_role") != "subscriber":
				validationErrors["user_role"]	=	"The user role value is not valid."
			
		if not validationErrors:
			password = request.data.get("password", "")
			email = request.data.get("email", "")
			user_role = request.data.get("user_role", "")
			if user_role == "model":
				user_role_id	=	3
			else:
				user_role_id	=	2

			if user_role_id == 2:
				strEmal = str(email)
				res = hashlib.md5(strEmal.encode()) 
				validatestring = res.hexdigest() 
				new_user = User.objects.create_user(
					username=email, password=password, email=email, user_role_id=user_role_id,is_approved=1,is_verified=0,validate_string=validatestring
				)
				lastUserId	=	new_user.id
				if lastUserId :
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
					#return HttpResponse(len(constant))
					x = range(len(constant))
					for i in x:
						massage_body=re.sub(constant[i], rep_Array[i], massage_body)
					massage_body = strip_tags(massage_body)
					massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
					htmly     = get_template('email.html')
					plaintext = get_template('email.txt')
					
					text_content = plaintext.render(context		=	{
						"body":massage_body
					})
					
					html_content = htmly.render(context		=	{
						"body":massage_body
					})
					emailData = EmailMultiAlternatives(subject,text_content,to=[email])
					emailData.attach_alternative(html_content, "text/html")
					emailData.content_subtype = "html"
					res = emailData.send()	
			content = {
				"success": True,
				"data":[],
				"msg":"Your account has been registered successfully. Please check your eamil to verify your account."
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
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid."
			else:
				if User.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	"This email is already exists."

		if request.POST.get("confirm_email") == "":
			validationErrors["confirm_email"]	=	"The confirm email field is required."
		else:
			if request.POST.get("confirm_email") != request.POST.get("email"):
				validationErrors["confirm_email"]	=	"The email and confirm email field is not equal."

		if request.POST.get("password") == None or request.POST.get("password") == "":
			validationErrors["password"]	=	"The password field is required."

		if request.POST.get("user_role") == None or request.POST.get("user_role") == "":
			validationErrors["user_role"]	=	"The user role field is required."
		else:
			if request.POST.get("user_role") != "model" and request.POST.get("user_role") != "subscriber":
				validationErrors["user_role"]	=	"The user role value is not valid."
			
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
				folder = 'media/uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
				folder_directory = 'uploads/model_images/'+str(currentMonth)+str(currentYear)+"/"
				if not os.path.exists(folder):
					os.mkdir(folder)
				
				
				gifi_image  = ''
				gibi_image  = ''
				pnti_image	= ''
				pntiwdp_image = ''	
				
				if request.FILES.get("government_id_front_image"):
					gifiFile = request.FILES.get("government_id_front_image")
					fs = FileSystemStorage()
					filename = gifiFile.name.split(".")[0].lower()
					extension = gifiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, gifiFile)	
					gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("government_id_back_image"):
					gibiFile = request.FILES.get("government_id_back_image")
					fs = FileSystemStorage()
					filename = gibiFile.name.split(".")[0].lower()
					extension = gibiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, gibiFile)	
					gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("photo_next_to_id"):
					pntiFile = request.FILES.get("photo_next_to_id")
					fs = FileSystemStorage()
					filename = pntiFile.name.split(".")[0].lower()
					extension = pntiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, pntiFile)	
					pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("photo_next_to_id_with_dated_paper"):
					pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
					fs = FileSystemStorage()
					filename = pntiwdpFile.name.split(".")[0].lower()
					extension = pntiwdpFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, pntiwdpFile)	
					pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				
				slug = (request.POST.get("last_name","")+'-'+request.POST.get("last_name","")).lower();
				lastUserId										=	new_user.id
				NewUserObj 										= 	new_user
				NewUserObj.first_name							=	request.POST.get("first_name","")
				NewUserObj.last_name							=	request.POST.get("last_name","")
				NewUserObj.slug									=	slug
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
				NewUserObj.government_id_number					=	request.POST.get("government_id_number","")
				NewUserObj.government_id_expiration_date		=	request.POST.get("government_id_expiration_date","")
				NewUserObj.government_id_front_image			=	gifi_image
				NewUserObj.government_id_back_image				=	gibi_image
				NewUserObj.photo_next_to_id						=	pnti_image
				NewUserObj.photo_next_to_id_with_dated_paper	=	pntiwdp_image
				NewUserObj.save()
				
				
				
				ModelNotificationInfo									=	ModelNotificationSetting()
				ModelNotificationInfo.user_id 							= 	lastUserId
				ModelNotificationInfo.new_subscription_purchased 		= 	0
				ModelNotificationInfo.subscription_expires 				= 	0
				ModelNotificationInfo.received_tip 						= 	0
				ModelNotificationInfo.subscriber_updates_snapchat_name 	= 	0
				ModelNotificationInfo.detects_login_unverified_device 	= 	0
				ModelNotificationInfo.detects_unsuccessful_login 		= 	0
				ModelNotificationInfo.save()
				
						
				categories 					=   request.POST.get('categories')
				if categories != None and categories != "":
					categories = categories.split(',')
					for category in categories:
						ModelCategoriesInfo							=	ModelCategories()
						ModelCategoriesInfo.dropdown_manager_id 	= 	category
						ModelCategoriesInfo.user_id 				= 	lastUserId
						ModelCategoriesInfo.save()
				
				images = request.FILES.getlist("images")
				if images:
					for imge in images:	
						myfile = imge
						fs = FileSystemStorage()
						filename = myfile.name.split(".")[0].lower()
						extension = myfile.name.split(".")[-1].lower()
						newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
						fs.save(folder_directory+newfilename, myfile)	
						model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
						
						ModelImagesInfo							=	ModelImages()
						ModelImagesInfo.image_url 				= 	model_image
						ModelImagesInfo.user_id 				= 	lastUserId
						ModelImagesInfo.save()
						
				subscription_dict = request.POST.get("subscription")
				if subscription_dict:
					subscription_dict = json.loads(subscription_dict)
					for subdata in subscription_dict:
						if subdata:
							if subscription_dict[subdata]['is_enabled'] == True:
								is_enabled = 1
							else:
								is_enabled = 0
							
							subObj 					= ModelSubscriptions()
							subObj.user_id 			= lastUserId
							subObj.social_account 	= subdata
							subObj.username 		= subscription_dict[subdata]['username']
							subObj.is_enabled 		= is_enabled
							subObj.save()
							
							subId = subObj.id	
							if is_enabled == 1:
								for planData in subscription_dict[subdata]['plans']:
									if planData['is_discount_enabled'] != '':
										is_discount_enabled = 1
									else:
										is_discount_enabled = 0
										
									if planData['is_permanent_discount'] != '':
										is_permanent_discount = 1
									else:
										is_permanent_discount = 0
										
									if planData['is_apply_to_rebills'] != '':
										is_apply_to_rebills = 1
									else:
										is_apply_to_rebills = 0
									
									plansObj 									= ModelSubscriptionPlans()
									plansObj.user_id 							= lastUserId
									plansObj.model_subscription_id 				= subId
									plansObj.plan_type 							= planData['plan_type']
									plansObj.offer_period_time 					= planData['offer_period_time']
									plansObj.offer_period_type 					= planData['offer_period_type']
									plansObj.price 								= planData['price']
									plansObj.currency 							= planData['currency']
									plansObj.description 						= planData['description']
									plansObj.is_discount_enabled 				= is_discount_enabled
									plansObj.discount 							= planData['discount']
									plansObj.from_discount_date 				= planData['from_discount_date']
									plansObj.to_discount_date 					= planData['to_discount_date']
									plansObj.is_permanent_discount 				= is_permanent_discount
									plansObj.is_apply_to_rebills 				= is_apply_to_rebills
									plansObj.save()
							
							
			
			content = {
				"success": True,
				"data":[],
				"msg":"Your account has been registered successfully."
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
		activeCategory = DropDownManager.objects.filter(dropdown_type="category").values("id");
		category = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=activeCategory).all().values('name',"dropdown_manger_id")  # or simply .values() to get all fields
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
		activeCountry = DropDownManager.objects.filter(dropdown_type="country").values("id");
		country = DropDownManagerDescription.objects.filter(dropdown_manger_id__in=activeCountry).all().values('name',"dropdown_manger_id")  # or simply .values() to get all fields
		country = list(country)  # important: convert the QuerySet to a list object
		content = {
			"success": True,
			"data":country,
			"msg":""
		}
		return Response(content)

class FeaturedProfile(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		FeaturedProfiles = User.objects.filter(is_approved=1).filter(is_active=1).filter(is_featured=1).filter(user_role_id=3).filter(is_deleted=0).all()[:10]
		FeaturedProfiles = list(FeaturedProfiles)  # important: convert the QuerySet to a list object
		
		profiles	=	[]
		if FeaturedProfiles:
			for Profile in FeaturedProfiles:
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
				ModelImage = ModelImages.objects.filter(user_id=Profile.id).first()
				if ModelImage:
					profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage.image_url
				else:
					profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/dummy.jpg"
					
					
				subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).all().values('social_account',"username","is_enabled","id");
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).all().values('plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
						planData = list(planData)
						subcription['plans'] = planData	
						
				profile['subcriptions'] = subcriptionData

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
		TotalModels = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0)
		DB = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0)
		if request.GET.get('name'):
			name = request.GET.get('name').strip()
			DB = DB.filter(Q(model_name__contains=name) | Q(first_name__contains=name) | Q(last_name__contains=name) | Q(previous_last_name__contains=name)| Q(previous_first_name__contains=name))
			TotalModels = TotalModels.filter(Q(model_name__contains=name) | Q(first_name__contains=name) | Q(last_name__contains=name) | Q(previous_last_name__contains=name)| Q(previous_first_name__contains=name))

		if request.GET.get('category'):
			category = request.GET.getlist('category')
			categoryUsers = ModelCategories.objects.filter(dropdown_manager_id__in=category).values("user_id");
			DB = DB.filter(Q(id__in=categoryUsers))
			TotalModels = TotalModels.filter(Q(id__in=categoryUsers))
			
		recordPerPge	=	6
		TotalModels	=	TotalModels.count()
		order_by	=	request.GET.get('order_by',"created_at")
		direction	=	request.GET.get('direction',"DESC")
		
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
				profile["user_id"]							=	Profile.id
				ModelImage = ModelImages.objects.filter(user_id=Profile.id).all()
				if ModelImage:
					images	=	[]
					for ProfileImage in ModelImage:
						images.append(settings.MEDIA_SITE_URL+"uploads/model_images/"+ProfileImage.image_url)

					profile["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage[0].image_url
					profile["images"]			=	images
				else:
					profile["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/dummy.jpeg"
					profile["images"]			=	""
					
				subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).all().values('social_account',"username","is_enabled","id");
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).all().values('plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
						planData = list(planData)
						subcription['plans'] = planData	

				profile['subcriptions'] = subcriptionData

				profiles.append(profile)

		content = {
			"success": True,
			"data":profiles,
			"msg":"",
			"TotalModels":TotalModels,
			"recordPerPge":recordPerPge
		}
		return Response(content)

class modelProfile(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		
		if request.GET["slug"] != None and request.GET["slug"] != "":
			
				
			slug	=	request.GET["slug"]
			ModelDetail = User.objects.filter(is_approved=1).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).filter(slug=slug).first()
			
			if ModelDetail:
				ModelDetail = model_to_dict(ModelDetail)
				
			if ModelDetail:
				if request.user.is_authenticated:
					user_id = request.user.id
					followDetails	=   ModelFollower.objects.filter(subscriber_id=user_id).filter(model_id=ModelDetail["id"]).first()
					if followDetails:
						ModelDetail["is_followed"] = 1
					else:
						ModelDetail["is_followed"] = 0
				else:
					ModelDetail["is_followed"] = 0	
				
				
				ModelImage = ModelImages.objects.filter(user_id=ModelDetail["id"]).all()
				if ModelImage:
					images	=	[]
					for ProfileImage in ModelImage:
						images.append(settings.MEDIA_SITE_URL+"uploads/model_images/"+ProfileImage.image_url)

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

				subcriptionData = ModelSubscriptions.objects.filter(user_id=ModelDetail["id"]).all().values('id','social_account',"username","is_enabled","id");
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).all().values('id','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
						planData = list(planData)
						subcription['plans'] = planData	
						
				ModelDetail['subcriptions'] = subcriptionData
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
					"msg":"Model not found",
				}
				return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":"Model not found",
			}
			return Response(content)

class cmsPageView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)

	def get(self, request, *args, **kwargs):
		if request.GET['slug'] == None or request.GET['slug'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			cmsPageDetail = CmsPage.objects.filter(slug=request.GET['slug']).first();
			if cmsPageDetail:
				cmsdata = CmsPageDescription.objects.filter(cms_page_id=cmsPageDetail.id).filter(language_code='en').first()
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
					"msg":"Invalid request"
				}
				
		return Response(content)

class supportView(generics.CreateAPIView):
	permission_classes = (permissions.AllowAny,)
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid."
			
		if request.POST.get("name") == None or request.POST.get("name") == "":
			validationErrors["name"]	=	"The name field is required."
			
		if request.POST.get("subject") == None or request.POST.get("subject") == "":
			validationErrors["subject"]	=	"The subject field is required."
			
		if request.POST.get("message") == None or request.POST.get("message") == "":
			validationErrors["message"]	=	"The message field is required."

		
			
		if not validationErrors:
			Obj						=	Support()
			Obj.email				=	request.POST.get("email")
			Obj.name				=	request.POST.get("name")
			Obj.subject				=	request.POST.get("subject")
			Obj.message				=	request.POST.get("message")
			Obj.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":"Support request sent sucessfully."
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
			
class aboutView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		blockData = Block.objects.filter(page_slug="about").filter(is_active=1).order_by("block_order").values("id");
		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).all()  # or simply .values() to get all fields		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.MEDIA_SITE_URL+"uploads/block_images/"+BlockObj.block.image
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
				"msg":"No data found"
			}
		
				
		return Response(content)
		
		
class makeMoneyOne(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		blockData = Block.objects.filter(page_slug="Make-Money-1").filter(is_active=1).order_by("block_order").values("id");
		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).all()  # or simply .values() to get all fields		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.MEDIA_SITE_URL+"uploads/block_images/"+BlockObj.block.image
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
				"msg":"No data found"
			}
		
				
		return Response(content)
		
class makeMoneyTwo(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		blockData = Block.objects.filter(page_slug="Make-Money-2").filter(is_active=1).order_by("block_order").values("id");
		if blockData:
			blockDesc 	= BlockDescription.objects.filter(block_id__in=blockData).all()  # or simply .values() to get all fields		
			blocks	=	[]
			if blockDesc:
				for BlockObj in blockDesc:
					blockList							=	{}
					blockList["block_name"]				=	BlockObj.block_name
					blockList["description"]			=	BlockObj.description
					blockList["image"]					=	settings.MEDIA_SITE_URL+"uploads/block_images/"+BlockObj.block.image
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
				"msg":"No data found"
			}
		
				
		return Response(content)
		
class verifyAccountView(generics.ListAPIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request, *args, **kwargs):
		if request.GET['validate_string'] == None or request.GET['validate_string'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			userDetail = User.objects.filter(validate_string=request.GET['validate_string']).first();
			if userDetail:
				obj 				= userDetail
				obj.validate_string = ''
				obj.is_verified 	= 1
				obj.save()
				content = {
					"success": True,
					"data":[],
					"msg":"Your account verified successfully."
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":"Invalid request"
				}
				
		return Response(content)
		
		
class manageSubscription(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	
	def get(self, request, *args, **kwargs):
		user_id = request.user.id
		subcriptionData = ModelSubscriptions.objects.filter(user_id=user_id).all().values('social_account',"username","is_enabled","id");
		subcriptionData = list(subcriptionData)
		if subcriptionData:
			for subcription in subcriptionData:
				planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).all().values('id','plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
				planData = list(planData)
				subcription['plans'] = planData
		content = {
			"success": True,
			"data":subcriptionData,
			"msg":""
		}
		return Response(content)
		
	def delete(self, request, *args, **kwargs):
		
		if request.GET['sub_id'] == None or request.GET['sub_id'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			ModelSubscriptionPlans.objects.filter(id=request.GET['sub_id']).all().delete()
			content = {
				"success": True,
				"data":[],
				"msg":"Subscription plan removed successfully."
			}	
		return Response(content)
	
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		
			
		if request.POST.get("subscription") == None or request.POST.get("subscription") == "":
			validationErrors["subscription"]	=	"The subscription field is required."
		
		user_id = request.user.id	
		if not validationErrors:
			subscription_dict = request.POST.get("subscription")
			if subscription_dict:
				
				subscription_dict = json.loads(subscription_dict)
				ModelSubscriptionPlans.objects.filter(user_id=user_id).all().delete()
				ModelSubscriptions.objects.filter(user_id=user_id).all().delete()
				for subdata in subscription_dict:
					if subdata:
						if subscription_dict[subdata]['is_enabled'] == True:
							is_enabled = 1
						else:
							is_enabled = 0
						
						
						
						
						subObj 					= ModelSubscriptions()
						subObj.user_id 			= user_id
						subObj.social_account 	= subdata
						subObj.username 		= subscription_dict[subdata]['username']
						subObj.is_enabled 		= is_enabled
						subObj.save()
						subId = subObj.id	
						if is_enabled == 1:
							for planData in subscription_dict[subdata]['plans']:
								if planData['is_discount_enabled'] != '':
									is_discount_enabled = 1
								else:
									is_discount_enabled = 0
								
								if "is_permanent_discount" in planData:
									is_permanent_discount = 1
								else:
									is_permanent_discount = 0
									
								
								if "is_apply_to_rebills" in planData:
									is_apply_to_rebills = 1
								else:
									is_apply_to_rebills = 0
									
								if "from_discount_date" in planData:
									from_discount_date = planData['from_discount_date']
								else:
									from_discount_date = ''
									
								if "to_discount_date" in planData:
									to_discount_date = planData['to_discount_date']
								else:
									to_discount_date = ''
								
								plansObj 									= ModelSubscriptionPlans()
								plansObj.user_id 							= user_id
								plansObj.model_subscription_id 				= subId
								plansObj.plan_type 							= planData['plan_type']
								plansObj.offer_period_time 					= planData['offer_period_time']
								plansObj.offer_period_type 					= planData['offer_period_type']
								plansObj.price 								= planData['price']
								plansObj.currency 							= planData['currency']
								plansObj.description 						= planData['description']
								plansObj.is_discount_enabled 				= is_discount_enabled
								plansObj.discount 							= planData['discount']
								plansObj.from_discount_date 				= from_discount_date
								plansObj.to_discount_date 					= to_discount_date
								plansObj.is_permanent_discount 				= is_permanent_discount
								plansObj.is_apply_to_rebills 				= is_apply_to_rebills
								plansObj.save()
								
			
			content = {
				"success": True,
				"data":[],
				"msg":"Subscriptions updated sucessfully."
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
		user_id = request.user.id
		userDetail = User.objects.filter(is_approved=1).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()
		if userDetail:
			if userDetail.user_role_id == 2:
				ModelDetail = model_to_dict(userDetail)
			else:
				ModelDetail = User.objects.filter(is_approved=1).filter(id=user_id).filter(is_active=1).filter(user_role_id=3).filter(is_deleted=0).first()
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
				"msg":"Invalid requst"
			}
			return Response(content)
		
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		user_id 		= request.user.id	
		userDetails		=   User.objects.filter(is_approved=1).filter(id=user_id).filter(is_active=1).filter(is_verified=1).filter(is_deleted=0).first()	
		
		
		
		
		if not userDetails:
			validationErrors["user"]	=	"Invalid Request"
		
		
		if not validationErrors:
			if userDetails.user_role_id == 2:
				NewUserObj										=   userDetails
				NewUserObj.skype_number							=	request.POST.get("skype_number")
				NewUserObj.model_name							=	request.POST.get("model_name")
				NewUserObj.phone_number							=	request.POST.get("phone_number")
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
				
				if request.FILES.get("government_id_front_image"):
					gifiFile = request.FILES.get("government_id_front_image")
					fs = FileSystemStorage()
					filename = gifiFile.name.split(".")[0].lower()
					extension = gifiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, gifiFile)	
					gifi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("government_id_back_image"):
					gibiFile = request.FILES.get("government_id_back_image")
					fs = FileSystemStorage()
					filename = gibiFile.name.split(".")[0].lower()
					extension = gibiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, gibiFile)	
					gibi_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("photo_next_to_id"):
					pntiFile = request.FILES.get("photo_next_to_id")
					fs = FileSystemStorage()
					filename = pntiFile.name.split(".")[0].lower()
					extension = pntiFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, pntiFile)	
					pnti_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
					
				if request.FILES.get("photo_next_to_id_with_dated_paper"):
					pntiwdpFile = request.FILES.get("photo_next_to_id_with_dated_paper")
					fs = FileSystemStorage()
					filename = pntiwdpFile.name.split(".")[0].lower()
					extension = pntiwdpFile.name.split(".")[-1].lower()
					newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
					fs.save(folder_directory+newfilename, pntiwdpFile)	
					pntiwdp_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
				
				
				lastUserId										=	user_id
				NewUserObj										=   userDetails
				if request.POST.get("type") == 'account':
					NewUserObj.model_name							=	request.POST.get("model_name")
					NewUserObj.phone_number							=	request.POST.get("phone_number")
					NewUserObj.skype_number							=	request.POST.get("skype_number")
				else:
					NewUserObj.first_name							=	request.POST.get("first_name")
					NewUserObj.last_name							=	request.POST.get("last_name")
					NewUserObj.previous_first_name					=	request.POST.get("previous_first_name")
					NewUserObj.previous_last_name					=	request.POST.get("previous_last_name")
					NewUserObj.date_of_birth						=	request.POST.get("date_of_birth")
					NewUserObj.gender								=	request.POST.get("gender")
					NewUserObj.country								=	request.POST.get("country")
					NewUserObj.address_line_1						=	request.POST.get("address_line_1")
					NewUserObj.address_line_2						=	request.POST.get("address_line_2")
					NewUserObj.city									=	request.POST.get("city")
					NewUserObj.postal_code							=	request.POST.get("postal_code")
					NewUserObj.skype_number							=	request.POST.get("skype_number")
					NewUserObj.model_name							=	request.POST.get("model_name")
					NewUserObj.bio									=	request.POST.get("bio")
					NewUserObj.best_known_for						=	request.POST.get("best_known_for")
					NewUserObj.private_snapchat_link				=	request.POST.get("private_snapchat_link")
					NewUserObj.public_snapchat_link					=	request.POST.get("public_snapchat_link")
					NewUserObj.public_instagram_link				=	request.POST.get("public_instagram_link")
					NewUserObj.twitter_link							=	request.POST.get("twitter_link")
					NewUserObj.youtube_link							=	request.POST.get("youtube_link")
					NewUserObj.amazon_wishlist_link					=	request.POST.get("amazon_wishlist_link")
					NewUserObj.age									=	request.POST.get("age")
					NewUserObj.from_date							=	request.POST.get("from_date")
					NewUserObj.height								=	request.POST.get("height")
					NewUserObj.weight								=	request.POST.get("weight")
					NewUserObj.hair									=	request.POST.get("hair")
					NewUserObj.eyes									=	request.POST.get("eyes")
					NewUserObj.youtube_video_url					=	request.POST.get("youtube_video_url")
					NewUserObj.government_id_number					=	request.POST.get("government_id_number")
					NewUserObj.government_id_expiration_date		=	request.POST.get("government_id_expiration_date")
					NewUserObj.phone_number							=	request.POST.get("phone_number")
					NewUserObj.government_id_front_image			=	gifi_image
					NewUserObj.government_id_back_image				=	gibi_image
					NewUserObj.photo_next_to_id						=	pnti_image
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
				
				images = request.FILES.getlist("images")
				if images:
					for imge in images:	
						myfile = imge
						fs = FileSystemStorage()
						filename = myfile.name.split(".")[0].lower()
						extension = myfile.name.split(".")[-1].lower()
						newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
						fs.save(folder_directory+newfilename, myfile)	
						model_image	=	str(currentMonth)+str(currentYear)+"/"+newfilename
						
						ModelImagesInfo							=	ModelImages()
						ModelImagesInfo.image_url 				= 	model_image
						ModelImagesInfo.user_id 				= 	lastUserId
						ModelImagesInfo.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":"Profile updated sucessfully."
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":validationErrors,
				"msg":"Validation errors"
			}
			return Response(content)
		
class followModel(generics.CreateAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}	
		if request.POST.get("model_id") == None or request.POST.get("model_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid Request"
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
					"msg":"Model followed successfully"
				}
				return Response(content)
			else:
				ModelFollower.objects.filter(subscriber_id=request.user.id).filter(model_id=request.POST.get("model_id")).delete()
				content = {
					"success": True,
					"data":[],
					"status":0,
					"msg":"Model unfollowed successfully"
				}
				return Response(content)
				
				
class newModels(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)

	def get(self, request, *args, **kwargs):
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
						images.append(settings.MEDIA_SITE_URL+"uploads/model_images/"+ProfileImage.image_url)

					profile["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage[0].image_url
					profile["images"]			=	images
				else:
					profile["profile_image"]	=	settings.MEDIA_SITE_URL+"uploads/dummy.jpeg"
					profile["images"]			=	""
					
					
				subcriptionData = ModelSubscriptions.objects.filter(user_id=Profile.id).all().values('social_account',"username","is_enabled","id");
				subcriptionData = list(subcriptionData)
				if subcriptionData:
					for subcription in subcriptionData:
						planData = ModelSubscriptionPlans.objects.filter(model_subscription_id=subcription['id']).all().values('plan_type',"offer_period_time","offer_period_type","price","currency","description","is_discount_enabled","discount","from_discount_date","to_discount_date","is_permanent_discount","is_apply_to_rebills");
						planData = list(planData)
						subcription['plans'] = planData	
						
				profile['subcriptions'] = subcriptionData

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
		followList	=   ModelFollower.objects.filter(subscriber_id=request.user.id).all().values("model_id")
		if followList:
			FollowingProfiles = User.objects.filter(id__in=followList).all()
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
						profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/model_images/"+ModelImage.image_url
					else:
						profile["profile_image"]					=	settings.MEDIA_SITE_URL+"uploads/dummy.jpeg"
						
					profiles.append(profile)
			content = {
				"success": True,
				"data":profiles,
				"msg":"Following listed successfully."
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":"No followings found."
			}
			return Response(content)
		
			
class deleteImage(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def delete(self, request, *args, **kwargs):
		
		if request.GET['img_id'] == None or request.GET['img_id'] == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			
			ModelImages.objects.filter(id=request.GET['img_id']).all().delete()
			content = {
				"success": True,
				"data":[],
				"msg":"Image removed successfully."
			}	
		return Response(content)
		
class manageNotifications(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	
	def get(self, request, *args, **kwargs):
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
		validationErrors	=	{}
		
		user_id = request.user.id	
		if not validationErrors:
			NotiSettingObj										=   ModelNotificationSetting.objects.filter(user_id=user_id).first()
			if NotiSettingObj:
				NotiSettingObj = NotiSettingObj
			else:
				NotiSettingObj  = ModelNotificationSetting()
				NotiSettingObj.user_id = user_id
			NotiSettingObj.new_subscription_purchased 			= 	request.POST.get("new_subscription_purchased",0)
			NotiSettingObj.subscription_expires 				= 	request.POST.get("subscription_expires",0)
			NotiSettingObj.received_tip 						= 	request.POST.get("received_tip",0)
			NotiSettingObj.subscriber_updates_snapchat_name 	= 	request.POST.get("subscriber_updates_snapchat_name",0)
			NotiSettingObj.detects_login_unverified_device 		= 	request.POST.get("detects_login_unverified_device",0)
			NotiSettingObj.detects_unsuccessful_login 			= 	request.POST.get("detects_unsuccessful_login",0)
			NotiSettingObj.save()
			
			content = {
				"success": True,
				"data":[],
				"msg":"Notification setting updated sucessfully."
			}
			return Response(content)

class UserSubscribe(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.AllowAny,)
	
	
	def post(self, request, *args, **kwargs):
		email= request.POST.get("email",'')
		userDetails		=   User.objects.filter(email=email).first()
		if userDetails:
			content = {
				"success": True,
				"data":[],
				"token":jwt_encode_handler(jwt_payload_handler(userDetails)),
				"msg":"User already exiets.Please login to process."
			}
			return Response(content)
		else:
			strEmal = str(email)
			res = hashlib.md5(strEmal.encode()) 
			validatestring = res.hexdigest() 
			password = 'System@123'
			new_user = User.objects.create_user(
				username=email, password=password, email=email, user_role_id=2,is_approved=1,is_verified=0,validate_string=validatestring
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
				#return HttpResponse(len(constant))
				x = range(len(constant))
				for i in x:
					massage_body=re.sub(constant[i], rep_Array[i], massage_body)
				massage_body = strip_tags(massage_body)
				massage_body = re.sub(r'&nbsp;', ' ', massage_body, flags=re.IGNORECASE)
				htmly     = get_template('email.html')
				plaintext = get_template('email.txt')
				
				text_content = plaintext.render(context		=	{
					"body":massage_body
				})
				
				html_content = htmly.render(context		=	{
					"body":massage_body
				})
				emailData = EmailMultiAlternatives(subject,text_content,to=[email])
				emailData.attach_alternative(html_content, "text/html")
				emailData.content_subtype = "html"
				res = emailData.send()
				###verification email
				
				
				
			content = {
				"success": True,
				"data":[],
				"token":jwt_encode_handler(jwt_payload_handler(user_details)),
				"msg":"Your account has been registered successfully. Please check your eamil to verify your account."
			}
			return Response(content)			
			
class saveUserSubscription(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		sub_type 		= request.POST.get("subscription_type",'')
		model_id 		= request.POST.get("model_id",'')
		user_id 		= request.user.id	
		subDetails		=   UserSubscriptionPlan.objects.filter(user_id=user_id).filter(model_subscription_id=sub_type).filter(model_user_id=model_id).first()
		if subDetails:
			content = {
				"success": False,
				"data":[],
				"msg":"You have already Subscribe for this plan"
			}
			return Response(content)
		else:
			userSubPlanObj  									= 	UserSubscriptionPlan()
			userSubPlanObj.user_id 								=   user_id
			userSubPlanObj.username 							= 	request.POST.get("username",'')
			userSubPlanObj.email 								= 	request.POST.get("email",'')
			userSubPlanObj.sub_name 							= 	request.POST.get("sub_name",'')
			userSubPlanObj.post_code 							= 	request.POST.get("post_code",'')
			userSubPlanObj.amount 								= 	request.POST.get("amount",'')
			userSubPlanObj.model_subscription_id				= 	request.POST.get("subscription_type",'')
			userSubPlanObj.plan_type_id 						= 	request.POST.get("plan_type",'')
			userSubPlanObj.model_user_id 						= 	request.POST.get("model_id",'')
			userSubPlanObj.subscription_desc 					= 	request.POST.get("subscription_desc",'')
			userSubPlanObj.save()
		
		content = {
			"success": True,
			"data":[],
			"msg":"Plan subscribed successfully ."
		}
		return Response(content)

class SubscribeNewsletter(generics.CreateAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		if request.POST.get("email") == None or request.POST.get("email") == "":
			validationErrors["email"]	=	"The email field is required."
		else:
			EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
			if request.POST.get("email") and not re.match(EMAIL_REGEX, request.POST.get("email")):
				validationErrors["email"]	=	"This email is not valid."
			else:
				if NewsletterSubscriber.objects.filter(email=request.POST.get("email")).exists():
					validationErrors["email"]	=	"This email is already exists."
			
		if not validationErrors:
			email 			=	request.data.get("email", "")
			Obj				=	NewsletterSubscriber()
			Obj.email		=	email
			Obj.save()
			content = {
				"success": True,
				"data":[],
				"msg":"Your email has been subscribed successfully."
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
		validationErrors	=	{}
		if request.POST.get("title") == None or request.POST.get("title") == "":
			validationErrors["title"]	=	"The title field is required."
		
		if request.POST.get("description") == None or request.POST.get("description") == "":
			validationErrors["description"]	=	"The description field is required."

		if len(request.FILES) == 0:
			validationErrors["image"]	=	"The image field is required."
		elif len(request.FILES) > 0:
			file = request.FILES["image"].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["image"]	=	"The image is not a valid image. Please upload a valid image. Valid extensions are jpg,jpeg,png,gif"
			
		if not validationErrors:
			currentMonth = datetime.datetime.now().month
			currentYear = datetime.datetime.now().year
			folder = 'media/uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
			folder_directory = 'uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
			if not os.path.exists(folder):
				os.mkdir(folder)
			if request.FILES.get("image"):
				image = request.FILES.get("image")
				fs = FileSystemStorage()
				filename = image.name.split(".")[0].lower().replace(" ","-")
				extension = image.name.split(".")[-1].lower()
				newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
				fs.save(folder_directory+newfilename, image)

			if request.POST.get("schedule_date") == None or request.POST.get("schedule_date") == "":
				status		=	"draft"
			else:
				status		=	"schedule"

			Obj					=	PrivateFeedModel()
			Obj.title			=	request.data.get('title')
			Obj.description		=	request.data.get('description')
			Obj.schedule_date	=	request.data.get('schedule_date')
			Obj.image			=	newfilename
			Obj.status			=	status
			Obj.user_id			=	request.user.id
			Obj.save()

			content = {
				"success": True,
				"data":[],
				"msg":"Your profile has been published successfully."
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
		
		if request.GET.get("search_string") == None or request.GET.get("search_string") == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		elif request.GET.get("status") == None or request.GET.get("status") == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			PrivateFeeds = PrivateFeedModel.objects.filter(user_id=request.user.id)
			PrivateFeedsTotal = PrivateFeedModel.objects.filter(user_id=request.user.id)
			if request.GET.get('search_string'):
				search_string = request.GET.get('search_string').strip()
				PrivateFeeds = PrivateFeeds.filter(Q(title__contains=search_string) | Q(description__contains=search_string))
				PrivateFeedsTotal = PrivateFeedsTotal.count()

			PrivateFeedsTotal = PrivateFeedModel.objects.filter(user_id=request.user.id)
			if request.GET.get('status'):
				search_string = request.GET.get('status').strip()
				PrivateFeeds = PrivateFeeds.filter("status",search_string)
				PrivateFeedsTotal = PrivateFeeds.count()

		recordPerPge	=	10
		order_by	=	request.GET.get('order_by',"created_at")
		direction	=	request.GET.get('direction',"DESC")

		page = request.GET.get('page', 1)
		paginator = Paginator(PrivateFeeds, recordPerPge)
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
				PrivateFeed["title"]					=	PrivateFeed1.title
				PrivateFeed["image"]					=	settings.MEDIA_SITE_URL+"uploads/private_feed_images"+PrivateFeed1.image
				PrivateFeed["description"]				=	PrivateFeed1.description
				PrivateFeed["description"]				=	PrivateFeed1.description
				PrivateFeed["schedule_date"]			=	PrivateFeed1.schedule_date
				PrivateFeed["status"]					=	PrivateFeed1.status
				PrivateFeed["created_at"]				=	PrivateFeed1.created_at
				private_feeds.append(PrivateFeed)
				
				

		content = {
			"success": True,
			"data":private_feeds,
			"msg":""
		}
		return Response(content)


	def put(self, request, *args, **kwargs):
		validationErrors	=	{}
		if request.POST.get("private_fee_id") == None or request.POST.get("private_fee_id") == "":
			validationErrors["private_fee_id"]	=	"The private feed id field is required."

		if request.POST.get("title") == None or request.POST.get("title") == "":
			validationErrors["title"]	=	"The title field is required."
		
		if request.POST.get("description") == None or request.POST.get("description") == "":
			validationErrors["description"]	=	"The description field is required."

		if len(request.FILES) > 0:
			file = request.FILES["image"].name
			extension = file.split(".")[-1].lower()
			if not extension in VALID_IMAGE_EXTENSIONS:
				validationErrors["image"]	=	"The image is not a valid image. Please upload a valid image. Valid extensions are jpg,jpeg,png,gif"
			
		if not validationErrors:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.POST.get("private_fee_id")).filter(user_id=request.user.id).first()
			if PrivateFeedDetail:
				newfilename	=	""
				if len(request.FILES) > 0:
					currentMonth = datetime.datetime.now().month
					currentYear = datetime.datetime.now().year
					folder = 'media/uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
					folder_directory = 'uploads/private_feed_images/'+str(currentMonth)+str(currentYear)+"/"
					if not os.path.exists(folder):
						os.mkdir(folder)
					if request.FILES.get("image"):
						image = request.FILES.get("image")
						fs = FileSystemStorage()
						filename = image.name.split(".")[0].lower().replace(" ","-")
						extension = image.name.split(".")[-1].lower()
						newfilename = filename+str(int(datetime.datetime.now().timestamp()))+"."+extension
						fs.save(folder_directory+newfilename, image)

				if request.POST.get("schedule_date") == None or request.POST.get("schedule_date") == "":
					status		=	"draft"
				else:
					status		=	"schedule"

				Obj					=	PrivateFeedDetail
				Obj.title			=	request.data.get('title')
				Obj.description		=	request.data.get('description')
				Obj.schedule_date	=	request.data.get('schedule_date')
				if newfilename != "":
					Obj.image			=	request.data.get('image')

				Obj.status			=	status
				Obj.save()

				content = {
					"success": True,
					"data":[],
					"msg":"Your profile has been updated successfully."
				}
				return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":"Private feed id does not exists."
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
		if request.GET.get("private_fee_id") == None or request.GET.get("private_fee_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.GET.get("private_fee_id")).filter(user_id=request.user.id).first()
			if PrivateFeedDetail:
				PrivateFeedModel.objects.filter(id=request.GET.get("private_fee_id")).filter(user_id=request.user.id).delete()
				content = {
					"success": True,
					"data":[],
					"msg":"Private feed removed successfully."
				}
			else:
				content = {
					"success": False,
					"data":[],
					"msg":"Private feed id does not exists."
				}	

		return Response(content)

class PublishPrivateFeed(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def post(self, request, *args, **kwargs):
		validationErrors	=	{}
		if request.POST.get("private_fee_id") == None or request.POST.get("private_fee_id") == "":
			validationErrors["private_fee_id"]	=	"The private feed id is required."

		if not validationErrors:
			PrivateFeedDetail = PrivateFeedModel.objects.filter(id=request.POST.get("private_fee_id")).filter(user_id=request.user.id).filter(status="draft").first()
			if PrivateFeedDetail:
				Obj					=	PrivateFeedDetail
				Obj.status			=	"publish"
				Obj.save()

				content = {
					"success": True,
					"data":[],
					"msg":"Your profile has been published successfully."
				}
				return Response(content)
			else:
				content = {
					"success": False,
					"data":[],
					"msg":"Private feed id does not exists."
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
		if request.GET.get("model_id") == None or request.GET.get("model_id") == "":
			content = {
				"success": False,
				"data":[],
				"msg":"Invalid request"
			}
		else:
			PrivateFeeds = PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish')
			PrivateFeedsTotal = PrivateFeedModel.objects.filter(user_id=request.GET.get("model_id")).filter(status='publish')
			if request.GET.get('search_string'):
				search_string = request.GET.get('search_string').strip()
				PrivateFeeds = PrivateFeeds.filter(Q(title__contains=search_string) | Q(description__contains=search_string))
				PrivateFeedsTotal = PrivateFeedsTotal.count()
			
			recordPerPge	=	10
			order_by	=	request.GET.get('order_by',"created_at")
			direction	=	request.GET.get('direction',"DESC")

			page = request.GET.get('page', 1)
			paginator = Paginator(PrivateFeeds, recordPerPge)
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
					PrivateFeed["title"]					=	PrivateFeed1.title
					PrivateFeed["image"]					=	settings.MEDIA_SITE_URL+"uploads/private_feed_images"+PrivateFeed1.image
					PrivateFeed["description"]				=	PrivateFeed1.description
					PrivateFeed["created_at"]				=	PrivateFeed1.created_at
					private_feeds.append(PrivateFeed)
					
			content = {
				"success": True,
				"data":private_feeds,
				"msg":""
			}
			return Response(content)
		return Response(content)

		
			
class getSubscriptionList(generics.ListAPIView):
	permission_classes = (permissions.IsAuthenticated,)
	def get(self, request, *args, **kwargs):
		subList	=   UserSubscriptionPlan.objects.filter(model_user_id=request.user.id).all()
		
		if subList:
			allSubList	=	[]
			for sub in subList:
				#return HttpResponse(sub.model_subscription_id.social_account)
				sub_data								=	{}
				planDetail = ModelSubscriptions.objects.filter(id=sub.model_subscription_id).first()
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
				"msg":"Subscribers listed successfully."
			}
			return Response(content)
		else:
			content = {
				"success": False,
				"data":[],
				"msg":"No Subscriber found."
			}
			return Response(content)
