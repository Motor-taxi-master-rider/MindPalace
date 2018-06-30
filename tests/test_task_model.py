from app.models import Category, DocumentCache, DocumentMeta
import pytest
import datetime
from mongoengine.errors import ValidationError


def test_update_time(test_app):
    dm = DocumentMeta(theme='test', category=Category.REVIEWED.value)
    dc = DocumentCache(content='test content')
    dm.save()
    dc.save()
    assert dm.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), 3)
    assert dc.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), 3)


def test_valid_document_category(test_app):
    dm = DocumentMeta(theme='valid', category=Category.REVIEWED.value)
    dm.save()
    assert dm.category == Category.REVIEWED.value


def test_invalid_document_category(test_app):
    dm = DocumentMeta(theme='invalid', category='invalid')
    with pytest.raises(ValidationError):
        dm.save()


def test_large_document_theme(test_app):
    long_string = "".join(str(i) for i in range(50))
    dm = DocumentMeta(theme=long_string, category=Category.REVIEWED.value)
    dm.save()
    assert dm.theme == long_string
    assert len(repr(dm)) < 40


def test_large_document_cache_content(test_app):
    dc = DocumentCache(content='test content' * 1000)
    dc.save()
    assert dc.content == 'test content' * 1000
