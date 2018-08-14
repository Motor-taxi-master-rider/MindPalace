import asyncio
import datetime
from unittest.mock import MagicMock

import aiohttp
import pytest
from mongoengine import Q
from utils import mock_coroutine

from app.exceptions import (DataBaseException, DocCacheException,
                            InvalidContentType)
from app.globals import INVALID_OBJECT_ID
from app.jobs.doc_cache import (add_unable_cache_tag, crawl_and_cache,
                                fetch_content, get_document, remove_cache_tag,
                                save_content)
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


async def test_fetch_content(aiohttp_response):
    pdf_url = 'http://pdf.com'
    txt_without_encoding_url = 'http://txt_without_encoding.com'
    txt_with_encoding_url = 'http://txt_with_encoding.com'
    aiohttp_response.get(
        pdf_url, body='hello', headers={'Content-Type': 'application/pdf'})
    aiohttp_response.get(
        txt_without_encoding_url,
        body='hello',
        headers={'Content-Type': 'text/html'})
    aiohttp_response.get(
        txt_with_encoding_url,
        body='你好'.encode('gbk'),
        headers={'Content-Type': 'text/plain; charset=gbk'})

    async with aiohttp.ClientSession() as session:
        with pytest.raises(InvalidContentType):
            await fetch_content(session, pdf_url)

        assert await fetch_content(session,
                                   txt_without_encoding_url) == 'hello'

        assert await fetch_content(session, txt_with_encoding_url) == '你好'


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
    monkeypatch.setattr('app.jobs.doc_cache.remove_cache_tag',
                        mock_coroutine())
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


async def test_crawl_and_cache(motor_collection, monkeypatch):
    document = {'_id': 'test', 'url': 'http://test.com'}
    monkeypatch.setattr(
        'app.jobs.doc_cache.fetch_content',
        mock_coroutine(side_effects=[
            aiohttp.client_exceptions.ClientConnectionError,
            asyncio.TimeoutError, InvalidContentType
        ]))
    monkeypatch.setattr('app.jobs.doc_cache.add_unable_cache_tag',
                        mock_coroutine())
    monkeypatch.setattr('app.jobs.doc_cache.save_content', mock_coroutine())

    async with aiohttp.ClientSession() as session:
        with pytest.raises(DocCacheException):
            await crawl_and_cache(motor_collection, session, document)

        with pytest.raises(DocCacheException):
            await crawl_and_cache(motor_collection, session, document)

        with pytest.raises(InvalidContentType):
            await crawl_and_cache(motor_collection, session, document)

        monkeypatch.setattr(
            'app.jobs.doc_cache.fetch_content',
            mock_coroutine(return_value='12345'))
        assert await crawl_and_cache(motor_collection, session, document) == 5
