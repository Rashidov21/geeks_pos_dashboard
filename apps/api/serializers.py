from rest_framework import serializers

from apps.licenses.models import SystemLog


class ActivateSerializer(serializers.Serializer):
    activation_key = serializers.CharField(max_length=128)
    hardware_id = serializers.CharField(max_length=255)
    client_meta = serializers.DictField(required=False)


class CheckStatusSerializer(serializers.Serializer):
    activation_key = serializers.CharField(max_length=128)
    hardware_id = serializers.CharField(max_length=255)


class SyncEventSerializer(serializers.Serializer):
    client_event_id = serializers.CharField(max_length=120)
    event_type = serializers.ChoiceField(choices=SystemLog.EventType.choices)
    payload = serializers.DictField(required=False)
    client_timestamp = serializers.DateTimeField(required=False)
    device_info = serializers.CharField(required=False, allow_blank=True)


class SyncReportSerializer(serializers.Serializer):
    activation_key = serializers.CharField(max_length=128)
    hardware_id = serializers.CharField(max_length=255)
    events = SyncEventSerializer(many=True)
