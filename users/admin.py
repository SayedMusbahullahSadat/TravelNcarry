# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Rating
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'username', 'user_type', 'is_verified', 'average_rating', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff')

    # Modify fieldsets to ensure required fields are included
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('User Profile', {'fields': (
        'user_type', 'phone_number', 'bio', 'profile_picture', 'address', 'average_rating', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Modify add_fieldsets to include user_type
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
        }),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Rating)