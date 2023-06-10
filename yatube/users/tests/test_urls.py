from http import HTTPStatus

from django.core.cache import cache
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_authorized = User.objects.create_user(
            username='authorized_user'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_guest_client_urls_exists_at_desired_location(self):
        """Проверяем доступность страниц неавторизованного пользователя"""
        guest_client_urls = {
            reverse('users:signup'): HTTPStatus.OK,
            reverse('users:login'): HTTPStatus.OK,
            reverse('users:password_change'): HTTPStatus.FOUND,
            reverse('users:password_reset'): HTTPStatus.OK,
            reverse('users:logout'): HTTPStatus.OK,
        }
        for url, response_status_code in guest_client_urls.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    response_status_code
                )

    def test_authorized_client_urls_exists_at_desired_location(self):
        """Проверяем доступность страниц авторизованного пользователя"""
        authorized_client_urls = {
            reverse('users:signup'): HTTPStatus.OK,
            reverse('users:login'): HTTPStatus.OK,
            reverse('users:password_change'): HTTPStatus.OK,
            reverse('users:password_reset'): HTTPStatus.OK,
            reverse('users:logout'): HTTPStatus.OK,
        }
        for url, response_status_code in authorized_client_urls.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client.get(url).status_code,
                    response_status_code
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_url_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse(
                'users:password_change'
            ): 'users/password_change_form.html',
            reverse('users:password_reset'): 'users/password_reset_form.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_anonymous_on_login(self):
        """Перенаправление анонимного пользователя на страницу логина"""
        url = reverse('users:password_change')
        response = self.guest_client.get(
            url,
            follow=True
        )
        login_url = reverse('users:login')

        self.assertRedirects(
            response,
            f'{login_url}?next={url}'
        )
