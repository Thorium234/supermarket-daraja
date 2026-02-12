from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class OwnerDashboardAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="Pass12345", is_staff=True)
        self.customer = User.objects.create_user(username="customer", password="Pass12345")

    def test_owner_dashboard_requires_login(self):
        response = self.client.get(reverse("owner:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_owner_dashboard_for_staff_user(self):
        self.client.login(username="owner", password="Pass12345")
        response = self.client.get(reverse("owner:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_forbidden_for_non_staff(self):
        self.client.login(username="customer", password="Pass12345")
        response = self.client.get(reverse("owner:dashboard"))
        self.assertEqual(response.status_code, 403)
