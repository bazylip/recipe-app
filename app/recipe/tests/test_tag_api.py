from core.models import Tag
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient
from utils.factories import recipe_factory, tag_factory, user_factory

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    return reverse("recipe:tag-detail", args=[tag_id])


class PublicTagAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    def setUp(self):
        self.user = user_factory()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        tag_factory(user=self.user, name="Dessert")
        tag_factory(user=self.user, name="Vegan")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tags_limited_to_user(self):
        other_user = user_factory(email="other@example.com")
        tag_factory(user=other_user, name="Dessert")
        tag = tag_factory(user=self.user, name="Vegan")

        res = self.client.get(TAGS_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_tag(self):
        tag = tag_factory(user=self.user, name="Dinner")
        payload = {"name": "Dessert"}

        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        tag = tag_factory(user=self.user, name="Dinner")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        tag1 = tag_factory(user=self.user, name="Breakfast")
        tag2 = tag_factory(user=self.user, name="Lunch")
        recipe = recipe_factory(user=self.user)
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        tag = tag_factory(user=self.user, name="Breakfast")
        tag_factory(user=self.user, name="Lunch")
        r1 = recipe_factory(user=self.user)
        r2 = recipe_factory(user=self.user)
        r1.tags.add(tag)
        r2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
