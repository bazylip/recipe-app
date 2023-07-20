from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

EXAMPLE_USER_EMAIL = "user@example.com"
EXAMPLE_USER_PASSWORD = "test_password123"
EXAMPLE_USER_NAME = "Test Name"


def create_user(**kwargs):
    return get_user_model().objects.create_user(**kwargs)


class PublicUserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test__create_user__success(self):
        payload = {
            "email": EXAMPLE_USER_EMAIL,
            "password": EXAMPLE_USER_PASSWORD,
            "name": EXAMPLE_USER_NAME,
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test__create_user_with_email_already_exists__returns_400(self):
        payload = {
            "email": EXAMPLE_USER_EMAIL,
            "password": EXAMPLE_USER_PASSWORD,
            "name": EXAMPLE_USER_NAME,
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test__create_user_with_password_too_short__error_and_does_not_create_user(self):
        payload = {
            "email": EXAMPLE_USER_EMAIL,
            "password": "pw",
            "name": EXAMPLE_USER_NAME,
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload["email"]).exists()
        self.assertFalse(user_exists)

    def test__create_token_for_user_with_proper_credentials__generates_token_successfully(
        self,
    ):
        user_details = {
            "name": EXAMPLE_USER_NAME,
            "email": EXAMPLE_USER_EMAIL,
            "password": EXAMPLE_USER_PASSWORD,
        }
        create_user(**user_details)
        payload = {"email": user_details["email"], "password": user_details["password"]}

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test__create_token_for_user_with_invalid_credentials__returns_400(self):
        user_details = {
            "name": EXAMPLE_USER_NAME,
            "email": EXAMPLE_USER_EMAIL,
            "password": "good_pass",
        }
        create_user(**user_details)
        payload = {"email": user_details["email"], "password": "bad_pass"}

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test__create_token_for_user_with_blank_password__returns_400(self):
        payload = {"email": EXAMPLE_USER_EMAIL, "password": ""}

        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test__get_user__unauthenticated__returns_401(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    def setUp(self) -> None:
        self.user = create_user(
            email=EXAMPLE_USER_EMAIL,
            password=EXAMPLE_USER_PASSWORD,
            name=EXAMPLE_USER_NAME,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test__get_user__authenticated__success(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {"name": self.user.name, "email": self.user.email})

    def test__post_user__returns_405(self):
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test__update_user__authenticated__success(self):
        new_name = "New Name"
        new_password = "newpassword"
        payload = {"name": new_name, "password": new_password}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, new_name)
        self.assertTrue(self.user.check_password(new_password))
