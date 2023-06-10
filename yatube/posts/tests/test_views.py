import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Другая группа',
            slug='else-slug',
            description='Тестовое описание',
        )
        cls.user_post_author = User.objects.create_user(
            username='post_author'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='текст',
            author=StaticPagesURLTests.user_post_author,
            group=StaticPagesURLTests.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_post_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
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
            ): 'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        reverse_name = reverse('posts:posts_index')
        object = self.post
        response = self.post_author.get(reverse_name)

        page_obj = response.context['page_obj'][0]

        self.assertEqual(page_obj.text, object.text)
        self.assertEqual(page_obj.pub_date, object.pub_date)
        self.assertEqual(page_obj.author, object.author)
        self.assertEqual(page_obj.group, object.group)
        self.assertEqual(page_obj.image, object.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        reverse_name = reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'}
        )
        object = self.post
        response = self.post_author.get(reverse_name)

        page_obj = response.context['page_obj'][0]
        group = response.context['group']

        self.assertEqual(page_obj.text, object.text)
        self.assertEqual(page_obj.pub_date, object.pub_date)
        self.assertEqual(page_obj.author, object.author)
        self.assertEqual(page_obj.group, object.group)
        self.assertEqual(page_obj.image, object.image)
        self.assertEqual(group, object.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        reverse_name = reverse(
            'posts:profile',
            kwargs={'username': 'post_author'}
        )
        object = self.post
        response = self.post_author.get(reverse_name)

        page_obj = response.context['page_obj'][0]
        author = response.context['author']

        self.assertEqual(page_obj.text, object.text)
        self.assertEqual(page_obj.pub_date, object.pub_date)
        self.assertEqual(page_obj.author, object.author)
        self.assertEqual(page_obj.group, object.group)
        self.assertEqual(page_obj.image, object.image)
        self.assertEqual(author, object.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        reverse_name = reverse('posts:post_detail', kwargs={'post_id': '1'})
        object = self.post
        response = self.post_author.get(reverse_name)

        page_obj = response.context['post']
        author = response.context['author']

        self.assertEqual(page_obj.text, object.text)
        self.assertEqual(page_obj.pub_date, object.pub_date)
        self.assertEqual(page_obj.author, object.author)
        self.assertEqual(page_obj.group, object.group)
        self.assertEqual(page_obj.image, object.image)
        self.assertEqual(author, str(object.author))

    def test_forms_show_correct_context(self):
        """Шаблоны post_create и post_edit сформированы
        с правильным контекстом."""
        reverse_names = {
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ),
        }
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField
                )
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField
                )
                self.assertIsInstance(
                    response.context['form'].fields['image'],
                    forms.fields.ImageField
                )

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        object = self.post

        response_index = self.post_author.get(
            reverse('posts:posts_index')
        )
        response_group = self.post_author.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )
        )
        response_profile = self.post_author.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'post_author'}
            )
        )
        response_another_group = self.post_author.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'else-slug'}
            )
        )
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        another_group = response_another_group.context['page_obj']

        self.assertIn(object, index, 'поста нет на главной')
        self.assertIn(object, group, 'поста нет в группе')
        self.assertIn(object, profile, 'поста нет в профиле')
        self.assertNotIn(object, another_group)


class PaginatorViewsTest(TestCase):
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

        cls.post = [
            Post.objects.create(
                text='Post ' + str(i),
                group=PaginatorViewsTest.group,
                author=PaginatorViewsTest.user_post_author,
            ) for i in range(13)
        ]

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_post_author)

    def test_paginator_on_pages(self):
        """Тестируем паджинатор - количество записей на странице"""
        FIRST_PAGE_LEN = 10
        SECOND_PAGE_LEN = 3
        pages = {
            reverse('posts:posts_index'):
            FIRST_PAGE_LEN,

            reverse('posts:posts_index') + '?page=2':
            SECOND_PAGE_LEN,

            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
            FIRST_PAGE_LEN,

            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
            + '?page=2':
            SECOND_PAGE_LEN,

            reverse('posts:profile', kwargs={'username': 'post_author'}):
            FIRST_PAGE_LEN,

            reverse('posts:profile', kwargs={'username': 'post_author'})
            + '?page=2':
            SECOND_PAGE_LEN,
        }
        for page, len_posts in pages.items():
            with self.subTest(reverse=reverse):
                self.assertEqual(
                    len(self.post_author.get(page).context.get('page_obj')),
                    len_posts
                )


class CacheIndexTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='post_author',
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Проверка кэша для главной страницы"""
        first_content = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        Post.objects.create(
            text='Текст',
            author=self.user,
        )
        second_content = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        self.assertEqual(first_content, second_content)
        cache.clear()
        third_content = self.authorized_client.get(
            reverse('posts:posts_index')
        ).content
        self.assertNotEqual(second_content, third_content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='post_author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.not_follower = User.objects.create(
            username='not_follower',
        )
        cls.post = Post.objects.create(
            author=FollowTest.author,
            text='текст',
        )

    def setUp(self):
        cache.clear()
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)

        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow(self):
        '''Проверяем возможность подписаться/отписаться от автора'''
        response = self.follower_client.get(reverse('posts:follow_index'))
        follow = response.context['page_obj']
        self.assertEqual((len(follow)), 0)
        # подписываемся
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        else_response = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        follow = response.context['page_obj']
        not_follow = else_response.context['page_obj']
        object = self.post

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual((len(follow)), 1)
        self.assertIn(object, follow, 'поста нет в подписках подписчика')
        self.assertNotIn(
            object,
            not_follow,
            'пост в подписках у того, кто не подписан на автора'
        )

        # отписываемся
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            )
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        follow = response.context['page_obj']
        object = self.post

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual((len(follow)), 0)
        self.assertNotIn(object, follow)
