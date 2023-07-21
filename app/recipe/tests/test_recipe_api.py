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


def user_factory(**kwargs) -> User:
    return get_user_model().objects.create_user(**kwargs)


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test__list_recipes_unauthenticated__returns_401(self):
        res = self.client.get(LIST_RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = user_factory(email=USER_EMAIL, password=USER_PASSWORD)
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
        other_user = user_factory(email="other@example.com", password="otherpass123")
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

    def test__create_recipe__creation_successful(self):
        payload = {
            "title": EXAMPLE_TITLE,
            "time_minutes": EXAMPLE_TIME_MINUTES,
            "price": EXAMPLE_PRICE,
        }

        res = self.client.post(LIST_RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test__partial_update__update_successful(self):
        new_title = "New recipe title"
        recipe = recipe_factory(user=self.user)
        payload = {"title": new_title}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, new_title)
        self.assertEqual(recipe.link, EXAMPLE_LINK)
        self.assertEqual(recipe.user, self.user)

    def test__full_update__update_successful(self):
        recipe = recipe_factory(user=self.user)
        payload = {
            "title": "New title",
            "time_minutes": 15,
            "price": Decimal("2.50"),
            "description": "New description",
            "link": "New link",
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test__update_user__does_not_update_user(self):
        new_user = user_factory(email="new@example.com", password="test123")
        recipe = recipe_factory(user=self.user)
        payload = {"user": new_user}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test__delete_recipe__deletion_successful(self):
        recipe = recipe_factory(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test__delete_recipe_of_other_user__returns_404(self):
        new_user = user_factory(email="new@example.com", password="test123")
        recipe = recipe_factory(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
