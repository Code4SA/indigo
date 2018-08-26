# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-20 17:37
from __future__ import unicode_literals

from django.db import migrations


def set_country_primary_language(apps, schema_editor):
    Language = apps.get_model("indigo_app", "Language")
    Country = apps.get_model("indigo_app", "Country")
    db_alias = schema_editor.connection.alias

    lang = Language.objects.using(db_alias).first()

    for country in Country.objects.using(db_alias).all():
        country.primary_language = lang
        country.save()


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_app', '0011_country_primary_language'),
    ]

    operations = [
        migrations.RunPython(set_country_primary_language, migrations.RunPython.noop),
    ]
