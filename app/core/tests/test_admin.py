from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        """function to set-up test case class before testing"""
        self.client = Client()
        # create admin user for test
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@comgrow.com",
            password="admin123"
        )
        # log admin in
        self.client.force_login(self.admin_user)
        # create normal user for test
        self.user = get_user_model().objects.create_user(
            email="test@comgrow.com",
            password="testing123",
            name="Test user full name"
        )

    def test_users_listed(self):
        """Test that users are listed on user page"""
        url = reverse('admin:core_user_changelist')  # <app>:<url>
        res = self.client.get(url)  # HTTP get

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        # /admin/core/user
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        # test page renders corectly
        self.assertEqual(res.status_code, 200)  # HTTP OK

    def test_create_user_page(self):
        """Test that the create user page works"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)  # HTTP OK
