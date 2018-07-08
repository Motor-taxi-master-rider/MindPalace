from app.models import Category, DocumentCache, DocumentMeta, User
import pytest
import datetime
from mongoengine.errors import ValidationError


@pytest.mark.usefixtures('db')
def test_update_time_init():
    dm = DocumentMeta(theme='test', category=Category.REVIEWED.value)
    dc = DocumentCache(content='test content')
    dm.save()
    dc.save()
    assert dm.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)
    assert dc.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)


@pytest.mark.usefixtures('db')
def test_update_time_change():
    dm = DocumentMeta(theme='test', category=Category.REVIEWED.value)
    dm.update_at = datetime.datetime.utcfromtimestamp(1000000000)
    dc = DocumentCache(content='test content')
    dc.update_at = datetime.datetime.utcfromtimestamp(1000000000)
    assert dm.update_at.timestamp() != pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)
    assert dc.update_at.timestamp() != pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)

    dm.save()
    dc.save()
    assert dm.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)
    assert dc.update_at.timestamp() == pytest.approx(datetime.datetime.utcnow().timestamp(), abs=1)


@pytest.mark.usefixtures('db')
def test_valid_document_category():
    dm = DocumentMeta(theme='valid', category=Category.REVIEWED.value)
    dm.save()
    assert dm.category == Category.REVIEWED.value


@pytest.mark.usefixtures('db')
def test_invalid_document_category():
    dm = DocumentMeta(theme='invalid', category='invalid')
    with pytest.raises(ValidationError):
        dm.save()


@pytest.mark.usefixtures('db')
def test_large_document_theme():
    long_string = "".join(str(i) for i in range(50))
    dm = DocumentMeta(theme=long_string, category=Category.REVIEWED.value)
    dm.save()
    assert dm.theme == long_string
    assert len(str(dm)) < 35


@pytest.mark.usefixtures('db')
def test_large_document_cache_content():
    dc = DocumentCache(content='test content' * 1000)
    dc.save()
    assert dc.content == 'test content' * 1000


@pytest.mark.usefixtures('db')
def test_create_by_user():
    u = User(email='test', password='password')
    u.save()
    dm = DocumentMeta(theme='valid', category=Category.REVIEWED.value, create_by=u)
    dm.save()
    assert dm.create_by == u
    assert dm.create_by.email == 'test'
