from decimal import Decimal

from core.models import Recipe, Tag, User
from django.contrib.auth import get_user_model

EXAMPLE_EMAIL = "test@example.com"
EXAMPLE_PASSWORD = "testpass123"

EXAMPLE_TITLE = "Example recipe name"
EXAMPLE_TIME_MINUTES = 5
EXAMPLE_PRICE = Decimal("5.50")
EXAMPLE_DESCRIPTION = "Example description"
EXAMPLE_LINK = "http://example.com/recipe.pdf"


def user_factory(email: str = EXAMPLE_EMAIL, password: str = EXAMPLE_PASSWORD) -> User:
    return get_user_model().objects.create_user(email=email, password=password)


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


def tag_factory(user: User, name: str, **kwargs) -> Tag:
    tag = Tag.objects.create(user=user, name=name, **kwargs)
    return tag
