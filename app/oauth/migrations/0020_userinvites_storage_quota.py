# Generated by Django 4.2.11 on 2024-04-08 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0019_alter_customuser_storage_quota_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinvites',
            name='storage_quota',
            field=models.PositiveBigIntegerField(blank=True, default=None, help_text="Futureser's storage quota in bytes.", null=True),
        ),
    ]
