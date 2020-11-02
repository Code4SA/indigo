# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-04-08 10:57
from django.db import migrations

from cobalt import datestring
from iso8601 import parse_date


def create_repeals(apps, schema_editor):
    Document = apps.get_model("indigo_api", "Document")
    Work = apps.get_model("indigo_api", "Work")
    db_alias = schema_editor.connection.alias

    # ensure works existing for all repealing documents,
    # and link the repeals in
    documents = Document.objects.using(db_alias).all()
    works = {w.frbr_uri: w for w in Work.objects.using(db_alias).all()}

    for doc in documents:
        if doc.repeal_event:
            date = parse_date(doc.repeal_event['date']).date()

            work = works.get(doc.repeal_event['repealing_uri'])
            if not work:
                work = Work(
                    title=doc.repeal_event['repealing_title'],
                    frbr_uri=doc.repeal_event['repealing_uri'],
                    publication_date=date,
                )
                work.save()
                works[work.frbr_uri] = work

            doc.work.repealed_by = work
            doc.work.repealed_date = date
            doc.work.save()


def uncreate_repeals(apps, schema_editor):
    Work = apps.get_model("indigo_api", "Work")
    db_alias = schema_editor.connection.alias

    # copy repeal info back into documents
    works = Work.objects.using(db_alias).filter(repealed_by__isnull=False).all()

    for work in works:
        for doc in work.document_set.all():
            doc.repeal_event = {
                'repealing_uri': work.frbr_uri,
                'repealing_title': work.title,
                'date': datestring(work.repealed_date),
            }
            doc.save(update_fields=['repeal_event'])


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0041_work_repeal'),
    ]

    operations = [
        migrations.RunPython(create_repeals, uncreate_repeals, elidable=True),
    ]
