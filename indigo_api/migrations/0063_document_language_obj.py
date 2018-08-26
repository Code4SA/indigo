# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-21 19:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0062_colophon_remove_old_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='language_obj',
            field=models.ForeignKey(help_text=b'Language this document is in.', null=True, on_delete=django.db.models.deletion.PROTECT, to='indigo_api.Language'),
        ),
    ]
