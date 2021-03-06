import datetime

import pytest
from mongoengine.errors import ValidationError

from app.models import Category, DocumentCache, DocumentMeta, User, UserTag


@pytest.mark.usefixtures('database')
def test_update_time_init():
    dc = DocumentCache(content='test content')
    dm = DocumentMeta(
        theme='test', category=Category.SHORT_TERM.value, cache=dc)
    dm.save()

    assert dm.update_at.timestamp() == pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)
    assert dm.cache.update_at.timestamp() == pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)


@pytest.mark.usefixtures('database')
def test_update_time_change():
    dm = DocumentMeta(theme='test', category=Category.SHORT_TERM.value)
    dm.update_at = datetime.datetime.utcfromtimestamp(1000000000)
    assert dm.update_at.timestamp() != pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)

    dm.save()
    assert dm.update_at.timestamp() == pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)


@pytest.mark.usefixtures('database')
def test_valid_document_category():
    dm = DocumentMeta(theme='valid', category=Category.SHORT_TERM.value)
    dm.save()

    assert dm.category == Category.SHORT_TERM.value


@pytest.mark.usefixtures('database')
def test_invalid_document_category():
    dm = DocumentMeta(theme='invalid', category='invalid')

    with pytest.raises(ValidationError):
        dm.save()


@pytest.mark.usefixtures('database')
def test_large_document_theme():
    long_string = "".join(str(i) for i in range(50))
    dm = DocumentMeta(theme=long_string, category=Category.SHORT_TERM.value)
    dm.save()

    assert dm.theme == long_string
    assert len(str(dm)) < 35


@pytest.mark.usefixtures('database')
def test_large_document_cache_content():
    dc = DocumentCache(content='test content' * 1000)
    dm = DocumentMeta(
        theme='test', category=Category.SHORT_TERM.value, cache=dc)
    dm.save()

    assert dm.cache.content == 'test content' * 1000


@pytest.mark.usefixtures('database')
def test_create_by_user():
    u = User(email='test', password='password')
    u.save()
    dm = DocumentMeta(
        theme='valid', category=Category.SHORT_TERM.value, create_by=u)
    dm.save()

    assert dm.create_by == u
    assert dm.create_by.email == 'test'


@pytest.mark.usefixtures('database')
def test_document_tag():
    dm = DocumentMeta(theme='test', category=Category.SHORT_TERM.value)
    dm.save()
    assert not dm.tags

    dm.tags.append(UserTag.cache.value)
    dm.save()
    dm.reload()
    assert UserTag.cache.value in dm.tags

    dm.tags.append('invalid tag')
    with pytest.raises(ValidationError):
        dm.save()


@pytest.mark.usefixtures('database')
def test_save_document():
    dm = DocumentMeta(
        theme='review_done',
        category=Category.SHORT_TERM.value,
        tags=[UserTag.reviewed.value],
        priority=3)
    dm.save()
    assert dm.priority == 0

    dm = DocumentMeta(
        theme='review_not_done',
        category=Category.SHORT_TERM.value,
        tags=[UserTag.to_do.value],
        priority=3)
    dm.save()
    assert dm.priority == 3
