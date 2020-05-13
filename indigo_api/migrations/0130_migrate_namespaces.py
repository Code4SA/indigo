# Generated by Django 2.2.12 on 2020-05-12 15:26

import json
from reversion.models import Version

from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from indigo_api.data_migrations import UpdateAKNNamespace


def forward(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Document = apps.get_model("indigo_api", "Document")
    ct_doc = ContentType.objects.get_for_model(Document)
    migration = UpdateAKNNamespace()

    for document in Document.objects.using(db_alias).all():
        xml = migration.update_namespace(document.document_xml)
        if xml != document.document_xml:
            document.reset_xml(xml, from_model=True)
            document.save()

        # Update historical Document versions
        for version in Version.objects.filter(content_type=ct_doc.pk)\
                .filter(object_id=document.pk).using(db_alias).all():
            data = json.loads(version.serialized_data)
            data[0]['fields']['document_xml'] = migration.update_namespace(data[0]['fields']['document_xml'])
            version.serialized_data = json.dumps(data)
            version.save()


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0129_migrate_refs_uris'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
