# Generated by Django 4.2.5 on 2023-10-05 08:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0006_sitesettings_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="show_setup",
            field=models.BooleanField(default=True),
        ),
    ]
