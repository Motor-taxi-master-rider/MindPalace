import asyncio
import datetime
import os
from contextlib import closing
from typing import Dict, List

import aiohttp
from aiohttp import ClientSession
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.results import UpdateResult

from app import create_app, rq
from app.exceptions import (DataBaseException, DocCacheException,
                            InvalidContentType, MindPalaceException)
from app.globals import (DEFAULT_CACHE_BATCH_SIZE, ENABLED_CACHE_TYPE,
                         MessageQueue)
from app.models import DocumentCache, DocumentMeta, SystemTag, UserTag
from app.utils import parse_content_type


def _check_update_one(result: UpdateResult):
    if result.modified_count != 1:
        raise DataBaseException(
            f'Updated row count is {result.modified_count}.')


async def get_document(collection: AsyncIOMotorCollection, **options) -> List:
    """Async generator to  pop up fulfilled documents from db"""

    default_filter = {
        '$and': [{
            DocumentMeta.tags.db_field: UserTag.cache.value
        }, {
            DocumentMeta.tags.db_field: {
                '$ne': SystemTag.cached.value
            }
        }],
        '.'.join([
            DocumentMeta.cache.db_field, DocumentCache.update_at.db_field
        ]): {
            '$not': {
                '$gt': datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            }
        }
    }
    row_limit = options.get('limit', DEFAULT_CACHE_BATCH_SIZE)
    filter = options.get('filter', default_filter)
    return await collection.find(
        filter, projection=['_id',
                            'url']).limit(row_limit).to_list(length=row_limit)


async def fetch_content(session: ClientSession, url: str) -> str:
    """Crawl text data from given web page."""

    async with session.get(url) as response:
        print(url)
        headers = response.headers
        content_type = parse_content_type(headers['Content-Type'])
        if content_type.type in ENABLED_CACHE_TYPE:
            content = await response.text(
                encoding=content_type.encoding or 'utf-8')
            return content
        else:
            raise InvalidContentType(
                f'Content type of {url} is {content_type.type} is not allowed to cache.'
            )


async def save_content(collection: AsyncIOMotorCollection, id: ObjectId,
                       content: str):
    """Add crawled cache to database and add cached tag to document."""

    result = await collection.update_one({
        '_id': id
    }, {
        '$set': {
            DocumentMeta.cache.db_field: {
                DocumentCache.content.db_field: content,
                DocumentCache.update_at.db_field: datetime.datetime.utcnow()
            }
        },
        '$push': {
            DocumentMeta.tags.db_field: SystemTag.cached.value
        }
    })
    _check_update_one(result)
    await remove_cache_tag(collection, id)


async def add_unable_cache_tag(collection: AsyncIOMotorCollection,
                               id: ObjectId):
    """Append unable to cache tag to document if it is unable to be cached."""

    result = await collection.update_one({
        '_id': id
    }, {
        '$push': {
            DocumentMeta.tags.db_field: SystemTag.unable_to_cache.value
        }
    })
    _check_update_one(result)
    await remove_cache_tag(collection, id)


async def remove_cache_tag(collection: AsyncIOMotorCollection, id: ObjectId):
    """Remove original cache tag of an document."""

    result = await collection.update_one({
        '_id': id
    }, {'$pull': {
        DocumentMeta.tags.db_field: UserTag.cache.value
    }})
    _check_update_one(result)


async def crawl_and_cache(collection: AsyncIOMotorCollection,
                          session: ClientSession, document: Dict) -> int:
    """
    Crawl html from document's url, then save cache to database.

    :param collection: database collection
    :param session: http request session
    :param document: document meta data
    :return: Byte length of saved content
    """

    url = document[DocumentMeta.url.db_field]
    try:
        content = await fetch_content(session, url)
    except aiohttp.client_exceptions.ClientConnectionError:
        raise DocCacheException(f'Enable to connect to {url}.', document)
    except asyncio.TimeoutError:
        raise DocCacheException(f'Time out when running task for {url}.',
                                document)
    except InvalidContentType as exe:
        try:
            await add_unable_cache_tag(collection, document['_id'])
        except DataBaseException as another_exe:
            raise DocCacheException(
                f'Unable to add unable to cache tag to {url}.',
                document) from another_exe
        else:
            raise exe

    await save_content(collection, document['_id'], content)

    return len(content)


async def doc_cache_task(db_name, collection_name, batch):
    """Create database client and http session and start async crawl."""

    with closing(AsyncIOMotorClient()) as client:
        db = client[db_name]
        collection = db[collection_name]
        async with ClientSession() as session:
            tasks = [
                crawl_and_cache(collection, session, document)
                for document in await get_document(collection, limit=batch)
            ]
            for task_to_complete in asyncio.as_completed(tasks):
                try:
                    print(await task_to_complete)
                except MindPalaceException as exe:
                    print(f'{exe.__class__.__name__}: {exe}')
                    if isinstance(exe, DocCacheException):
                        print('Should Requeue.')


@rq.job(MessageQueue.cache, timeout=600)
def doc_cache(batch=DEFAULT_CACHE_BATCH_SIZE):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        asyncio.get_event_loop().run_until_complete(
            doc_cache_task(
                db_name=app.config['MONGODB_DB'],
                collection_name=DocumentMeta._meta['collection'],
                batch=batch))


if __name__ == '__main__':
    doc_cache(10)
