# Generated by Django 4.2.11 on 2024-05-27 20:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import home.util.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0026_files_thumb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='files',
            name='thumb',
            field=home.util.storage.StoragesRouterFileField(blank=True, null=True, upload_to='./thumbs/'),
        ),
        migrations.CreateModel(
            name='Albums',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, help_text='Album Name.', max_length=255, null=True, verbose_name='Name')),
                ('password', models.CharField(blank=True, max_length=255, null=True, verbose_name='Album Password')),
                ('private', models.BooleanField(default=False, verbose_name='Private Album')),
                ('info', models.CharField(blank=True, help_text='Album Information.', max_length=255, null=True, verbose_name='Info')),
                ('view', models.IntegerField(default=0, help_text='Album Views.', verbose_name='Views')),
                ('maxv', models.IntegerField(default=0, help_text='Max Views.', verbose_name='Max')),
                ('expr', models.CharField(blank=True, default='', help_text='Album Expire.', max_length=32, verbose_name='Expiration')),
                ('date', models.DateTimeField(auto_now_add=True, help_text='Album Created Date.', verbose_name='Created')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Album',
                'verbose_name_plural': 'Albums',
            },
        ),
        migrations.AddField(
            model_name='files',
            name='albums',
            field=models.ManyToManyField(to='home.albums'),
        ),
    ]