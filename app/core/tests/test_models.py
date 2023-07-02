from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    def test__create_user__with_email__sets_email_and_password_correctly(self):
        email = "test@example.com"
        password = "testpass123"

        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test__create_user__with_unnormalized_email__sets_normalized_email(self):
        sample_emails = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@example.com", "Test2@example.com"),
            ("TEST3@EXAMPLE.com", "TEST3@example.com"),
            ("test4@example.COM", "test4@example.com"),
        ]

        for email, expected_email in sample_emails:
            user = get_user_model().objects.create_user(
                email=email, password="testpass123"
            )
            self.assertEqual(user.email, expected_email)

    def test__create_user__without_email__raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="testpass123")

    def test__create_superuser__sets_proper_superuser_fields(self):
        user = get_user_model().objects.create_superuser(
            email="test@example.com", password="testpass123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
