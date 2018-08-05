import pytest

from app.models import Category, DocumentMeta
from app.utils import (beautify_static, generate_documents_for_user,
                       parse_content_type)


@pytest.mark.usefixtures('db')
def test_generate_documents_for_user(admin):
    doc_list = generate_documents_for_user(admin)
    assert set(doc_list) == set(DocumentMeta.objects(create_by=admin).all())
    assert len(doc_list) == sum(range(1, len(Category) + 1)) * 3


def test_beautify_static():
    assert beautify_static('Capital') == 'Capital'
    assert beautify_static('UPPER') == 'Upper'
    assert beautify_static('WhAt\'s Up?') == 'What\'s up?'
    assert beautify_static('str_TO_format') == 'Str to format'


def test_parse_content_type():
    assert parse_content_type('application/pdf') == ('application/pdf', None)
    assert parse_content_type('text/html; charset=utf-8') == ('text/html',
                                                              'utf-8')
    assert parse_content_type('text/html;charset=UTF-8') == ('text/html',
                                                             'UTF-8')
