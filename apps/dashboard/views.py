from django.shortcuts import render,HttpResponse
from django.contrib.auth.decorators import login_required
from apps.users.models import User,Payout, TransactionHistory
from django.db.models import Count,Sum
import datetime
import time
import calendar
from dateutil.relativedelta import *
from datetime import date,timedelta

# Create your views here.

@login_required(login_url='/login/')
def index(request):
	totalSubscriber		=	User.objects.filter(user_role_id=2).filter(is_deleted=0).all().count()
	if totalSubscriber:
		totalSubscriber	=	totalSubscriber
	else:
		totalSubscriber = 00
	totalModel			=	User.objects.filter(user_role_id=3).filter(is_deleted=0).all().count()
	if totalModel:
		totalModel		=	totalModel
	else:
		totalModel = 00
	activeModel			=	User.objects.filter(user_role_id=3).filter(is_deleted=0).filter(is_active=1).all().count()
	if activeModel:
		activeModel		=	activeModel
	else:
		activeModel = 00
	approvedModel		=	User.objects.filter(user_role_id=3).filter(is_deleted=0).filter(is_approved=1).all().count()
	if approvedModel:
		approvedModel		=	approvedModel
	else:
		approvedModel = 00

	amountUSD   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='USD').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('commission'))
	if amountUSD['commission__sum']==None or amountUSD['commission__sum'] =="":
		amountUSD   =   0.0
	else:
		amountUSD   =   amountUSD['commission__sum']
	amountUSD		=	round(amountUSD, 2)

	amountAUD   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='AUD').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('commission'))
	if amountAUD['commission__sum']==None or amountAUD['commission__sum'] =="":
		amountAUD   =   0.0
	else:
		amountAUD   =   amountAUD['commission__sum']
	amountAUD		=	round(amountAUD, 2)

	amountGBP   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='GBP').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('commission'))
	if amountGBP['commission__sum']==None or amountGBP['commission__sum'] =="":
		amountGBP   =   0.0
	else:
		amountGBP   =   amountGBP['commission__sum']
	amountGBP		=	round(amountGBP, 2)

	amountEUR   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='EUR').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('commission'))
	if amountEUR['commission__sum']==None or amountEUR['commission__sum'] =="":
		amountEUR   =   0.0
	else:
		amountEUR   =   amountEUR['commission__sum']
	amountEUR		=	round(amountEUR, 2)


	amountUSDPayment   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='USD').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('amount'))
	if amountUSDPayment['amount__sum']==None or amountUSDPayment['amount__sum'] =="":
		amountUSDPayment   =   0.0
	else:
		amountUSDPayment   =   amountUSDPayment['amount__sum']
	amountUSDPayment       =	round(amountUSDPayment, 2)

	amountAUDPayment   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='AUD').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('amount'))
	if amountAUDPayment['amount__sum']==None or amountAUDPayment['amount__sum'] =="":
		amountAUDPayment   =   0.0
	else:
		amountAUDPayment   =   amountAUDPayment['amount__sum']
	amountAUDPayment       =	round(amountAUDPayment, 2)

	amountGBPPayment   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='GBP').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('amount'))
	if amountGBPPayment['amount__sum']==None or amountGBPPayment['amount__sum'] =="":
		amountGBPPayment   =   0.0
	else:
		amountGBPPayment   =   amountGBPPayment['amount__sum']
	amountGBPPayment       =	round(amountGBPPayment, 2)

	amountEURPayment   =   TransactionHistory.objects.exclude(payment_type='refunds').filter(currency='EUR').filter(status="success").filter(model__is_deleted = 0).all().aggregate(Sum('amount'))
	if amountEURPayment['amount__sum']==None or amountEURPayment['amount__sum'] =="":
		amountEURPayment   =   0.0
	else:
		amountEURPayment   =   amountEURPayment['amount__sum']
	amountEURPayment       =	round(amountEURPayment, 2)


	yearData = {}
	yearDataPayment = {}
	currentdate 	=	datetime.date.today()
	one_month_ago 	=	currentdate - relativedelta(months=1)
	if one_month_ago.day 	> 25:
		one_month_ago 	+= datetime.timedelta(7)
	firstDateOneMonth	=	one_month_ago.replace(day=1)
	lastDateOneMonth	=	datetime.date(one_month_ago.year, one_month_ago.month, calendar.monthrange(one_month_ago.year, one_month_ago.month)[-1])
	one_month_ago 	= 	one_month_ago.strftime("%B")
	
	two_month_ago 	=	currentdate - relativedelta(months=2)
	if two_month_ago.day 	> 25:
		two_month_ago 	+= datetime.timedelta(7)
	firstDateTwoMonth	=	two_month_ago.replace(day=1)
	lastDateTwoMonth	=	datetime.date(two_month_ago.year, two_month_ago.month, calendar.monthrange(two_month_ago.year, two_month_ago.month)[-1])
	two_month_ago 		=	two_month_ago.strftime("%B")

	three_month_ago	=	currentdate - relativedelta(months=3)
	if three_month_ago.day 	> 25:
		three_month_ago 	+= datetime.timedelta(7)
	firstDateThreeMonth	=	three_month_ago.replace(day=1)
	lastDateThreeMonth	=	datetime.date(three_month_ago.year, three_month_ago.month, calendar.monthrange(three_month_ago.year, three_month_ago.month)[-1])
	three_month_ago 	=	three_month_ago.strftime("%B")

	four_month_ago	=	currentdate - relativedelta(months=4)
	if four_month_ago.day 	> 25:
		four_month_ago 	+= datetime.timedelta(7)
	firstDateFourMonth	=	four_month_ago.replace(day=1)
	lastDateFourMonth	=	datetime.date(four_month_ago.year, four_month_ago.month, calendar.monthrange(four_month_ago.year, four_month_ago.month)[-1])
	four_month_ago 		=	four_month_ago.strftime("%B")

	five_month_ago	=	currentdate - relativedelta(months=5)
	if five_month_ago.day 	> 25:
		five_month_ago 	+= datetime.timedelta(7)
	firstDateFiveMonth	=	five_month_ago.replace(day=1)
	lastDateFiveMonth	=	datetime.date(five_month_ago.year, five_month_ago.month, calendar.monthrange(five_month_ago.year, five_month_ago.month)[-1])
	five_month_ago 		=	five_month_ago.strftime("%B")

	six_month_ago	=	currentdate - relativedelta(months=6)
	if six_month_ago.day 	> 25:
		six_month_ago 	+= datetime.timedelta(7)
	firstDateSixMonth	=	six_month_ago.replace(day=1)
	lastDateSixMonth	=	datetime.date(six_month_ago.year, six_month_ago.month, calendar.monthrange(six_month_ago.year, six_month_ago.month)[-1])
	six_month_ago 		=	six_month_ago.strftime("%B")


	amountSixMonthUSD   =   Payout.objects.filter(is_paid=1).filter(currency='USD').filter(created_at__gte=firstDateSixMonth).filter(created_at__lte=lastDateSixMonth).all().aggregate(Sum('commission_amount'))
	if amountSixMonthUSD['commission_amount__sum']==None or amountSixMonthUSD['commission_amount__sum'] =="":
		amountSixMonthUSD   =   0.0
	else:
		amountSixMonthUSD   =   amountSixMonthUSD['commission_amount__sum']

	amountSixMonthAUD   	=   Payout.objects.filter(is_paid=1).filter(currency='AUD').filter(created_at__gte=firstDateSixMonth).filter(created_at__lte=lastDateSixMonth).all().aggregate(Sum('commission_amount'))
	if amountSixMonthAUD['commission_amount__sum']==None or amountSixMonthAUD['commission_amount__sum'] =="":
		amountSixMonthAUD   =   0.0
	else:
		amountSixMonthAUD   =   amountSixMonthAUD['commission_amount__sum']

	amountSixMonthGBP   	=   Payout.objects.filter(is_paid=1).filter(currency='GBP').filter(created_at__gte=firstDateSixMonth).filter(created_at__lte=lastDateSixMonth).all().aggregate(Sum('commission_amount'))
	if amountSixMonthGBP['commission_amount__sum']==None or amountSixMonthGBP['commission_amount__sum'] =="":
		amountSixMonthGBP   =   0.0
	else:
		amountSixMonthGBP   =   amountSixMonthGBP['commission_amount__sum']

	amountSixMonthEUR   	=   Payout.objects.filter(is_paid=1).filter(currency='EUR').filter(created_at__gte=firstDateSixMonth).filter(created_at__lte=lastDateSixMonth).all().aggregate(Sum('commission_amount'))
	if amountSixMonthEUR['commission_amount__sum']==None or amountSixMonthEUR['commission_amount__sum'] =="":
		amountSixMonthEUR   =   0.0
	else:
		amountSixMonthEUR   =   amountSixMonthEUR['commission_amount__sum']

	x = 6
	now = time.localtime()
	allMonths =  reversed([time.localtime(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0)))[:2] for n in range(x)])
	currency_list = ['USD','AUD','GBP','EUR']
	month_arr	=	[]
	sub_month_arr	=	[]
	model_month_arr	=	[]
	for allMonth in allMonths:
		num_days 		= calendar.monthrange(allMonth[0], allMonth[1])
		start_date 		= datetime.date(allMonth[0], allMonth[1], 1)
		last_day 		= datetime.date(allMonth[0], allMonth[1], num_days[1])

		new_sub_data = {}
		new_sub_data_payment = {}
		for currency in currency_list:
			commission_in_month = 	TransactionHistory.objects.exclude(payment_type='refunds').filter(currency=currency).filter(status="success").filter(created_at__gte=start_date).filter(created_at__lte=last_day).filter(model__is_deleted = 0).all().aggregate(Sum('commission'))
			
			if commission_in_month['commission__sum']==None or commission_in_month['commission__sum'] =="":
				new_sub_data[currency]   =   0.0
			else:
				new_sub_data[currency]   =   commission_in_month['commission__sum']
		yearData[str(allMonth[0])+'-'+str(allMonth[1])] = new_sub_data

		for currency in currency_list:
			amount_in_month = 	TransactionHistory.objects.exclude(payment_type='refunds').filter(status="success").filter(currency=currency).filter(created_at__gte=start_date).filter(created_at__lte=last_day).filter(model__is_deleted = 0).all().aggregate(Sum('amount'))
			
			if amount_in_month['amount__sum']==None or amount_in_month['amount__sum'] =="":
				new_sub_data_payment[currency]   =   0.0
			else:
				new_sub_data_payment[currency]   =   amount_in_month['amount__sum']
		yearDataPayment[str(allMonth[0])+'-'+str(allMonth[1])] = new_sub_data_payment
		start_date	=	str(start_date)+" 00:00:00"
		last_day	=	str(last_day)+" 23:59:59"

		monthlySubscriber		=	User.objects.filter(user_role_id=2).filter(is_deleted=0).filter(created_at__gte=start_date).filter(created_at__lte=last_day).all().count()
		if monthlySubscriber !=None or monthlySubscriber !="":
			monthlySubscriber	=	str(monthlySubscriber)
		else:
			monthlySubscriber	=	0
		sub_month_arr.append(monthlySubscriber)

		monthlyModel		=	User.objects.filter(user_role_id=3).filter(is_deleted=0).filter(created_at__gte=start_date).filter(created_at__lte=last_day).all().count()
		if monthlyModel !=None or monthlyModel !="":
			monthlyModel	=	str(monthlyModel)
		else:
			monthlyModel	=	0
		model_month_arr.append(monthlyModel)

	model_month_arr	=	model_month_arr
	sub_month_arr	=	sub_month_arr
	for result in yearData:
		month_arr.append(result)
	month_arr	=	month_arr

	content = {
				"totalSubscriber": totalSubscriber,
				"totalModel":totalModel,
				"activeModel":activeModel,
				"approvedModel":approvedModel,
				"amountUSD":amountUSD,
				"amountAUD":amountAUD,
				"amountGBP":amountGBP,
				"amountEUR":amountEUR,
				"amountUSDPayment":amountUSDPayment,
				"amountAUDPayment":amountAUDPayment,
				"amountGBPPayment":amountGBPPayment,
				"amountEURPayment":amountEURPayment,
				"yearData":yearData,
				"yearDataPayment":yearDataPayment,
				"currency_list":currency_list,
				"month_arr":month_arr,
				"sub_month_arr":sub_month_arr,
				"model_month_arr":model_month_arr,
			}
	return render(request,"dashboard/index.html",content)
