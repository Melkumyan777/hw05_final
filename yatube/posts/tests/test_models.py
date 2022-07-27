from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names_title(self):
        """Тестирование вывода __str__"""
        expected_group_title = self.group.title
        self.assertEqual(expected_group_title, str(self.group))

    def test_models_have_correct_object_names_text(self):
        """Тестирование вывода __str__"""
        expected_post_text = self.post.text[:15]
        self.assertEqual(expected_post_text, str(self.post))
