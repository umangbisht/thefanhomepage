from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import User,ModelImages,ModelCategories,ModelSubscriptions,ModelSubscriptionPlans,Payout,TransactionHistory,PaymentGatewayErrors
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
    DB = PaymentGatewayErrors.objects.filter(model_user__is_deleted= 0).filter(user__is_deleted= 0).all()
    if request.GET.get('model_name'):
        model_name= request.GET.get('model_name').strip()
        DB = DB.filter(model_user__model_name__icontains= model_name).filter(model_user__is_deleted= 0)
    
    if request.GET.get('subscriber_name'):
        subscriber_name= request.GET.get('subscriber_name').strip()
        DB = DB.filter(email__icontains= subscriber_name).filter(user__is_deleted= 0)

    # if request.GET.get('started_at'):
    #     started_at= request.GET.get('started_at').strip()
    #     DB = DB.filter(created_at__gte= started_at)

    # if request.GET.get('ended_at'):
    #     ended_at= request.GET.get('ended_at').strip()
    #     DB = DB.filter(created_at__lte= ended_at)

    # if request.GET.get('transaction_type'):
    #     transaction_type= request.GET.get('transaction_type').strip()
    #     DB = DB.filter(transaction_type__icontains= transaction_type)
		

	
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
        'datetimeFormat':datetimeFormat,
        'direction': direction,
        'searchingVariables': searchingVariables,
        'querySring': querySring,
        'page_range': page_range,
    }
    return render(request, "failedtransaction/index.html",context)