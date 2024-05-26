from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("subscription-expires", views.subscriptionExpires, name='cron.cronjob'),
    path("check-discount-enabled-disabled", views.checkDiscountEnabledDisabled, name='cron.checkDiscountEnabledDisabled'),
    path("generate-payouts", views.generatePayout, name='cron.generatePayout'),
    path("save-currency-price", views.saveCurrencyPrice, name='cron.saveCurrencyPrice'),
    path("update-model-site-rank", views.updateModelSiteRank, name='cron.updateModelSiteRank'),
    path("status-publish-private-feeds", views.publishPrivateFeed, name='cron.publishPrivateFeed'),
    path("send-newletters", views.sendNewsletters, name='cron.sendNewsletters'),
    path("convert-video", views.ConvertedVideoPrivateFeed, name='cron.ConvertedVideoPrivateFeed'),
	
]
