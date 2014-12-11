"""Simple NITF parser"""

from datetime import datetime
from superdesk.io import Parser
from superdesk.io import get_word_count
import xml.etree.ElementTree as etree

ITEM_CLASS_TEXT = 'text'
ITEM_CLASS_PRE_FORMATTED = 'preformatted'

subject_fields = ('tobject.subject.type', 'tobject.subject.matter', 'tobject.subject.detail')


def get_places(docdata):
    places = []
    evloc = docdata.find('evloc')
    if evloc is not None:
        places.append({
            'name': evloc.attrib.get('city'),
            'code': evloc.attrib.get('iso-cc'),
        })
    return places


def get_subjects(tree):
    subjects = []
    for elem in tree.findall('head/tobject/tobject.subject'):
        qcode = elem.get('tobject.subject.refnum')
        for field in subject_fields:
            if elem.get(field):
                subjects.append({
                    'name': elem.get(field)
                })

        if len(subjects):
            subjects[-1]['qcode'] = qcode
    return subjects


def get_keywords(docdata):
    return [keyword.attrib['key'] for keyword in docdata.findall('key-list/keyword')]


def get_content(tree):
    elements = []
    for elem in tree.find('body/body.content'):
        elements.append(etree.tostring(elem, encoding='unicode'))
    return ''.join(elements)


def get_norm_datetime(tree):
    if tree is None:
        return
    try:
        return datetime.strptime(tree.attrib['norm'], '%Y%m%dT%H%M%S')
    except ValueError:
        return datetime.strptime(tree.attrib['norm'], '%Y%m%dT%H%M%S%z')


def get_byline(tree):
    elem = tree.find('body/body.head/byline')
    byline = ''
    if elem is not None:
        byline = elem.text
        person = elem.find('person')
        if person is not None:
            byline = "{} {}".format(byline.strip(), person.text.strip())
    return byline


def parse_meta(tree, item):
    for elem in tree.findall('head/meta'):
        attribute_name = elem.get('name')

        if attribute_name == 'anpa-keyword':
            item['slugline'] = elem.get('content')
        elif attribute_name == 'anpa-sequence':
            item['ingest_provider_sequence'] = elem.get('content')
        elif attribute_name == 'anpa-category':
            item['anpa-category'] = {'qcode': elem.get('content'), 'name': ''}
        elif attribute_name == 'anpa-wordcount':
            item['word_count'] = int(elem.get('content'))
        elif attribute_name == 'anpa-takekey':
            item['anpa_take_key'] = elem.get('content')
        elif attribute_name == 'anpa-format':
            anpa_format = elem.get('content').lower() if elem.get('content') is not None else 'x'
            item['type'] = ITEM_CLASS_TEXT if anpa_format == 'x' else ITEM_CLASS_PRE_FORMATTED


class NITFParser(Parser):
    """
    NITF Parser
    """

    def parse_message(self, tree):
        item = {}
        docdata = tree.find('head/docdata')
        # set the default type.
        item['type'] = ITEM_CLASS_TEXT
        item['guid'] = item['uri'] = docdata.find('doc-id').get('id-string')
        item['urgency'] = docdata.find('urgency').get('ed-urg', '5')
        item['pubstatus'] = docdata.attrib.get('management-status', 'usable')
        item['firstcreated'] = get_norm_datetime(docdata.find('date.issue'))
        item['versioncreated'] = get_norm_datetime(docdata.find('date.issue'))
        item['expiry'] = get_norm_datetime(docdata.find('date.expire'))
        item['subject'] = get_subjects(tree)
        item['body_html'] = get_content(tree)
        item['place'] = get_places(docdata)
        item['keywords'] = get_keywords(docdata)

        if docdata.find('ed-msg') is not None:
            item['ednote'] = docdata.find('ed-msg').attrib.get('info')

        item['headline'] = tree.find('body/body.head/hedline/hl1').text

        elem = tree.find('body/body.head/abstract')
        item['abstract'] = elem.text if elem is not None else ''

        elem = tree.find('body/body.head/dateline/location/city')
        item['dateline'] = elem.text if elem is not None else ''
        item['byline'] = get_byline(tree)

        parse_meta(tree, item)
        item.setdefault('word_count', get_word_count(item['body_html']))
        return item
