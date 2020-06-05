# Generated by Django 2.2.12 on 2020-05-16 12:33

import logging
import re

from django.db import migrations

from indigo_api.data_migrations.akn3 import AKNeId

log = logging.getLogger(__name__)

replacements = AKNeId.basic_replacements


def forward(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Commencement = apps.get_model("indigo_api", "Commencement")

    for commencement in Commencement.objects.using(db_alias).all().order_by("-pk"):
        if commencement.provisions:
            log.info(f"Commencement on {commencement.commenced_work.frbr_uri}: Old provisions: {commencement.provisions}")
            new_provisions = []

            for provision in commencement.provisions:
                element = provision.split("-", 1)[0]
                new_provisions.append(re.sub(replacements[element][0], replacements[element][1], provision))

            commencement.provisions = new_provisions
            commencement.save()
            log.info(f"New provisions: {commencement.provisions}")


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0132_migrate_ids_eIds'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
