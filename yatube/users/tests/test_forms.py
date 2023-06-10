import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import User


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_authorized_client_create_post(self):
        """Проверка создания поста авторизованного клиента"""
        url = reverse('users:signup')
        user_count = User.objects.count()
        form_data = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'логин',
            'email': 'test@mail.ru',
            'password1': '123AA123BB',
            'password2': '123AA123BB',
        }
        response = self.guest_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:posts_index'))
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='Имя',
                last_name='Фамилия',
                username='логин',
                email='test@mail.ru',
            ).exists()
        )
        self.assertEqual(
            self.guest_client.get(url).status_code,
            HTTPStatus.OK
        )
