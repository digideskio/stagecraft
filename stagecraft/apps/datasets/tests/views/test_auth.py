from django.conf import settings
from django.test import TestCase

from hamcrest import assert_that, is_, is_not, equal_to
from httmock import HTTMock

from stagecraft.apps.datasets.models.oauth_user import OAuthUser
from .test_utils import govuk_signon_mock


class OAuthReauthTestCase(TestCase):
    def setUp(self):
        settings.USE_DEVELOPMENT_USERS = False

    def _create_oauth_user(self):
        OAuthUser.objects.cache_user(
            'the-token',
            {"uid": "the-uid",
             "email": "foo@foo.com",
             "permissions": ['signin']})

    def _mock_signon(self, permissions):
        return HTTMock(
            govuk_signon_mock(
                permissions=permissions))

    def test_reauth_with_permission(self):
        self._create_oauth_user()
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(200))
            assert_that(
                OAuthUser.objects.get_by_access_token('the-token'),
                is_(None))

    def test_reauth_without_permission(self):
        self._create_oauth_user()
        with self._mock_signon(['signin']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(403))
            assert_that(
                OAuthUser.objects.get_by_access_token('the-token'),
                is_not(None))

    def test_reauth_returns_200_if_user_is_not_found(self):
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(200))

    def test_fails_with_get(self):
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.get(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(405))
