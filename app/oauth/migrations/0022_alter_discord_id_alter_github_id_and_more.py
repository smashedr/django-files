# Generated by Django 4.2.11 on 2024-06-02 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0021_google_alter_customuser_user_avatar_choice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discord',
            name='id',
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='github',
            name='id',
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name='google',
            name='access_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='google',
            name='avatar',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='google',
            name='id',
            field=models.CharField(max_length=128, unique=True),
        ),
    ]