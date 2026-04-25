from django.test import TestCase

from apps.licenses.models import License
from apps.licenses.services import generate_license
from apps.stores.models import Store


class LicenseServiceTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(
            name="Store A",
            address="Address",
            owner_name="Owner",
            phone="+998901112233",
            contact_channel=Store.ContactChannel.TELEGRAM,
            contact_id="owner_telegram",
        )

    def test_generate_license_monthly(self):
        license_obj = generate_license(store=self.store, license_type=License.LicenseType.MONTHLY)
        self.assertEqual(license_obj.license_type, License.LicenseType.MONTHLY)
        self.assertIsNotNone(license_obj.end_date)
        self.assertTrue(license_obj.activation_key)

    def test_generate_license_deactivates_previous_active(self):
        first = generate_license(store=self.store, license_type=License.LicenseType.MONTHLY)
        second = generate_license(store=self.store, license_type=License.LicenseType.YEARLY)
        first.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)
