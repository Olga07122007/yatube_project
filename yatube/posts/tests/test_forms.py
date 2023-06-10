import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR))
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DIR)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='post_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_create_post(self):
        """Проверка создания поста авторизованного клиента"""
        post_count = Post.objects.count()
        url = reverse('posts:post_create')

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

        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), post_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Текст поста',
                author=self.user,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(
            self.authorized_client.get(url).status_code,
            HTTPStatus.OK
        )


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='post_author',
        )
        cls.group_1 = Group.objects.create(
            title='Группа 1',
            slug='group1-test-slug1',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='текст',
            author=PostEditFormTests.user,
            group=PostEditFormTests.group_1,
        )
        cls.group_2 = Group.objects.create(
            title='Группа 2',
            slug='test-slug2',
            description='Тестовое описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_author_edit_post(self):
        """Проверка редактирования поста автором"""
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
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

        form_data = {
            'text': 'Новый текст',
            'group': self.group_2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.filter(group=self.group_1).count(), 0)
        self.assertEqual(Post.objects.filter(group=self.group_2).count(), 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст',
                author=self.user,
                group=self.group_2,
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(
            self.authorized_client.get(url).status_code,
            HTTPStatus.OK
        )


class PostCommentTest(TestCase):
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
            author=PostCommentTest.user_post_author,
            group=PostCommentTest.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.user_post_author)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_authorized)

    def test_authorized_client_add_comment(self):
        """Проверка добавления комментария авторизованным клиентом"""
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id,
                }
            ),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id,
                }
            )
        )
        self.assertEqual(self.post.comments.count(), 1)

        comment_request = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id,
                }
            )
        )
        post = comment_request.context['post']
        comment = post.comments.all()[0]

        self.assertEqual(comment.text, 'Комментарий')
        self.assertEqual(comment.author, self.user_authorized)

    def test_guest_client_add_comment(self):
        """Проверка добавления комментария неавторизованным клиентом"""
        self.assertEqual(self.post.comments.count(), 0)
        form_data = {
            'text': 'Комментарий',
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id,
                }
            ),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        login_url = reverse('users:login')
        add_comment_url = reverse(
            'posts:add_comment',
            kwargs={
                'post_id': self.post.id,
            }
        )
        redirect = f'{login_url}?next={add_comment_url}'
        self.assertRedirects(response, redirect)
        self.assertEqual(self.post.comments.count(), 0)
