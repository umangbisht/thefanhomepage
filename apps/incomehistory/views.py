from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,Payout
from apps.dropdownmanger.models import DropDownManager 
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
from django.db.models import Count,Sum


# Create your views here.
VALID_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "gif",
]



@login_required(login_url='/login')
def indexIncomeHistory(request):
    # userDetail =    User.objects.all().values("id")
    dateFormat  =   settings.READINGDATE_FORMAT
    DB = Payout.objects.filter(is_paid=1).all()

    if request.GET.get('model_name'):
        model_name= request.GET.get('model_name').strip()
        DB = DB.filter(model__model_name= model_name)
        
    if request.GET.get('created_at'):
        created_at= request.GET.get('created_at').strip()
        DB = DB.filter(created_at= created_at)
    
    if request.GET.get('start_date') and request.GET.get('end_date'):
        DB 			= DB.filter(created_at__gte=request.GET.get('start_date')+" 00:00:00")
        DB 			= DB.filter(created_at__lte=request.GET.get('end_date')+" 23:59:59")
    elif request.GET.get('start_date'):
        DB 			= DB.filter(created_at__gte=request.GET.get('start_date')+" 00:00:00")
    elif request.GET.get('end_date'):
        DB 			= DB.filter(created_at__lte=request.GET.get('end_date')+" 23:59:59")
    
    if request.GET.get('currency'):
        DB = DB.filter(currency=request.GET.get('currency'))
		

	
    order_by	=	request.GET.get('order_by',"created_at")
    direction	=	request.GET.get('direction',"DESC")
    if direction == "DESC":
        DB = DB.order_by("-"+order_by).all()
    else:
        DB = DB.order_by(order_by).all()
    recordPerPge    =	settings.READINGRECORDPERPAGE
    page = request.GET.get('page', 1)
    paginator = Paginator(DB, recordPerPge)
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)
		
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
    amountUSD   =   Payout.objects.filter(is_paid=1).filter(currency='USD').all().aggregate(Sum('commission_amount'))
    if amountUSD['commission_amount__sum']==None or amountUSD['commission_amount__sum'] =="":
        amountUSD   =   0.0
    else:
        amountUSD   =   amountUSD['commission_amount__sum']
    amountAUD   =   Payout.objects.filter(is_paid=1).filter(currency='AUD').all().aggregate(Sum('commission_amount'))
    if amountAUD['commission_amount__sum']==None or amountAUD['commission_amount__sum'] =="":
        amountAUD   =   0.0
    else:
        amountAUD   =   amountAUD['commission_amount__sum']
    amountGBP   =   Payout.objects.filter(is_paid=1).filter(currency='GBR').all().aggregate(Sum('commission_amount'))
    if amountGBP['commission_amount__sum']==None or amountGBP['commission_amount__sum'] =="":
        amountGBP   =   0.0
    else:
        amountGBP   =   amountGBP['commission_amount__sum']
    amountEUR   =   Payout.objects.filter(is_paid=1).filter(currency='EUR').all().aggregate(Sum('commission_amount'))
    if amountEUR['commission_amount__sum']==None or amountEUR['commission_amount__sum'] =="":
        amountEUR   =   0.0
    else:
        amountEUR   =   amountEUR['commission_amount__sum']
    context		=	{
        'results': results,
        'amountUSD':amountUSD,
        'amountAUD':amountAUD,
        'amountGBP':amountGBP,
        'amountEUR':amountEUR,
        'page': page,
        'order_by': order_by,
        'direction': direction,
        'searchingVariables': searchingVariables,
        'querySring': querySring,
        'page_range': page_range,
        'dateFormat': dateFormat
    }
    return render(request, "incomehistory/index.html",context)
