from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.licenses.models import License
from apps.stores.models import Store


class DashboardPermissionTests(TestCase):
    def test_login_required(self):
        response = self.client.get(reverse("dashboard-home"))
        self.assertEqual(response.status_code, 302)

    def test_stores_list_requires_login(self):
        response = self.client.get(reverse("stores-list"))
        self.assertEqual(response.status_code, 302)

    def test_non_superuser_redirected_from_dashboard(self):
        user = get_user_model().objects.create_user(username="u1", password="pw", is_superuser=False)
        self.client.login(username="u1", password="pw")
        response = self.client.get(reverse("dashboard-home"))
        self.assertEqual(response.status_code, 403)


class AssignLicenseViewTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="a@a.com", password="adminpass"
        )
        self.store = Store.objects.create(
            name="S1",
            address="Addr",
            owner_name="O",
            phone="+998901112255",
            contact_channel=Store.ContactChannel.TELEGRAM,
            contact_id="t1",
        )

    def test_assign_license_creates_row(self):
        self.client.login(username="admin", password="adminpass")
        url = reverse("assign-license")
        next_url = reverse("dashboard-home")
        response = self.client.post(
            url,
            {
                "store_id": str(self.store.pk),
                "license_type": License.LicenseType.MONTHLY,
                "next": next_url,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            License.objects.filter(store=self.store, license_type=License.LicenseType.MONTHLY).exists()
        )
