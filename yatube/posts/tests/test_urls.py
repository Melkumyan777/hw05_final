from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='slug',
            description='Тестовое описание группы',
        )

        cls.user = User.objects.create_user(
            username='user')
        cls.user_2 = User.objects.create_user(
            username='user2')

        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(self.user)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user_2)
        cache.clear()

    def test_unauthorized_user_urls_HTTPStatus(self):
        """Проверка HTTPStatus для неавторизованного пользователя."""
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse(
                'posts:post_create'): HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse(
                'posts:follow_index'): HTTPStatus.FOUND,
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user}): HTTPStatus.FOUND,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user}): HTTPStatus.FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_authorized_user_urls_HTTPStatus(self):
        """Проверка HTTPStatus для авторизованного пользователя."""
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse(
                'posts:post_create'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}): HTTPStatus.FOUND,
            reverse(
                'posts:follow_index'): HTTPStatus.OK,
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user}): HTTPStatus.FOUND,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user}): HTTPStatus.FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_user.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.author.get(adress)
                self.assertTemplateUsed(response, template)
