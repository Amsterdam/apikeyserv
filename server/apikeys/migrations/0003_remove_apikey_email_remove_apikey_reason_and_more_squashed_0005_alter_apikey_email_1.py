# Generated by Django 4.2.1 on 2023-07-12 14:24

import apikeys.models
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ("apikeys", "0003_remove_apikey_email_remove_apikey_reason_and_more"),
        ("apikeys", "0004_alter_apikey_email_1"),
        ("apikeys", "0005_alter_apikey_email_1"),
    ]

    dependencies = [
        ("apikeys", "0002_auto_20230509_1530"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="apikey",
            name="email",
        ),
        migrations.RemoveField(
            model_name="apikey",
            name="reason",
        ),
        migrations.AddField(
            model_name="apikey",
            name="contactperson_1_name",
            field=models.CharField(
                blank=True, max_length=256, null=True, verbose_name="Contactpersoon"
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="contactperson_2_name",
            field=models.CharField(
                blank=True, max_length=256, null=True, verbose_name="Tweede contactpersoon"
            ),
        ),
        migrations.AddField(
            model_name="apikey",
            name="department",
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name="Afdeling"),
        ),
        migrations.AddField(
            model_name="apikey",
            name="email_2",
            field=models.EmailField(
                blank=True, max_length=256, null=True, verbose_name="Tweede e-mailadres"
            ),
        ),
        migrations.AlterField(
            model_name="apikey",
            name="expires",
            field=models.DateTimeField(
                blank=True, default=apikeys.models.get_expiry_datetime, null=True
            ),
        ),
        migrations.AlterField(
            model_name="apikey",
            name="organisation",
            field=models.CharField(max_length=256, verbose_name="Organisatie"),
        ),
        migrations.AddField(
            model_name="apikey",
            name="email_1",
            field=models.EmailField(default="", max_length=256, verbose_name="E-mailadres"),
        ),
    ]
