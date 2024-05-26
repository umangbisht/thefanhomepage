from django.contrib import admin
from django.urls import path,include
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path('api/(?P<version>(v1))/', include('apps.api.urls')),
    path('', include('apps.login.urls')),
    path('login/', include('apps.login.urls')),
	path('dashboard/', include('apps.dashboard.urls')),
    path('dropdown-managers/', include('apps.dropdownmanger.urls')),
    path('emailtemplates/', include('apps.emailtemplates.urls')),
    path('settings/', include('apps.settings.urls')),
    path('languages/', include('apps.languages.urls')),
    path('cmspages/', include('apps.cmspages.urls')),
    path('subscribers/', include('apps.users.urls')),
    path('models/', include('apps.users.model_urls')),
    path('email-logs/', include('apps.emaillogs.urls')),
    path('blocks/', include('apps.blocks.urls')),
    path('supports/', include('apps.supports.urls')),
    path('newsletters/', include('apps.newsletters.urls')),
    path('modelreports/', include('apps.modelreport.urls')),
    path('slider/', include('apps.slider.urls')),
    path('payout/', include('apps.payout.urls')),
    path('crons/', include('apps.cron.urls')),
    path('common/', include('apps.common.urls')),
    path('income-history/', include('apps.incomehistory.urls')),
    path('transactions/', include('apps.transactions.urls')),
	path('faq/', include('apps.faq.urls')),
    path('failed-transactions/', include('apps.failedtransactions.urls')),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
