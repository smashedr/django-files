# Generated by Django 4.2.3 on 2023-08-05 22:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oauth", "0002_customuser_nav_color_1_customuser_nav_color_2_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="remove_exif_geo",
            field=models.BooleanField(
                default=False,
                help_text="Removes geo exif data from images on upload.",
                verbose_name="No EXIF Geo",
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="show_exif_preview",
            field=models.BooleanField(
                default=False,
                help_text="Shows exif data on previews and unfurls.",
                verbose_name="EXIF Preview",
            ),
        ),
    ]