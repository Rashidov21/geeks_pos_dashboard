from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import HasValidClientKey, IsSuperuser
from apps.api.serializers import (
    ActivateSerializer,
    AdminLicenseListSerializer,
    CheckStatusSerializer,
    SyncReportSerializer,
    UploadBackupSerializer,
    VerifyActivationKeySerializer,
)
from apps.licenses.models import ClientBackup, License, SystemLog


class AdminLicensePagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 500


def _build_status_payload(license_obj: License) -> dict:
    return {
        "status": license_obj.computed_status,
        "license_type": license_obj.license_type,
        "start_date": license_obj.start_date,
        "end_date": license_obj.end_date,
        "store": {
            "id": license_obj.store_id,
            "name": license_obj.store.name,
        },
    }


class VerifyActivationKeyView(APIView):
    """POS-safe: check one activation key exists and its status (no bulk list)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasValidClientKey]
    throttle_scope = "verify"

    def post(self, request):
        serializer = VerifyActivationKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["activation_key"]
        try:
            license_obj = License.objects.select_related("store").get(activation_key=key)
        except License.DoesNotExist:
            return Response({"detail": "Invalid activation key."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "exists": True,
                "status": license_obj.computed_status,
                "license_type": license_obj.license_type,
                "start_date": license_obj.start_date,
                "end_date": license_obj.end_date,
                "store": {"id": license_obj.store_id, "name": license_obj.store.name},
                "hardware_bound": bool(license_obj.hardware_id),
            },
            status=status.HTTP_200_OK,
        )


class ActivateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasValidClientKey]
    throttle_scope = "activate"

    def post(self, request):
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            license_obj = License.objects.select_related("store").get(activation_key=data["activation_key"])
        except License.DoesNotExist:
            return Response({"detail": "Invalid activation key."}, status=status.HTTP_404_NOT_FOUND)

        if license_obj.computed_status != "active":
            return Response({"detail": "License is not active."}, status=status.HTTP_400_BAD_REQUEST)

        if not license_obj.hardware_id:
            license_obj.hardware_id = data["hardware_id"]
            license_obj.save(update_fields=["hardware_id", "updated_at"])
        elif license_obj.hardware_id != data["hardware_id"]:
            SystemLog.objects.create(
                store=license_obj.store,
                license=license_obj,
                event_type=SystemLog.EventType.ERROR,
                payload={"reason": "hardware_mismatch"},
                source_ip=request.META.get("REMOTE_ADDR"),
            )
            return Response({"detail": "Hardware ID mismatch."}, status=status.HTTP_403_FORBIDDEN)

        SystemLog.objects.create(
            store=license_obj.store,
            license=license_obj,
            event_type=SystemLog.EventType.ACTIVATION,
            payload=data.get("client_meta", {}),
            source_ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(_build_status_payload(license_obj), status=status.HTTP_200_OK)


class CheckStatusView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasValidClientKey]
    throttle_scope = "status"

    def get(self, request):
        serializer = CheckStatusSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            license_obj = License.objects.select_related("store").get(activation_key=data["activation_key"])
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        if license_obj.hardware_id and license_obj.hardware_id != data["hardware_id"]:
            return Response({"detail": "Hardware ID mismatch."}, status=status.HTTP_403_FORBIDDEN)

        SystemLog.objects.create(
            store=license_obj.store,
            license=license_obj,
            event_type=SystemLog.EventType.LICENSE_CHECK,
            payload={"status": license_obj.computed_status},
            source_ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(_build_status_payload(license_obj), status=status.HTTP_200_OK)


class SyncReportView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasValidClientKey]
    throttle_scope = "sync"

    def post(self, request):
        serializer = SyncReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            license_obj = License.objects.select_related("store").get(activation_key=data["activation_key"])
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        if license_obj.hardware_id and license_obj.hardware_id != data["hardware_id"]:
            return Response({"detail": "Hardware ID mismatch."}, status=status.HTTP_403_FORBIDDEN)

        created_count = 0
        for event in data["events"]:
            _, created = SystemLog.objects.get_or_create(
                store=license_obj.store,
                client_event_id=event["client_event_id"],
                defaults={
                    "license": license_obj,
                    "event_type": event["event_type"],
                    "payload": event.get("payload", {}),
                    "client_timestamp": event.get("client_timestamp", timezone.now()),
                    "device_info": event.get("device_info", ""),
                    "source_ip": request.META.get("REMOTE_ADDR"),
                },
            )
            if created:
                created_count += 1

        return Response(
            {"received": len(data["events"]), "created": created_count},
            status=status.HTTP_200_OK,
        )


class UploadBackupView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, HasValidClientKey]
    throttle_scope = "backup"

    def post(self, request):
        serializer = UploadBackupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            license_obj = License.objects.select_related("store").get(activation_key=data["activation_key"])
        except License.DoesNotExist:
            return Response({"detail": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        if not license_obj.hardware_id:
            license_obj.hardware_id = data["hardware_id"]
            license_obj.save(update_fields=["hardware_id", "updated_at"])
        elif license_obj.hardware_id != data["hardware_id"]:
            return Response({"detail": "Hardware ID mismatch."}, status=status.HTTP_403_FORBIDDEN)

        backup_file = data["backup_file"]
        existing = ClientBackup.objects.filter(hardware_id=data["hardware_id"]).first()
        previous_name = existing.backup_file.name if existing and existing.backup_file else None

        backup_obj, created = ClientBackup.objects.update_or_create(
            hardware_id=data["hardware_id"],
            defaults={
                "store": license_obj.store,
                "license": license_obj,
                "backup_file": backup_file,
                "size_bytes": backup_file.size,
            },
        )

        # Ensure previous backup file is removed from disk.
        if previous_name and previous_name != backup_obj.backup_file.name:
            storage = backup_obj.backup_file.storage
            if storage.exists(previous_name):
                storage.delete(previous_name)

        SystemLog.objects.create(
            store=license_obj.store,
            license=license_obj,
            event_type=SystemLog.EventType.BACKUP_UPLOAD,
            payload={"size_bytes": backup_file.size, "created": created},
            source_ip=request.META.get("REMOTE_ADDR"),
            device_info=request.META.get("HTTP_USER_AGENT", "")[:255],
        )

        return Response(
            {
                "status": "created" if created else "updated",
                "hardware_id": backup_obj.hardware_id,
                "file_name": backup_obj.backup_file.name,
                "size_bytes": backup_obj.size_bytes,
                "uploaded_at": backup_obj.uploaded_at,
            },
            status=status.HTTP_200_OK,
        )


class AdminLicenseListView(ListAPIView):
    """Superuser-only: all licenses with activation_key and hardware_id."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsSuperuser, HasValidClientKey]
    serializer_class = AdminLicenseListSerializer
    pagination_class = AdminLicensePagination

    def list(self, request, *args, **kwargs):
        if not getattr(settings, "ADMIN_LICENSE_LIST_ENABLED", False):
            return Response(
                {"detail": "Admin license list is disabled. Set ADMIN_LICENSE_LIST_ENABLED=true in .env to enable."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return License.objects.select_related("store").order_by("-created_at")
