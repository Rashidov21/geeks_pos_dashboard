from django.contrib import admin

from apps.licenses.models import License, SystemLog


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("store", "license_type", "is_active", "start_date", "end_date", "hardware_id")
    list_filter = ("is_active", "license_type", "start_date", "end_date")
    search_fields = ("store__name", "activation_key", "hardware_id")


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ("store", "event_type", "received_at", "source_ip", "client_event_id")
    list_filter = ("event_type", "received_at")
    search_fields = ("store__name", "client_event_id", "device_info")
