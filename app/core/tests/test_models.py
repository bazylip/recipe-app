from decimal import Decimal
from unittest.mock import patch

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from utils.factories import (
    EXAMPLE_EMAIL,
    EXAMPLE_PASSWORD,
    ingredient_factory,
    user_factory,
)

EXAMPLE_RECIPE_TITLE = "Example recipe name"
EXAMPLE_RECIPE_TIME_MINUTES = 5
EXAMPLE_RECIPE_PRICE = Decimal("5.50")
EXAMPLE_RECIPE_DESCRIPTION = "Example description"

EXAMPLE_INGREDIENT_NAME = "Ingredient 1"


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
            title=EXAMPLE_RECIPE_TITLE,
            time_minutes=EXAMPLE_RECIPE_TIME_MINUTES,
            price=EXAMPLE_RECIPE_PRICE,
            description=EXAMPLE_RECIPE_DESCRIPTION,
        )

        self.assertEqual(str(recipe), recipe.title)

    def test__create_tag__successful(self):
        user = user_factory()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)

    def test__create_ingredient_successful(self):
        user = user_factory()

        ingredient = ingredient_factory(user=user, name=EXAMPLE_INGREDIENT_NAME)

        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test__recipe_file_name_uuid(self, mock_uuid):
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
