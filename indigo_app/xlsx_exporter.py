# coding=utf-8
from django.http import HttpResponse
import io
import xlsxwriter

from indigo_api.models import Amendment


def generate_xlsx(queryset, filename, full_index):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    if full_index:
        write_full_index(workbook, queryset)
    else:
        write_works(workbook, queryset)
        write_relationships(workbook, queryset)

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


def write_works(workbook, queryset):
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    works_sheet = workbook.add_worksheet('Works')
    works_sheet_columns = ['FRBR URI', 'Place', 'Title', 'Subtype', 'Year',
                           'Number', 'Publication Date', 'Publication Number',
                           'Assent Date', 'Commenced', 'Main Commencement Date',
                           'Repealed Date', 'Parent Work', 'Stub']
    # Write the works sheet column titles
    for position, title in enumerate(works_sheet_columns, 1):
        works_sheet.write(0, position, title)

    for row, work in enumerate(queryset, 1):
        works_sheet.write(row, 0, row)
        works_sheet.write(row, 1, work.frbr_uri)
        works_sheet.write(row, 2, work.place.place_code)
        works_sheet.write(row, 3, work.title)
        works_sheet.write(row, 4, work.subtype)
        works_sheet.write(row, 5, work.year)
        works_sheet.write(row, 6, work.number)
        works_sheet.write(row, 7, work.publication_date, date_format)
        works_sheet.write(row, 8, work.publication_number)
        works_sheet.write(row, 9, work.assent_date, date_format)
        works_sheet.write(row, 10, work.commenced)
        works_sheet.write(row, 11, work.commencement_date, date_format)
        works_sheet.write(row, 12, work.repealed_date, date_format)
        works_sheet.write(row, 13, work.parent_work.frbr_uri if work.parent_work else None)
        works_sheet.write(row, 14, work.stub)


def write_relationships(workbook, queryset):
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    relationships_sheet = workbook.add_worksheet('Relationships')
    relationships_sheet_columns = ['First Work', 'Relationship', 'Second Work', 'Date']

    # write the relationships sheet column titles
    for position, title in enumerate(relationships_sheet_columns, 1):
        relationships_sheet.write(0, position, title)

    row = 1
    for work in queryset:
        family = []

        # parent work
        if work.parent_work:
            family.append({
                'rel': 'subsidiary of',
                'work': work.parent_work.frbr_uri,
                'date': None
            })

        # amended works
        amended = Amendment.objects.filter(amending_work=work).prefetch_related('amended_work').all()
        family = family + [{
            'rel': 'amends',
            'work': a.amended_work.frbr_uri,
            'date': a.date
        } for a in amended]

        # repealed works
        repealed_works = work.repealed_works.all()
        family = family + [{
            'rel': 'repeals',
            'work': r.frbr_uri,
            'date': r.repealed_date
        } for r in repealed_works]

        # commenced works
        family = family + [{
            'rel': 'commences',
            'work': c.commenced_work.frbr_uri,
            'date': c.date
        } for c in work.commencements_made.all()]

        for relationship in family:
            relationships_sheet.write(row, 0, row)
            relationships_sheet.write(row, 1, work.frbr_uri)
            relationships_sheet.write(row, 2, relationship['rel'])
            relationships_sheet.write(row, 3, relationship['work'])
            relationships_sheet.write(row, 4, relationship['date'], date_format)
            row += 1


