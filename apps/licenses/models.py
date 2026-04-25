from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.stores.models import Store


class License(models.Model):
    class LicenseType(models.TextChoices):
        MONTHLY = "monthly", "1 month"
        YEARLY = "yearly", "1 year"
        LIFETIME = "lifetime", "Lifetime"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="licenses")
    activation_key = models.CharField(max_length=128, unique=True)
    license_type = models.CharField(max_length=20, choices=LicenseType.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    hardware_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store"],
                condition=Q(is_active=True),
                name="unique_active_license_per_store",
            ),
        ]
        ordering = ["-created_at"]

    @property
    def computed_status(self) -> str:
        if not self.is_active:
            return "blocked"
        if self.end_date and self.end_date < timezone.localdate():
            return "expired"
        return "active"

    def __str__(self) -> str:
        return f"{self.store.name} - {self.license_type}"


class SystemLog(models.Model):
    class EventType(models.TextChoices):
        LICENSE_CHECK = "license_check", "License check"
        ACTIVATION = "activation", "Activation"
        Z_REPORT_SYNC = "z_report_sync", "Z-report sync"
        ERROR = "error", "Error"

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="system_logs")
    license = models.ForeignKey(
        License, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    payload = models.JSONField(default=dict, blank=True)
    client_timestamp = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, blank=True)
    client_event_id = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "client_event_id"],
                condition=Q(client_event_id__isnull=False),
                name="uniq_store_client_event_id",
            )
        ]

    def __str__(self) -> str:
        return f"{self.store.name} - {self.event_type}"
