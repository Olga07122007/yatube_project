from django.core.cache import cache
from django.test import TestCase

from ..models import Group, Post, User
from ..utils.constants import FIRST_CHARACTERS_OF_POST


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        cache.clear()
        post = self.post
        group = self.group

        str_objects = {
            post.text[:FIRST_CHARACTERS_OF_POST]: str(post),
            group.title: str(group),
        }
        for value, expected in str_objects.items():
            self.assertEqual(value, expected)

    def test_models_have_correct_verbose_name(self):
        """Проверяем, что у моделей корректно работает verbose_name"""
        cache.clear()
        post = self.post
        verbose_name_objects = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор заметки',
            'group': 'Группа',
        }

        for value, expected in verbose_name_objects.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_models_have_correct_help_text(self):
        """Проверяем, что у моделей корректно работает help_text"""
        cache.clear()
        post = self.post
        help_text_objects = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for value, expected in help_text_objects.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text,
                    expected
                )
