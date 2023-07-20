from decimal import Decimal

from core.models import Recipe, User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

LIST_RECIPES_URL = reverse("recipe:recipe-list")

EXAMPLE_TITLE = "Example recipe name"
EXAMPLE_TIME_MINUTES = 5
EXAMPLE_PRICE = Decimal("5.50")
EXAMPLE_DESCRIPTION = "Example description"
EXAMPLE_LINK = "http://example.com/recipe.pdf"

USER_EMAIL = "user@example.com"
USER_PASSWORD = "password123"


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def recipe_factory(user: User, **kwargs) -> Recipe:
    defaults = {
        "title": EXAMPLE_TITLE,
        "time_minutes": EXAMPLE_TIME_MINUTES,
        "price": EXAMPLE_PRICE,
        "description": EXAMPLE_DESCRIPTION,
        "link": EXAMPLE_LINK,
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test__list_recipes_unauthenticated__returns_401(self):
        res = self.client.get(LIST_RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email=USER_EMAIL, password=USER_PASSWORD
        )
        self.client.force_authenticate(self.user)

    def test__list_recipes_authenticated__lists_recipes_successfully(self):
        recipe_factory(user=self.user)
        recipe_factory(user=self.user)

        res = self.client.get(LIST_RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test__list_recipes_authenticated__lists_only_recipes_for_authenticated_user(
        self,
    ):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="otherpass123"
        )
        recipe_factory(user=self.user)
        recipe_factory(user=other_user)

        res = self.client.get(LIST_RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test__get_recipe_detail__returns_correct_detail(self):
        recipe = recipe_factory(user=self.user)
        url = detail_url(recipe.id)

        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
