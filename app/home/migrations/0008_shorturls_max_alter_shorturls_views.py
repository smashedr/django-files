# Generated by Django 4.2.4 on 2023-08-05 08:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0007_alter_files_date_alter_files_edit_alter_files_expr_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="shorturls",
            name="max",
            field=models.IntegerField(
                default=0, help_text="Max ShortURL Views", verbose_name="Max"
            ),
        ),
        migrations.AlterField(
            model_name="shorturls",
            name="views",
            field=models.IntegerField(
                default=0, help_text="Total ShortURL Views", verbose_name="Views"
            ),
        ),
    ]
