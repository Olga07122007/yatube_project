from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        cache.clear()
        response = self.client.get('/nonexist-page/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.NOT_FOUND
        )
        self.assertTemplateUsed(response, 'core/404.html')
