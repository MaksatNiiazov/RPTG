from django.contrib import admin
from unfold.admin import ModelAdmin
# Register your models here.

from .models import User

@admin.register(User)
class UserAdmin(ModelAdmin):
    pass