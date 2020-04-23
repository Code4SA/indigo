# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-04-22 12:39
from __future__ import unicode_literals

from lxml import etree

from django.db import migrations

from cobalt import Act, FrbrUri, datestring
from cobalt.uri import FRBR_URI_RE
from indigo.analysis.refs.base import BaseRefsFinder


def new_frbr_uri(uri, forward):
    """ Sets prefix on uri:
        'akn' if forward is True, None if it's False.
    """
    if not isinstance(uri, FrbrUri):
        uri = FrbrUri.parse(uri)
    uri.prefix = 'akn' if forward else None
    return uri


class RefsFinderRef(BaseRefsFinder):
    """ Finds hrefs in documents, of the form:

        href="/za/act/2012/22">Act no 22 of 2012
        href="/akn/za/act/2012/22">Act no 22 of 2012

        and either adds or removes the /akn prefix, depending on what is passed to `handle_refs`

    """

    ancestors = ['meta', 'coverPage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']
    candidate_xpath = "//a:*[starts-with(@href, '/')]"
    pattern_re = FRBR_URI_RE

    def handle_refs(self, document, forward):
        root = etree.fromstring(document.document_xml)
        self.setup(root)

        for ancestor in self.ancestor_nodes(root):
            for node in self.candidate_nodes(ancestor):
                ref = node.get('href')
                match = self.pattern_re.match(ref)
                if match:
                    ref = str(new_frbr_uri(ref, forward))
                    node.set('href', ref)

        document.document_xml = etree.tostring(root, encoding='utf-8').decode('utf-8')


def migrate_uris(apps, schema_editor, forward):
    """ Start or stop using AKN3 FRBR URIs (i.e. /akn prefix)
    - Update URIs of all existing works and documents
    - Update meta/identification block of each AKN document
    - Update hrefs in all documents
    """
    db_alias = schema_editor.connection.alias
    Work = apps.get_model("indigo_api", "Work")
    Document = apps.get_model("indigo_api", "Document")

    for work in Work.objects.using(db_alias).all():
        work.frbr_uri = new_frbr_uri(work.frbr_uri, forward)
        work.save()

    for doc in Document.objects.using(db_alias).all():
        doc.frbr_uri = doc.work.frbr_uri
        cobalt_doc = Act(doc.document_xml)
        cobalt_doc.frbr_uri = doc.frbr_uri
        doc.document_xml = cobalt_doc.to_xml()
        RefsFinderRef.handle_refs(RefsFinderRef(), doc, forward)
        doc.save()


def migrate_forward(apps, schema_editor):
    migrate_uris(apps, schema_editor, forward=True)


def migrate_backward(apps, schema_editor):
    migrate_uris(apps, schema_editor, forward=False)


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0128_rename_badges'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
