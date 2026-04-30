import os
import tempfile

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.licenses.models import ClientBackup, License
from apps.licenses.services import generate_license
from apps.stores.models import Store


@override_settings(ROOT_URLCONF="core.urls")
class ApiEndpointTests(APITestCase):
    def setUp(self):
        os.environ["CLIENT_API_KEY"] = "test-client-key"
        self.user = get_user_model().objects.create_user(username="apiuser", password="pass1234")
        token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
            HTTP_X_CLIENT_KEY="test-client-key",
        )
        self.store = Store.objects.create(
            name="Store API",
            address="Address",
            owner_name="Owner",
            phone="+998901112244",
            contact_channel=Store.ContactChannel.WHATSAPP,
            contact_id="99890",
        )
        self.license = generate_license(store=self.store, license_type=License.LicenseType.MONTHLY)

    def test_activate_success(self):
        response = self.client.post(
            "/api/v1/activate/",
            {"activation_key": self.license.activation_key, "hardware_id": "HW-1"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_check_status_success(self):
        self.license.hardware_id = "HW-1"
        self.license.save(update_fields=["hardware_id"])
        response = self.client.get(
            "/api/v1/check-status/",
            {"activation_key": self.license.activation_key, "hardware_id": "HW-1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "active")

    def test_sync_report_idempotent(self):
        self.license.hardware_id = "HW-1"
        self.license.save(update_fields=["hardware_id"])
        payload = {
            "activation_key": self.license.activation_key,
            "hardware_id": "HW-1",
            "events": [
                {"client_event_id": "evt-1", "event_type": "z_report_sync", "payload": {"total": 10}}
            ],
        }
        first = self.client.post("/api/v1/sync-report/", payload, format="json")
        second = self.client.post("/api/v1/sync-report/", payload, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["created"], 1)
        self.assertEqual(second.data["created"], 0)

    def test_admin_licenses_forbidden_for_non_superuser(self):
        with self.settings(ADMIN_LICENSE_LIST_ENABLED=True):
            response = self.client.get("/api/v1/admin/licenses/")
        self.assertEqual(response.status_code, 403)

    def test_admin_licenses_ok_for_superuser(self):
        admin = get_user_model().objects.create_superuser(
            username="adminapi", email="a@a.com", password="pw"
        )
        admin_token = Token.objects.create(user=admin)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {admin_token.key}",
            HTTP_X_CLIENT_KEY="test-client-key",
        )
        with self.settings(ADMIN_LICENSE_LIST_ENABLED=True):
            response = self.client.get("/api/v1/admin/licenses/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        row = response.data["results"][0]
        self.assertIn("activation_key", row)
        self.assertIn("hardware_id", row)

    def test_admin_licenses_disabled_returns_403(self):
        admin = get_user_model().objects.create_superuser(
            username="adminapi2", email="b@b.com", password="pw"
        )
        admin_token = Token.objects.create(user=admin)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {admin_token.key}",
            HTTP_X_CLIENT_KEY="test-client-key",
        )
        with self.settings(ADMIN_LICENSE_LIST_ENABLED=False):
            response = self.client.get("/api/v1/admin/licenses/")
        self.assertEqual(response.status_code, 403)

    def test_verify_activation_key_ok(self):
        response = self.client.post(
            "/api/v1/verify-activation-key/",
            {"activation_key": self.license.activation_key},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["exists"])
        self.assertEqual(response.data["status"], "active")
        self.assertFalse(response.data["hardware_bound"])

    def test_verify_activation_key_not_found(self):
        response = self.client.post(
            "/api/v1/verify-activation-key/",
            {"activation_key": "invalid-key-xxxxxxxxxxxxxxxx"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_upload_backup_create_and_replace(self):
        tmp_media = tempfile.mkdtemp(prefix="media_test_")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp_media, ignore_errors=True))
        self.license.hardware_id = "HW-1"
        self.license.save(update_fields=["hardware_id"])

        first_file = SimpleUploadedFile("backup1.db", b"first backup data", content_type="application/octet-stream")
        second_file = SimpleUploadedFile("backup2.db", b"second backup data", content_type="application/octet-stream")

        with self.settings(MEDIA_ROOT=tmp_media):
            first = self.client.post(
                "/api/v1/upload-backup/",
                {"activation_key": self.license.activation_key, "hardware_id": "HW-1", "backup_file": first_file},
                format="multipart",
            )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["status"], "created")

        with self.settings(MEDIA_ROOT=tmp_media):
            second = self.client.post(
                "/api/v1/upload-backup/",
                {"activation_key": self.license.activation_key, "hardware_id": "HW-1", "backup_file": second_file},
                format="multipart",
            )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["status"], "updated")

        self.assertEqual(ClientBackup.objects.count(), 1)
        backup = ClientBackup.objects.get(hardware_id="HW-1")
        self.assertIn("backup2", backup.backup_file.name)

    def test_upload_backup_hardware_mismatch(self):
        self.license.hardware_id = "HW-LOCKED"
        self.license.save(update_fields=["hardware_id"])
        file_obj = SimpleUploadedFile("backup.db", b"abc", content_type="application/octet-stream")
        response = self.client.post(
            "/api/v1/upload-backup/",
            {"activation_key": self.license.activation_key, "hardware_id": "HW-1", "backup_file": file_obj},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)
