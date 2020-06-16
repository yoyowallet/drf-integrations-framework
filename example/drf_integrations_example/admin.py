from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Organisation)
admin.site.register(models.IntegrationUser)
admin.site.register(models.UserPurchase)
