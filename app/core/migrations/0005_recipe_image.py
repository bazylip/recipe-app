# Generated by Django 3.2.20 on 2023-09-01 09:49

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_auto_20230801_1720"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image",
            field=models.ImageField(
                null=True, upload_to=core.models.recipe_image_file_path
            ),
        ),
    ]
