import json

from django.test import TestCase
from django.test import RequestFactory
from django.test.client import MULTIPART_CONTENT
from rest_framework import status

from bothub.common.models import RepositoryCategory
from bothub.common.models import Repository
from bothub.common.models import RequestRepositoryAuthorization
from bothub.common.models import RepositoryExample
from bothub.common import languages

from ..tests.utils import create_user_and_token

from .views import RepositoryViewSet
from .serializers import RepositorySerializer


def get_valid_mockups(categories):
    return [
        {
            'name': 'Repository 1',
            'slug': 'repository-1',
            'language': languages.LANGUAGE_EN,
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': True,
        },
        {
            'name': 'Repository 2',
            'slug': 'repo2',
            'language': languages.LANGUAGE_PT,
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': False,
        },
    ]


def get_invalid_mockups(categories):
    return [
        {
            'name': '',
            'slug': 'repository-1',
            'language': languages.LANGUAGE_EN,
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': True,
        },
        {
            'name': 'Repository 2',
            'slug': '',
            'language': languages.LANGUAGE_PT,
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': False,
        },
        {
            'name': 'Repository 3',
            'slug': 'repo3',
            'language': 'out',
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': False,
        },
        {
            'name': 'Repository 4',
            'slug': 'repository 4',
            'language': languages.LANGUAGE_EN,
            'categories': [
                category.pk
                for category in categories
            ],
            'is_private': True,
        },
    ]


def create_repository_from_mockup(owner, categories, **mockup):
    r = Repository.objects.create(
        owner_id=owner.id,
        **mockup)
    for category in categories:
        r.categories.add(category)
    return r


class CreateRepositoryAPITestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.owner, self.owner_token = create_user_and_token('owner')
        self.user, self.user_token = create_user_and_token('user')
        self.category = RepositoryCategory.objects.create(name='Category 1')

    def request(self, data, token=None):
        authorization_header = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key),
        } if token else {}

        request = self.factory.post(
            '/api/v2/repository/',
            data,
            **authorization_header)

        response = RepositoryViewSet.as_view({'post': 'create'})(request)
        response.render()
        content_data = json.loads(response.content)
        return (response, content_data,)

    def test_okay(self):
        for mockup in get_valid_mockups([self.category]):
            response, content_data = self.request(
                mockup,
                self.owner_token)

            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED)

            repository = self.owner.repositories.get(
                uuid=content_data.get('uuid'))

            self.assertEqual(
                repository.name,
                mockup.get('name'))
            self.assertEqual(
                repository.slug,
                mockup.get('slug'))
            self.assertEqual(
                repository.language,
                mockup.get('language'))
            self.assertEqual(
                repository.is_private,
                mockup.get('is_private'))

    def test_invalid_data(self):
        for mockup in get_invalid_mockups([self.category]):
            response, content_data = self.request(
                mockup,
                self.owner_token)

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST)


class RetriveRepositoryTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.owner, self.owner_token = create_user_and_token('owner')
        self.category = RepositoryCategory.objects.create(name='Category 1')

        self.repositories = [
            create_repository_from_mockup(self.owner, **mockup)
            for mockup in get_valid_mockups([self.category])
        ]

    def request(self, repository, token=None):
        authorization_header = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key),
        } if token else {}

        request = self.factory.get(
            '/api/v2/repository/{}/'.format(repository.uuid),
            **authorization_header)

        response = RepositoryViewSet.as_view({'get': 'retrieve'})(
            request,
            uuid=repository.uuid)
        response.render()
        content_data = json.loads(response.content)
        return (response, content_data,)

    def test_okay(self):
        for repository in self.repositories:
            response, content_data = self.request(repository, self.owner_token)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK)

    def test_private_repository(self):
        for repository in self.repositories:
            response, content_data = self.request(repository)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED
                if repository.is_private else status.HTTP_200_OK)


class UpdateRepositoryTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.owner, self.owner_token = create_user_and_token('owner')
        self.user, self.user_token = create_user_and_token('user')
        self.category = RepositoryCategory.objects.create(name='Category 1')

        self.repositories = [
            create_repository_from_mockup(self.owner, **mockup)
            for mockup in get_valid_mockups([self.category])
        ]

    def request(self, repository, data={}, token=None):
        authorization_header = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key),
        } if token else {}

        request = self.factory.patch(
            '/api/v2/repository/{}/'.format(repository.uuid),
            self.factory._encode_data(data, MULTIPART_CONTENT),
            MULTIPART_CONTENT,
            **authorization_header)

        response = RepositoryViewSet.as_view({'patch': 'update'})(
            request,
            uuid=repository.uuid,
            partial=True)
        response.render()
        content_data = json.loads(response.content)
        return (response, content_data,)

    def test_okay_update_name(self):
        for repository in self.repositories:
            response, content_data = self.request(
                repository,
                {
                    'name': 'Repository {}'.format(repository.uuid),
                },
                self.owner_token)

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK)

    def test_unauthorized(self):
        for repository in self.repositories:
            response, content_data = self.request(
                repository,
                {
                    'name': 'Repository {}'.format(repository.uuid),
                },
                self.user_token)

            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN)


class RepositoryAuthorizationTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user, self.user_token = create_user_and_token()
        self.owner, self.owner_token = create_user_and_token('owner')
        self.category = RepositoryCategory.objects.create(name='Category 1')

        self.repositories = [
            create_repository_from_mockup(self.owner, **mockup)
            for mockup in get_valid_mockups([self.category])
        ]

    def request(self, repository, token=None):
        authorization_header = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key),
        } if token else {}

        request = self.factory.get(
            '/api/v2/repository/{}/'.format(repository.uuid),
            **authorization_header)

        response = RepositoryViewSet.as_view({'get': 'retrieve'})(
            request,
            uuid=repository.uuid)
        response.render()
        content_data = json.loads(response.content)
        return (response, content_data,)

    def test_authorization_without_user(self):
        for repository in self.repositories:
            # ignore private repositories
            if repository.is_private:
                continue
            response, content_data = self.request(repository)
            self.assertIsNone(content_data.get('authorization'))

    def test_authorization_with_user(self):
        for repository in self.repositories:
            user, user_token = (self.owner, self.owner_token) \
                if repository.is_private else (self.user, self.user_token)
            response, content_data = self.request(repository, user_token)
            authorization = content_data.get('authorization')
            self.assertIsNotNone(authorization)
            self.assertEqual(
                authorization.get('uuid'),
                str(repository.get_user_authorization(user).uuid))


class RepositoryAvailableRequestAuthorizationTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user, self.user_token = create_user_and_token()
        self.owner, self.owner_token = create_user_and_token('owner')

        self.repository = Repository.objects.create(
            owner=self.owner,
            name='Testing',
            slug='test',
            language=languages.LANGUAGE_EN)

    def request(self, repository, token=None):
        authorization_header = {
            'HTTP_AUTHORIZATION': 'Token {}'.format(token.key),
        } if token else {}

        request = self.factory.get(
            '/api/v2/repository/{}/'.format(repository.uuid),
            **authorization_header)

        response = RepositoryViewSet.as_view({'get': 'retrieve'})(
            request,
            uuid=repository.uuid)
        response.render()
        content_data = json.loads(response.content)
        return (response, content_data,)

    def test_owner_ever_false(self):
        response, content_data = self.request(
            self.repository,
            self.owner_token)
        available_request_authorization = content_data.get(
            'available_request_authorization')
        self.assertFalse(available_request_authorization)

    def test_user_available(self):
        response, content_data = self.request(
            self.repository,
            self.user_token)
        available_request_authorization = content_data.get(
            'available_request_authorization')
        self.assertTrue(available_request_authorization)

    def test_false_when_request(self):
        RequestRepositoryAuthorization.objects.create(
            user=self.user,
            repository=self.repository,
            text='r')
        response, content_data = self.request(
            self.repository,
            self.user_token)
        available_request_authorization = content_data.get(
            'available_request_authorization')
        self.assertFalse(available_request_authorization)


class IntentsInRepositorySerializer(TestCase):
    def setUp(self):
        self.owner, self.owner_token = create_user_and_token('owner')

        self.repository = Repository.objects.create(
            owner=self.owner,
            name='Testing',
            slug='test',
            language=languages.LANGUAGE_EN)
        RepositoryExample.objects.create(
            repository_update=self.repository.current_update(),
            text='hi',
            intent='greet')

    def test_count_1(self):
        repository_data = RepositorySerializer(self.repository).data
        intent = repository_data.get('intents')[0]
        self.assertEqual(intent.get('examples__count'), 1)

    def test_example_deleted(self):
        example = RepositoryExample.objects.create(
            repository_update=self.repository.current_update(),
            text='hi',
            intent='greet')
        repository_data = RepositorySerializer(self.repository).data
        intent = repository_data.get('intents')[0]
        self.assertEqual(intent.get('examples__count'), 2)
        example.delete()
        repository_data = RepositorySerializer(self.repository).data
        intent = repository_data.get('intents')[0]
        self.assertEqual(intent.get('examples__count'), 1)