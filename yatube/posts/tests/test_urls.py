from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user_post_author = User.objects.create_user(
            username='post_author'
        )
        cls.user_authorized = User.objects.create_user(
            username='authorized_user'
        )
        cls.post = Post.objects.create(
            text='текст',
            author=StaticPagesURLTests.user_post_author,
            group=StaticPagesURLTests.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_post_author)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_guest_client_urls_exists_at_desired_location(self):
        """Проверяем доступность страниц неавторизованного пользователя"""
        guest_client_urls = {
            reverse('posts:posts_index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': 'post_author'}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): HTTPStatus.OK,
            '/no-page/': HTTPStatus.NOT_FOUND,
            reverse('posts:post_create'): HTTPStatus.FOUND,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): HTTPStatus.FOUND,
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
            reverse('posts:posts_index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': 'post_author'}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): HTTPStatus.OK,
            '/no-page/': HTTPStatus.NOT_FOUND,
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): HTTPStatus.FOUND,
        }
        for url, response_status_code in authorized_client_urls.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.authorized_client.get(url).status_code,
                    response_status_code
                )

    def test_post_author_edit_exists_at_desired_location(self):
        """Проверяем возможность редактирования поста автором"""
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': '1'}
        )
        response = self.post_author.get(url).status_code
        self.assertEqual(response, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_url_names = {
            reverse('posts:posts_index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'post_author'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_anonymous_on_login(self):
        """Перенаправление анонимного пользователя на страницу логина"""
        login_url = reverse('users:login')
        post_url_create = reverse('posts:post_create')
        post_url_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': '1'}
        )
        redirect_url_names = {
            post_url_create: f'{login_url}?next={post_url_create}',
            post_url_edit: f'{login_url}?next={post_url_edit}',
        }

        for url, redirect in redirect_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_post_edit_redirect_authorized_client_on_post_detail(self):
        """Перенаправление авторизованного пользователя на страницу поста"""
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': '1'}
        )
        redirect_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': '1'}
        )
        response = self.authorized_client.get(url, follow=True)
        self.assertRedirects(
            response, redirect_url
        )
