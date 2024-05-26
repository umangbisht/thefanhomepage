from django.test import TestCase, Client
from django.urls import reverse 
# from django.contrib.auth import User

class TestView(TestCase):
    def test_users_list_get(self):
        client = Client()
        response = client.get(reverse('users.add_subscriber'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "subscribers/index.html")