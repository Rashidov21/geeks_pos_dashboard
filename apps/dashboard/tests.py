from django.test import TestCase
from django.urls import reverse


class DashboardPermissionTests(TestCase):
    def test_login_required(self):
        response = self.client.get(reverse("dashboard-home"))
        self.assertEqual(response.status_code, 302)

# Create your tests here.
