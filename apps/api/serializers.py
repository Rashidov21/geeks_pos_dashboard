from rest_framework import serializers

from apps.licenses.models import License, SystemLog


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


class AdminLicenseListSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    computed_status = serializers.SerializerMethodField()

    def get_computed_status(self, obj: License) -> str:
        return obj.computed_status

    class Meta:
        model = License
        fields = (
            "id",
            "store_id",
            "store_name",
            "activation_key",
            "hardware_id",
            "license_type",
            "is_active",
            "computed_status",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        )
