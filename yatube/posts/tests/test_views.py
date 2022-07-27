
import tempfile
import shutil

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Comment
from posts.models import Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_commentator = User.objects.create_user(
            username='user_commentator'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_authorized_user_create_post(self):
        """Проверка создания записи авторизированным пользователем."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, form_data['group'])
        self.assertEqual(post.image.name, 'posts/small.gif')

    def test_authorized_user_create_comment(self):
        """Проверка создания коментария авторизированным пользователем."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст',
            author=self.user)
        form_data = {'text': 'Тестовый коментарий'}
        response = self.user_commentator.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}),
            data=form_data,
            follow=True)
        comment = Comment.objects.latest('id')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.comm_author)
        self.assertEqual(comment.post_id, post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail', args={post.id}))

    def check_context(self, context):
        with self.subTest(context=context):
            self.assertEqual(context.text, self.post.text)
            self.assertEqual(context.author, self.post.author)
            self.assertEqual(context.group.id, self.post.group.id)

    def test_cache(self):
        """Проверка работы кеша"""
        post = Post.objects.create(
            text='Текст',
            author=self.user)
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_cache_clear)

    def test_forms_correct(self):
        """Проверка коректности формы."""
        context = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_context(response.context['page_obj'][0])

    def test_groups_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_context(response.context['page_obj'][0])

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        self.assertEqual(response.context['author'], self.user)
        self.check_context(response.context['page_obj'][0])

    def test_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))
        self.check_context(response.context['post'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='slug',
            description='Тестовое описание группы',
        )
        for i in range(14):
            Post.objects.create(
                text=f'Пост №{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_on_pages(self):
        first_page = settings.FOR_PAGINATOR
        second_page = Post.objects.count() % first_page
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverse_page in url_pages:
            with self.subTest(reverse=reverse_page):
                self.assertEqual(len(self.guest_client.get(
                    reverse_page).context.get('page_obj')),
                    first_page
                )
                self.assertEqual(len(self.guest_client.get(
                    reverse_page + '?page=2').context.get('page_obj')),
                    second_page
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='user',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.post = Post.objects.create(
            text='Подпишитесь',
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.user)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.follower.id)
        self.assertEqual(follow.user_id, self.user.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.user,
            author=self.follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            author=self.user,
            text="Подпишитесь")
        Follow.objects.create(
            user=self.follower,
            author=self.user)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.user,
            text="Подпишитесь")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)