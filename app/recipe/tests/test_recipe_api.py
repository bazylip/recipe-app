import os.path
import tempfile
from decimal import Decimal

from core.models import Ingredient, Recipe, Tag
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient
from utils.factories import (
    EXAMPLE_LINK,
    EXAMPLE_PRICE,
    EXAMPLE_TIME_MINUTES,
    EXAMPLE_TITLE,
    ingredient_factory,
    recipe_factory,
    tag_factory,
    user_factory,
)

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test__list_recipes_unauthenticated__returns_401(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = user_factory()
        self.client.force_authenticate(self.user)

    def test__list_recipes_authenticated__lists_recipes_successfully(self):
        recipe_factory(user=self.user)
        recipe_factory(user=self.user)

        res = self.client.get(RECIPES_URL)
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

        res = self.client.get(RECIPES_URL)
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

        res = self.client.post(RECIPES_URL, payload)
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

    def test__create_recipe_with_new_tags(self):
        payload = {
            "title": EXAMPLE_TITLE,
            "time_minutes": EXAMPLE_TIME_MINUTES,
            "price": EXAMPLE_PRICE,
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(name=tag["name"], user=self.user).exists()
            )

    def test__create_recipe_with_existing_tags(self):
        tag_indian = tag_factory(user=self.user, name="Indian")
        payload = {
            "title": EXAMPLE_TITLE,
            "time_minutes": EXAMPLE_TIME_MINUTES,
            "price": EXAMPLE_PRICE,
            "tags": [{"name": "Indian"}, {"name": "Dinner"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            self.assertTrue(
                recipe.tags.filter(name=tag["name"], user=self.user).exists()
            )

    def test__create_tag_on_recipe_update(self):
        recipe = recipe_factory(user=self.user)
        tag_name = "Lunch"
        payload = {"tags": [{"name": tag_name}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name=tag_name)
        self.assertIn(new_tag, recipe.tags.all())

    def test__assign_tag_on_recipe_update(self):
        recipe = recipe_factory(user=self.user)
        tag_breakfast = tag_factory(user=self.user, name="Breakfast")
        recipe.tags.add(tag_breakfast)

        lunch_name = "Lunch"
        tag_lunch = tag_factory(user=self.user, name=lunch_name)
        payload = {"tags": [{"name": lunch_name}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test__clear_recips_tags(self):
        recipe = recipe_factory(user=self.user)
        tag = tag_factory(user=self.user, name="Breakfast")
        recipe.tags.add(tag)
        payload = {"tags": []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        payload = {
            "title": EXAMPLE_TITLE,
            "time_minutes": EXAMPLE_TIME_MINUTES,
            "price": EXAMPLE_PRICE,
            "ingredients": [{"name": "Cauliflower"}, {"name": "Salt"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        ingredient = ingredient_factory(user=self.user, name="Cauliflower")
        payload = {
            "title": EXAMPLE_TITLE,
            "time_minutes": EXAMPLE_TIME_MINUTES,
            "price": EXAMPLE_PRICE,
            "ingredients": [{"name": "Cauliflower"}, {"name": "Salt"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_recipe_update(self):
        recipe = recipe_factory(user=self.user)
        payload = {"ingredients": [{"name": "Limes"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name="Limes")
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        ingredient1 = ingredient_factory(user=self.user, name="Cauliflower")
        recipe = recipe_factory(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = ingredient_factory(user=self.user, name="Limes")
        payload = {"ingredients": [{"name": "Limes"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient = ingredient_factory(user=self.user, name="Cauliflower")
        recipe = recipe_factory(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_recipes_by_tags(self):
        r1 = recipe_factory(user=self.user, title="Curry")
        r2 = recipe_factory(user=self.user, title="Melanzane")
        t1 = tag_factory(user=self.user, name="Vegan")
        t2 = tag_factory(user=self.user, name="Vegatarian")
        r1.tags.add(t1)
        r2.tags.add(t2)
        r3 = recipe_factory(user=self.user, title="Fish and Chips")

        params = {"tags": f"{t1.id},{t2.id}"}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        r1 = recipe_factory(user=self.user, title="Curry")
        r2 = recipe_factory(user=self.user, title="Melanzane")
        i1 = ingredient_factory(user=self.user, name="Vegan")
        i2 = ingredient_factory(user=self.user, name="Vegatarian")
        r1.ingredients.add(i1)
        r2.ingredients.add(i2)
        r3 = recipe_factory(user=self.user, title="Fish and Chips")

        params = {"ingredients": f"{i1.id},{i2.id}"}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = user_factory()
        self.client.force_authenticate(self.user)
        self.recipe = recipe_factory(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test__upload_valid_image__successful(self):
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test__upload_invalid_image__bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {"image": "test"}

        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
