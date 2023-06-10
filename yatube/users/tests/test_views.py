from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_post_author = User.objects.create_user(
            username='authorized_user'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user_post_author)

    def test_forms_show_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        reverse_name = reverse('users:signup')
        response = self.authorized_user.get(reverse_name)

        self.assertIsInstance(
            response.context['form'].fields['first_name'],
            forms.fields.CharField
        )
        self.assertIsInstance(
            response.context['form'].fields['last_name'],
            forms.fields.CharField
        )
        self.assertIsInstance(
            response.context['form'].fields['username'],
            forms.fields.CharField
        )
        self.assertIsInstance(
            response.context['form'].fields['email'],
            forms.fields.EmailField
        )
