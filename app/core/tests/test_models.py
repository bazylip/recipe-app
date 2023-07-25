from decimal import Decimal

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from utils.factories import EXAMPLE_EMAIL, EXAMPLE_PASSWORD, user_factory

EXAMPLE_TITLE = "Example recipe name"
EXAMPLE_TIME_MINUTES = 5
EXAMPLE_PRICE = Decimal("5.50")
EXAMPLE_DESCRIPTION = "Example description"


class ModelTests(TestCase):
    def test__create_user__with_email__sets_email_and_password_correctly(self):
        user = user_factory()

        self.assertEqual(user.email, EXAMPLE_EMAIL)
        self.assertTrue(user.check_password(EXAMPLE_PASSWORD))

    def test__create_user__with_unnormalized_email__sets_normalized_email(self):
        sample_emails = [
            ("test1@EXAMPLE.com", "test1@example.com"),
            ("Test2@example.com", "Test2@example.com"),
            ("TEST3@EXAMPLE.com", "TEST3@example.com"),
            ("test4@example.COM", "test4@example.com"),
        ]

        for email, expected_email in sample_emails:
            user = user_factory(email=email, password="testpass123")
            self.assertEqual(user.email, expected_email)

    def test__create_user__without_email__raises_error(self):
        with self.assertRaises(ValueError):
            user_factory(email="", password="testpass123")

    def test__create_superuser__sets_proper_superuser_fields(self):
        user = get_user_model().objects.create_superuser(
            email=EXAMPLE_EMAIL, password=EXAMPLE_PASSWORD
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test__create_recipe__successful(self):
        user = user_factory()
        recipe = models.Recipe.objects.create(
            user=user,
            title=EXAMPLE_TITLE,
            time_minutes=EXAMPLE_TIME_MINUTES,
            price=EXAMPLE_PRICE,
            description=EXAMPLE_DESCRIPTION,
        )

        self.assertEqual(str(recipe), recipe.title)

    def test__create_tag__successful(self):
        user = user_factory()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)
