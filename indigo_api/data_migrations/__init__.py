import re

from indigo.xmlutils import rewrite_ids


class AKNMigration(object):
    def migrate_document(self, document):
        return self.migrate_act(document.doc)


class ScheduleArticleToHcontainer(AKNMigration):
    """ Change from using article as the main schedule container
    to using hcontainer.

    Migrates:

        <mainBody>
          <article id="schedule2">
            <heading>BY-LAWS REPEALED BY SECTION 99</heading>
            <paragraph id="schedule2.paragraph-0">

    to:

        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subeading>BY-LAWS REPEALED BY SECTION 99</subeading>
            <paragraph id="schedule2.paragraph-0">
    """
    def migrate_act(self, act):
        changed = False

        for article in act.root.xpath('//a:mainBody/a:article', namespaces={'a': act.namespace}):
            changed = True

            # change to hcontainer
            article.tag = '{%s}hcontainer' % act.namespace
            article.set('name', 'schedule')

            # make heading a subheading
            try:
                heading = article.heading
                heading.tag = '{%s}subheading' % act.namespace
            except AttributeError:
                pass

            # add a new heading
            alias = article.getparent().getparent().meta.identification.FRBRWork.FRBRalias.get('value')
            heading = act.maker.heading(alias)
            article.insert(0, heading)

        return changed


class FixSignificantWhitespace(AKNMigration):
    """ Strip unnecessary whitespace from p, heading, subheading and listIntroduction
    elements.

    In the past, we pretty-printed our XML which introduced meaningful whitespace. This
    migration removes it.
    """
    def migrate_document(self, document):
        xml = self.strip_whitespace(document.document_xml)
        if xml != document.document_xml:
            document.reset_xml(xml, from_model=True)
            return True

    def strip_whitespace(self, xml):
        opening = re.compile(r'<(p|heading|subheading|listIntroduction)>\n\s+<')
        xml = opening.sub('<\\1><', xml)

        closing = re.compile(r'\s*\n\s+</(p|heading|subheading|listIntroduction)>')
        xml = closing.sub('</\\1>', xml)

        return xml


class UpdateAKNNamespace(AKNMigration):
    """ Update all instances of:
    <akomaNtoso xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    to
    <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
    """
    def update_namespace(self, xml):
        xml = xml.replace(
            ' xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd"',
            "",
            1)\
            .replace(
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            "",
            1)\
            .replace(
            'xmlns="http://www.akomantoso.org/2.0"',
            'xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"',
            1)

        return xml


class UnnumberedParagraphsToHcontainer(AKNMigration):
    """ Update all instances un-numbered paragraphs to hcontainers. Slaw generates these when
    a block of text is encountered in a hierarchical element.

    This ALSO changes the id of the element to match AKN 3 styles, but using the id attribute (not eId)

    <paragraph id="section-1.paragraph0">
      <content>
        <p>text</p>
      </content>
    </paragraph>

    becomes

    <hcontainer id="section-1.hcontainer_0">
      <content>
        <p>text</p>
      </content>
    </hcontainer>
    """
    def migrate_act(self, act):
        for para in act.root.xpath('//a:paragraph[not(a:num)]', namespaces={'a': act.namespace}):
            para.tag = f'{{{act.namespace}}}hcontainer'
            # new id is based on the number of preceding hcontainer siblings
            num = len(para.xpath('preceding-sibling::a:hcontainer', namespaces={'a': act.namespace}))
            old_id = para.get('id')
            new_id = re.sub('paragraph(\d+)$', f'hcontainer_{num}', old_id)
            rewrite_ids(para, old_id, new_id)
