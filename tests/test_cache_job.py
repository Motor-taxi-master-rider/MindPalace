import datetime
from unittest.mock import MagicMock

import pytest
from mongoengine import Q
from utils import mock_coroutine

from app.exceptions import DataBaseException
from app.globals import INVALID_OBJECT_ID
from app.jobs.doc_cache import (add_unable_cache_tag, get_document,
                                remove_cache_tag, save_content)
from app.models import Category, DocumentMeta, SystemTag, UserTag

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures('tagged_docs')
async def test_get_document(motor_collection):
    docs = await get_document(motor_collection)
    assert len(docs) == 10  # default limit
    assert {doc['_id']
            for doc in docs} <= {
                doc.id
                for doc in DocumentMeta.objects(
                    Q(category=Category.LONG_TERM.value)
                    | Q(category=Category.SHORT_TERM.value))
            }

    docs = await get_document(motor_collection, limit=5)
    assert len(docs) == 5

    docs = await get_document(
        motor_collection, filter={'category': Category.FLIP.value})
    assert [doc['_id'] for doc in docs] == [
        doc.id for doc in DocumentMeta.objects(category=Category.FLIP.value)
    ]


async def test_save_content(tagged_docs, motor_collection):
    await save_content(motor_collection, tagged_docs[0].id, 'mock_content')
    tagged_docs[0].reload()
    assert tagged_docs[0].cache.content == 'mock_content'
    assert tagged_docs[0].cache.update_at.timestamp() == pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)
    assert SystemTag.cached.value in tagged_docs[0].tags
    assert UserTag.cache.value not in tagged_docs[0].tags

    with pytest.raises(DataBaseException):
        await save_content(motor_collection, INVALID_OBJECT_ID, 'mock_content')


async def test_add_unable_cache_tag(tagged_docs, motor_collection,
                                    monkeypatch):
    monkeypatch.setattr('app.jobs.doc_cache.remove_cache_tag', mock_coroutine)
    await add_unable_cache_tag(motor_collection, tagged_docs[0].id)
    tagged_docs[0].reload()
    assert SystemTag.unable_to_cache.value in tagged_docs[0].tags

    with pytest.raises(DataBaseException):
        await add_unable_cache_tag(motor_collection, INVALID_OBJECT_ID)


async def test_remove_cache_tag(tagged_docs, motor_collection):
    await remove_cache_tag(motor_collection, tagged_docs[0].id)
    tagged_docs[0].reload()
    assert UserTag.cache.value not in tagged_docs[0].tags

    with pytest.raises(DataBaseException):
        await remove_cache_tag(motor_collection, INVALID_OBJECT_ID)
