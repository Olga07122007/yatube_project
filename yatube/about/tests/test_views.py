from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_guest_client_urls_exists_at_desired_location(self):
        """Проверяем доступность страниц неавторизованного пользователя"""
        guest_client_urls = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for url, response_status_code in guest_client_urls.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.guest_client.get(url).status_code,
                    response_status_code
                )
