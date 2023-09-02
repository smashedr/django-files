# Generated by Django 4.2.4 on 2023-09-02 07:58

from django.db import migrations, models
import home.util.rand


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0019_sitesettings_site_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="duo_auth",
            field=models.BooleanField(
                default=False,
                help_text="Require Duo Authentication",
                verbose_name="Duo AUth",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pub_load",
            field=models.BooleanField(
                default=False,
                help_text="Allow Public Uploads",
                verbose_name="Public Upload",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="site_color",
            field=models.CharField(
                default=home.util.rand.rand_color_hex,
                help_text="Site Theme Color for Site Embeds",
                max_length=7,
                verbose_name="Site Color",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="site_description",
            field=models.TextField(
                default="A Feature Packed Self-Hosted Django/Docker File Manager for Sharing Files with ShareX, Flameshot and Much more...",
                max_length=155,
                verbose_name="Site Description",
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="site_title",
            field=models.CharField(
                default="Django Files", max_length=64, verbose_name="Site Title"
            ),
        ),
    ]
