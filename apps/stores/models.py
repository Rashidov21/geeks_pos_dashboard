from django.core.validators import RegexValidator
from django.db import models


class Store(models.Model):
    class ContactChannel(models.TextChoices):
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    name = models.CharField(max_length=255)
    address = models.TextField()
    owner_name = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^\+?[0-9]{9,15}$", "Enter a valid phone number.")],
    )
    contact_channel = models.CharField(max_length=20, choices=ContactChannel.choices)
    contact_id = models.CharField(max_length=120, help_text="Telegram/WhatsApp user or chat id")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "phone"], name="uniq_store_name_phone"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"