def write_full_index(workbook, works):
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    sheet = workbook.add_worksheet('Works')
    columns = ['country', 'locality',
               'title', 'cap',
               'subtype (blank for Acts)', 'number', 'year',
               'publication_name', 'publication_number',
               'assent_date', 'publication_date', 'commencement_date (main)',
               'stub (✔)', 'taxonomy',
               'primary_work',
               'commenced_by', 'commenced_on_date',
               'amended_by', 'amended_on_date',
               'repealed_by', 'repealed_on_date',
               'subleg',
               'commences', 'commences_on_date',
               'amends', 'amends_on_date',
               'repeals', 'repeals_on_date',
               'Ignore (x) or in (✔)',
               'frbr_uri', 'frbr_uri_title',
               'comments', 'LINKS ETC (add columns as needed)']
    # write the column titles
    for position, title in enumerate(columns):
        sheet.write(0, position, title)

    # gather the works and their related information
    rows = []
    for work in works:
        """ how many rows will we need for this work?
            a minimum of one, plus more if there are multiple commencements / amendments / repeals
             (but not if there's one of each)
            grab the commencements / amendments / repeals while we're at it
        """
        n_rows = 1
        commencements_passive = work.commencements.all().order_by('date')
        amendments_passive = work.amendments.all().order_by('date')
        commencements_active = work.commencements_made.all().order_by('date')
        amendments_active = work.amendments_made.all().order_by('date')
        repeals_active = work.repealed_works.all().order_by('repealed_date')

        for relation in [commencements_passive, amendments_passive,
                         commencements_active, amendments_active, repeals_active]:
            n_rows += len(relation) - 1 if len(relation) else 0

        info = {
            'work': work,
            'n_rows': n_rows,
            'commencements_passive': commencements_passive,
            'amendments_passive': amendments_passive,
            'commencements_active': commencements_active,
            'amendments_active': amendments_active,
            'repeals_active': repeals_active,
        }

        rows.append(info)

    # write the works
    row = 0
    for info in rows:
        work = info.get('work')
        for n in range(info.get('n_rows')):
            row += 1
            sheet.write(row, 0, work.country.code)
            sheet.write(row, 1, work.locality.code if work.locality else None)
            sheet.write(row, 2, work.title)
            sheet.write(row, 3, work.properties.get('cap') or "")
            sheet.write(row, 4, work.subtype)
            sheet.write(row, 5, work.number)
            sheet.write(row, 6, work.year)
            sheet.write(row, 7, work.publication_name)
            sheet.write(row, 8, work.publication_number)
            sheet.write(row, 9, work.assent_date, date_format)
            sheet.write(row, 10, work.publication_date, date_format)
            sheet.write(row, 11, work.commencement_date, date_format)
            sheet.write(row, 12, '✔' if work.stub else '')
            sheet.write(row, 13, '; '.join(t.slug for t in work.taxonomies.all()))
            sheet.write(row, 14, uri_title(work.parent_work))
            write_commencement_passive(sheet, row, info, n, date_format)
            write_amendment_passive(sheet, row, info, n, date_format)
            sheet.write(row, 19, uri_title(work.repealed_by))
            sheet.write(row, 20, work.repealed_date, date_format)
            sheet.write(row, 21,
                        '; '.join(uri_title(child) for child in work.child_works.all()))
            write_commencement_active(sheet, row, info, n, date_format)
            write_amendment_active(sheet, row, info, n, date_format)
            write_repeal_active(sheet, row, info, n, date_format)
            sheet.write(row, 28, '✔')
            sheet.write(row, 29, work.frbr_uri)
            sheet.write(row, 30, uri_title(work))


def uri_title(work=None):
    return f'{work.frbr_uri} - {work.title}' if work else ""


def write_commencement_passive(sheet, row, info, n, date_format):
    commencements_passive = info.get('commencements_passive')
    if commencements_passive:
        try:
            commencement = commencements_passive[n]
            # don't rewrite main commencement date if it doesn't have a commencing work
            if commencement == info.get('work').main_commencement and not commencement.commencing_work:
                return
            sheet.write(row, 15, uri_title(commencement.commencing_work))
            sheet.write(row, 16, commencement.date or '(unknown)', date_format)
        except IndexError:
            pass


def write_amendment_passive(sheet, row, info, n, date_format):
    amendments_passive = info.get('amendments_passive')
    if amendments_passive:
        try:
            amendment = amendments_passive[n]
            sheet.write(row, 17, uri_title(amendment.amending_work))
            sheet.write(row, 18, amendment.date, date_format)
        except IndexError:
            pass


def write_commencement_active(sheet, row, info, n, date_format):
    commencements_active = info.get('commencements_active')
    if commencements_active:
        try:
            commencement = commencements_active[n]
            sheet.write(row, 22, uri_title(commencement.commenced_work))
            sheet.write(row, 23, commencement.date or '(unknown)', date_format)
        except IndexError:
            pass


def write_amendment_active(sheet, row, info, n, date_format):
    amendments_active = info.get('amendments_active')
    if amendments_active:
        try:
            amendment = amendments_active[n]
            sheet.write(row, 24, uri_title(amendment.amended_work))
            sheet.write(row, 25, amendment.date, date_format)
        except IndexError:
            pass


def write_repeal_active(sheet, row, info, n, date_format):
    repealed_works = info.get('repeals_active')
    if repealed_works:
        try:
            repealed_work = repealed_works[n]
            sheet.write(row, 26, uri_title(repealed_work))
            sheet.write(row, 27, repealed_work.repealed_date, date_format)
        except IndexError:
            pass
