# users/models.py
from apps.dropdownmanger.models import DropDownManager
from django.contrib.auth.models import AbstractUser
from apps.dropdownmanger.models import DropDownManager 
from django.db import models
from django.utils import timezone
# user.signup_from = user
class User(AbstractUser):
	user_role_id = models.IntegerField(db_index=True,default=0)
	email = models.EmailField(db_index=True, max_length=254,blank=False,unique = True)
	username = models.CharField(db_index=True, max_length=150,blank=False,unique = True)
	first_name = models.CharField(max_length=100, blank=True, null=True)
	last_name = models.CharField(max_length=100, blank=True,null=True)
	password = models.CharField(max_length=128,blank=False)
	previous_first_name = models.CharField(max_length=100, blank=True, null=True)
	previous_last_name = models.CharField(max_length=100, blank=True, null=True)
	date_of_birth= models.CharField(max_length=100,blank=True, null=True)
	gender=models.CharField(max_length=100, blank=True,null=True)
	address_line_1=models.CharField(max_length=255, blank=True,null=True)
	address_line_2=models.CharField(max_length=255, blank=True,null=True)
	city=models.CharField(max_length=100,blank=True, null=True)
	country=models.CharField(max_length=100,blank=True, null=True)
	postal_code=models.CharField(max_length=100,blank=True, null=True)
	skype_number=models.CharField(max_length=100,blank=True, null=True)
	model_name=models.CharField(max_length=100,blank=True, null=True)
	best_known_for=models.TextField(blank=True, null=True)
	bio=models.TextField(blank=True, null=True)
	private_snapchat_link = models.CharField(max_length=254, blank=True, null=True)
	public_snapchat_link = models.CharField(max_length=254, blank=True, null=True)
	public_instagram_link = models.CharField(max_length=254, blank=True, null=True)
	twitter_link = models.CharField(max_length=254, blank=True, null=True)
	youtube_link = models.CharField(max_length=254, blank=True, null=True)
	amazon_wishlist_link = models.CharField(max_length=254, blank=True, null=True)
	age=models.CharField(max_length=100,blank=True, null=True)
	from_date=models.CharField(max_length=100,blank=True, null=True)
	height=models.CharField(max_length=100,blank=True, null=True)
	weight=models.CharField(max_length=100,blank=True, null=True)
	hair=models.CharField(max_length=100,blank=True, null=True)
	eyes=models.CharField(max_length=100,blank=True, null=True)
	youtube_video_url=models.CharField(max_length=254,blank=True, null=True)
	is_active = models.IntegerField(default=1)
	is_approved = models.IntegerField(default=1)
	is_featured = models.IntegerField(default=0)
	is_verified = models.IntegerField(default=1)
	validate_string = models.CharField(max_length=255,blank=True, null=True)
	government_id_number = models.CharField(max_length=255,blank=True, null=True)
	government_id_expiration_date = models.CharField(max_length=255,blank=True, null=True)
	government_id_front_image = models.CharField(max_length=255,blank=True, null=True)
	government_id_back_image = models.CharField(max_length=255,blank=True, null=True)
	photo_next_to_id = models.CharField(max_length=255,blank=True, null=True)
	photo_next_to_id_with_dated_paper = models.CharField(max_length=255,blank=True, null=True)
	slug=models.CharField(max_length=100,blank=True, null=True)
	phone_number=models.CharField(max_length=100,blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	is_deleted = models.BooleanField(default=False)
	total_views = models.IntegerField(default=0)
	highest_discount = models.IntegerField(default=0)
	featured_image = models.CharField(max_length=255,blank=True, null=True)
	default_currency = models.CharField(max_length=255,blank=True, null=True)
	rank = models.CharField(max_length=255,blank=True, null=True,default=0)
	rank_status = models.CharField(max_length=255,blank=True, null=True)
	forgot_password_string	=	models.CharField(max_length=255,blank=True, null=True)
	signup_from	=	models.ForeignKey('self', models.PROTECT, blank=True, null=True )
	total_subscriber_signup = models.IntegerField(default = 0)
	is_subscription_enabled = models.IntegerField(default = 1)
	login_with_model = models.IntegerField(default = 0)
	is_homepage_profile = models.CharField(max_length=255,blank=True, null=True,default=1)
	is_private_feed = models.IntegerField(default = 0)
	main_image = models.CharField(max_length=255,blank=True, null=True)

	USERNAME_FIELD = 'username'

	class Meta:
		db_table = 'auth_user'
		
		
class ModelImages(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	image_url = models.CharField(max_length=255, blank=False)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'model_images'
		
class ModelCategories(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	dropdown_manager = models.ForeignKey(DropDownManager, models.PROTECT)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'model_categories'
		
class ModelSubscriptions(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	social_account = models.CharField(max_length=255, blank=False)
	username = models.CharField(max_length=255, blank=True, null=True)
	is_enabled = models.IntegerField(default=0)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	is_deleted = models.BooleanField(default=False)

	class Meta:
		db_table = 'model_subscriptions'
		
class ModelSubscriptionPlans(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	model_subscription = models.ForeignKey(ModelSubscriptions, models.PROTECT)
	plan_type = models.CharField(max_length=255, blank=True, null=True)
	offer_period_time = models.CharField(max_length=255, blank=True, null=True)
	offer_period_type = models.CharField(max_length=255, blank=True, null=True)
	price = models.FloatField(default=0)
	discounted_price = models.FloatField(default=0)
	currency = models.CharField(max_length=255, blank=True, null=True)
	description = models.CharField(max_length=255, blank=True, null=True)
	is_discount_enabled = models.IntegerField(default=0)
	discount = models.FloatField(default=0)
	from_discount_date = models.CharField(max_length=255, blank=True, null=True)
	offer_name = models.CharField(max_length=255, blank=True, null=True)
	to_discount_date = models.CharField(max_length=255, blank=True, null=True)
	is_permanent_discount = models.IntegerField(default=0)
	is_apply_to_rebills = models.IntegerField(default=0)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	is_deleted = models.BooleanField(default=False)
	model_status = models.IntegerField(default=0)

	class Meta:
		db_table = 'model_subscription_plans'
		
		
class ModelFollower(models.Model):
	subscriber = models.ForeignKey(User, models.PROTECT)
	model = models.ForeignKey(User, models.PROTECT,related_name='+')
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'model_followers'
		verbose_name_plural = 'ModelFollower'
		
class ModelNotificationSetting(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	new_subscription_purchased = models.IntegerField(default=0)
	subscription_expires = models.IntegerField(default=0)
	received_tip = models.IntegerField(default=0)
	subscriber_updates_snapchat_name = models.IntegerField(default=0)
	detects_login_unverified_device = models.IntegerField(default=0)
	detects_unsuccessful_login = models.IntegerField(default=0)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'model_notification_settings'
		
class UserSubscriptionPlan(models.Model):
	user = models.ForeignKey(User, models.PROTECT,related_name='+')
	model_subscription = models.ForeignKey(ModelSubscriptions, models.PROTECT,related_name='+')
	plan_type = models.ForeignKey(ModelSubscriptionPlans, models.PROTECT,related_name='-')
	model_user = models.ForeignKey(User, models.PROTECT,related_name='userparent',null=True)
	username = models.CharField(max_length=255, blank=True, null=True)
	email = models.CharField(max_length=255, blank=True, null=True)
	sub_name = models.CharField(max_length=255, blank=True, null=True)
	post_code = models.CharField(max_length=255, blank=True, null=True)
	amount = models.FloatField(default=0)
	price_in_model_currency = models.CharField(max_length=255, blank=True, null=True)
	subscription_desc = models.CharField(max_length=255, blank=True, null=True)
	expiry_date = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	transaction_id = models.CharField(max_length=255, blank=True, null=True)
	transaction_payment_id = models.CharField(max_length=255, blank=True, null=True)
	plan_status = models.CharField(max_length=255, blank=True, null=True,default="active")
	plan_validity = models.CharField(max_length=255, blank=True, null=True)
	feedback = models.CharField(max_length=255, blank=True, null=True)
	stay_connected = models.CharField(max_length=255, blank=True, null=True)

	offer_name = models.CharField(max_length=255, blank=True, null=True)
	offer_description = models.CharField(max_length=255, blank=True, null=True)
	plan_type = models.CharField(max_length=255, blank=True, null=True)
	offer_period_time = models.CharField(max_length=255, blank=True, null=True)
	offer_period_type = models.CharField(max_length=255, blank=True, null=True)
	planprice = models.FloatField(default=0)
	discounted_price = models.FloatField(default=0)
	is_discount_enabled = models.IntegerField(default=0)
	is_subscription_cancelled = models.IntegerField(default=0)
	discount = models.FloatField(default=0)
	from_discount_date = models.CharField(max_length=255, blank=True, null=True)
	to_discount_date = models.CharField(max_length=255, blank=True, null=True)
	is_permanent_discount = models.IntegerField(default=0)
	is_apply_to_rebills = models.IntegerField(default=0)
	user_subscription_plan_description = models.TextField(blank=True, null=True)
	is_flaged = models.IntegerField(default=0)
	subscription_cancelled_on = models.DateTimeField(default=timezone.now)
	is_tick_marked = models.IntegerField(default=0)
	
	class Meta:
		db_table = 'user_subscription_plans'

class PrivateFeedModel(models.Model):
	user = models.ForeignKey(User, models.PROTECT)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	schedule_date = models.CharField(max_length=255,null=True)
	image = models.CharField(max_length=255,null=True)
	uploaded_file_type = models.CharField(max_length=10,null=True)
	is_converted = models.IntegerField(default=1)
	status = models.CharField(max_length=50, default='draft')
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	class Meta:
		db_table = 'private_feeds'

class TipMe(models.Model):
	user 					= models.ForeignKey(User, models.PROTECT,related_name='+', null=True)
	model_user	 			= models.ForeignKey(User, models.PROTECT,related_name='+')
	transaction_id 			= models.CharField(max_length=255, blank=True, null=True)
	amount					= models.CharField(max_length=255, blank=True, null=True)
	currency				= models.CharField(max_length=255, blank=True, null=True)
	price_in_model_currency = models.CharField(max_length=255, blank=True, null=True)
	message 				= models.CharField(max_length=255, blank=True, null=True)
	email 					= models.CharField(max_length=255, blank=True, null=True)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at				= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'tips'

class ModelViews(models.Model):
	model	 		= models.ForeignKey(User, models.PROTECT,related_name='+',null=True,blank=True)
	ip_address		= models.CharField(max_length=255, blank=True, null=True)
	created_at 		= models.DateTimeField(default=timezone.now)
	updated_at		= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'model_views'
		
class TransactionHistory(models.Model):
	amount 			 		= models.FloatField(default=0)
	price_in_model_currency = models.CharField(max_length=255, blank=True, null=True)
	user   			 		= models.ForeignKey(User, models.PROTECT,related_name='+', null=True)
	model   			 	= models.ForeignKey(User, models.PROTECT,related_name='+',blank=True, null=True)
	transaction_id 			= models.CharField(max_length=255, blank=True, null=True)
	transaction_date 		= models.DateTimeField(default=timezone.now)
	model_subscription 		= models.ForeignKey(ModelSubscriptions, models.PROTECT,related_name='+', blank=True, null=True)
	plan_id 					= models.IntegerField(default=0)
	tips 	 				= models.ForeignKey(TipMe, models.PROTECT,related_name='+', blank=True, null=True)
	currency 		 		= models.CharField(max_length=255, blank=True, null=True)
	status 				    = models.CharField(max_length=50, default='success')
	transaction_type 		= models.CharField(max_length=255, blank=True, null=True)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at 				= models.DateTimeField(default=timezone.now)
	tip_email				= models.CharField(max_length=255, blank=True, null=True)
	user_subscription	 	= models.ForeignKey(UserSubscriptionPlan, models.PROTECT,related_name='+', null=True)
	expiry_date = models.CharField(max_length=255, blank=True, null=True)
	is_subscription_cancelled = models.IntegerField(default=0)
	commission				=	models.FloatField(default=0)
	payment_type = models.CharField(max_length=255, blank=True, null=True)
	subscription_cancelled_on = models.DateTimeField(default=timezone.now)
	
	class Meta:
		db_table = 'transaction_history'
		
class LastPayoutDate(models.Model):
	model	 				= models.ForeignKey(User, models.PROTECT,related_name='+',null=True,blank=True)
	last_payout_date		= models.DateTimeField(default=timezone.now)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at				= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'last_payout_dates'
		
class Payout(models.Model):
	model   			 	= models.ForeignKey(User, models.PROTECT,related_name='+')
	start_date 				= models.DateTimeField(default=timezone.now)
	end_date 				= models.DateTimeField(default=timezone.now)
	period 		 			= models.CharField(max_length=255, blank=True, null=True)
	gross_revenue 			= models.FloatField(default=0)
	net_revenue 			= models.FloatField(default=0)
	commission_amount 		= models.FloatField(default=0)
	rebill_gross_revenue 	= models.FloatField(default=0)
	rebill_net_revenue 		= models.FloatField(default=0)
	rebill_commission		= models.FloatField(default=0)
	join_gross_revenue 		= models.FloatField(default=0)
	join_net_revenue 		= models.FloatField(default=0)
	join_commission			= models.FloatField(default=0)
	tip_gross_revenue 		= models.FloatField(default=0)
	tip_net_revenue 		= models.FloatField(default=0)
	tip_commission			= models.FloatField(default=0)
	
	refunds_gross_revenue 		= models.FloatField(default=0)
	refunds_net_revenue 		= models.FloatField(default=0)
	refunds_commission			= models.FloatField(default=0)
	
	
	currency 				= models.CharField(max_length=255, blank=True, null=True)
	pay_slip 				= models.CharField(max_length=255, blank=True, null=True)
	is_paid 				= models.IntegerField(default=0)
	payment_date 				= models.DateTimeField(default=timezone.now)
	payment_method 			= models.CharField(max_length=255, blank=True, null=True)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at 				= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'payouts'
						
class TopFan(models.Model):
	model   			 	= models.ForeignKey(User, models.PROTECT,related_name='+')
	fan   			 		= models.ForeignKey(User, models.PROTECT,related_name='+')
	total_spend 		 	= models.CharField(max_length=255, blank=True, null=True)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at 				= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'top_fans'

class AccountDetails(models.Model):
	model   			 	= models.ForeignKey(User, models.PROTECT,related_name='+')
	payment_method			= models.CharField(max_length= 255, null=True, blank=True)
	pay_to 					= models.CharField(max_length= 255, null=True, blank=True)
	minimum_payout 		 	= models.CharField(max_length=255, blank=True, null=True)
	bank_name 		 		= models.CharField(max_length=255, blank=True, null=True)
	bank_address		 	= models.CharField(max_length=255, blank=True, null=True)
	country					= models.CharField(max_length= 255, null=True, blank=True)
	swift_bic		 		= models.CharField(max_length=255, blank=True, null=True)
	iban					= models.CharField(max_length=255, blank=True, null=True)

	name					= models.CharField(max_length=255, blank=True, null=True)
	cheque_email			= models.CharField(max_length=255, blank=True, null=True)
	address 				= models.CharField(max_length=255, blank=True, null=True)
	contact_number			= models.CharField(max_length=255, blank=True, null=True)
	
	paypal_email			= models.CharField(max_length=255, blank=True, null=True)
	#is_saved				= models.IntegerField(default=0)
	created_at 				= models.DateTimeField(default=timezone.now)
	updated_at 				= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'account_details'

class AuthorizeDevices(models.Model):
	user			=	models.ForeignKey(User, models.PROTECT,related_name='+')
	user_agent		=	models.TextField(blank=True, null=True)
	browser_device	=	models.CharField(max_length=255, blank=True, null=True)
	location		=	models.CharField(max_length=255, blank=True, null=True)
	ip_address		=	models.CharField(max_length=255, blank=True, null=True)
	created_at 		= models.DateTimeField(default=timezone.now)
	updated_at 		= models.DateTimeField(default=timezone.now)
	class Meta:
		db_table = 'authorize_devices'


class AdditionalLinks(models.Model):
	model			=	models.ForeignKey(User, models.PROTECT,related_name='+',blank=True, null=True)
	name			=	models.CharField(max_length=255, blank=True, null=True)
	link			=	models.CharField(max_length=255, blank=True, null=True)
	class Meta:
		db_table = 'model_additional_links'
		
		
class FinalizedTransaction(models.Model):
	transaction_id	=	models.CharField(max_length=255)
	status			=	models.CharField(max_length=50)
	errors			=	models.TextField(blank=True, null=True)
	class Meta:
		db_table = 'finalized_transactions'




class PaymentGatewayErrors(models.Model):
	user = models.ForeignKey(User, models.PROTECT,related_name='+')
	model_subscription = models.ForeignKey(ModelSubscriptions, models.PROTECT,related_name='+', null=True, blank=True)
	plan_type = models.ForeignKey(ModelSubscriptionPlans, models.PROTECT,related_name='+')
	model_user = models.ForeignKey(User, models.PROTECT,related_name='paymentgatewayerrors',null=True)
	username = models.CharField(max_length=255, blank=True, null=True)
	email = models.CharField(max_length=255, blank=True, null=True)
	sub_name = models.CharField(max_length=255, blank=True, null=True)
	post_code = models.CharField(max_length=255, blank=True, null=True)
	amount = models.FloatField(default=0)
	price_in_model_currency = models.CharField(max_length=255, blank=True, null=True)
	subscription_desc = models.CharField(max_length=255, blank=True, null=True)
	expiry_date = models.DateTimeField(blank=True, null=True)
	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)
	transaction_id = models.CharField(max_length=255, blank=True, null=True)
	transaction_payment_id = models.CharField(max_length=255, blank=True, null=True)
	plan_status = models.CharField(max_length=255, blank=True, null=True,default="active")
	plan_validity = models.CharField(max_length=255, blank=True, null=True)
	feedback = models.CharField(max_length=255, blank=True, null=True)
	stay_connected = models.CharField(max_length=255, blank=True, null=True)

	plan_type = models.CharField(max_length=255, blank=True, null=True)
	offer_period_time = models.CharField(max_length=255, blank=True, null=True)
	offer_period_type = models.CharField(max_length=255, blank=True, null=True)
	planprice = models.FloatField(default=0)
	discounted_price = models.FloatField(default=0)
	is_discount_enabled = models.IntegerField(default=0)
	is_subscription_cancelled = models.IntegerField(default=0)
	discount = models.FloatField(default=0)
	from_discount_date = models.CharField(max_length=255, blank=True, null=True)
	to_discount_date = models.CharField(max_length=255, blank=True, null=True)
	is_permanent_discount = models.IntegerField(default=0)
	is_apply_to_rebills = models.IntegerField(default=0)
	user_subscription_plan_description = models.TextField(blank=True, null=True)
	is_flaged = models.IntegerField(default=0)
	subscription_cancelled_on = models.DateTimeField(default=timezone.now)
	is_tick_marked = models.IntegerField(default=0)
	response = models.TextField(blank=True, null=True)
	transaction_type = models.CharField(max_length = 255, null =True, blank = True)
	
	class Meta:
		db_table = 'payment_gateway_errors'



from storages.backends.gcloud import GoogleCloudStorage
storage = GoogleCloudStorage()
class Upload:
	@staticmethod
	def upload_image_on_gcp(file, filename):
		try:
			target_path = '/media/uploads/' + filename
			path = storage.save(target_path, file)
			print("successfully uploaded!!")
			return storage.url(path)
		except Exception as e:
			print("Failed to upload!")