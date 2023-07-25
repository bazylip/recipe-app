from core.models import Tag
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient
from utils.factories import user_factory

TAGS_URL = reverse("recipe:tag-list")


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
        Tag.objects.create(user=self.user, name="Dessert")
        Tag.objects.create(user=self.user, name="Vegan")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_tags_limited_to_user(self):
        other_user = user_factory(email="other@example.com")
        Tag.objects.create(user=other_user, name="Dessert")
        tag = Tag.objects.create(user=self.user, name="Vegan")

        res = self.client.get(TAGS_URL)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
