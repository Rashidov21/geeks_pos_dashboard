from django.contrib import admin
from django.utils import timezone

from apps.licenses.models import License
from apps.licenses.services import generate_license
from apps.stores.models import Store


@admin.action(description="Generate monthly license")
def generate_monthly(modeladmin, request, queryset):
    for store in queryset:
        generate_license(store=store, license_type=License.LicenseType.MONTHLY, start_date=timezone.localdate())


@admin.action(description="Generate yearly license")
def generate_yearly(modeladmin, request, queryset):
    for store in queryset:
        generate_license(store=store, license_type=License.LicenseType.YEARLY, start_date=timezone.localdate())


@admin.action(description="Generate lifetime license")
def generate_lifetime(modeladmin, request, queryset):
    for store in queryset:
        generate_license(store=store, license_type=License.LicenseType.LIFETIME, start_date=timezone.localdate())


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_name", "phone", "contact_channel", "is_active", "created_at")
    list_filter = ("is_active", "contact_channel", "created_at")
    search_fields = ("name", "owner_name", "phone", "contact_id")
    actions = (generate_monthly, generate_yearly, generate_lifetime)
