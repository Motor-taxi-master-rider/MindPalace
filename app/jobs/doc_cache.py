import asyncio
import datetime
import os
from contextlib import closing
from pprint import pprint
from typing import AsyncGenerator, Dict

import aiohttp
from aiohttp import ClientSession
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app import create_app
from app.exceptions import (DocCacheException, InvalidContentType,
                            MindPalaceException)
from app.globals import ENABLED_CACHE_TYPE
from app.models import DocumentCache, DocumentMeta
from app.utils import parse_content_type


async def get_document(collection: AsyncIOMotorCollection,
                       **options) -> AsyncGenerator:
    """Async generator to  pop up fulfilled documents from db"""
    default_filter = {
        'cache.update_at': {
            '$not': {
                '$gt': datetime.datetime.utcnow() - datetime.timedelta(days=1)
            }
        }
    }
    row_limit = options.get('limit', 10)
    filter = options.get('filter', default_filter)
    async for document in collection.find(filter).limit(row_limit):
        yield document


async def fetch_content(session: ClientSession, url: str) -> str:
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
                       content: str) -> int:
    result = await collection.update_one({
        '_id': id
    }, {
        '$set': {
            'cache': {
                DocumentCache.content.db_field: content,
                DocumentCache.update_at.db_field: datetime.datetime.utcnow()
            }
        }
    })
    return result.modified_count


async def crawl_and_cache(collection: AsyncIOMotorCollection,
                          session: ClientSession, document: Dict) -> bool:
    try:
        content = await fetch_content(session, document['url'])
    except aiohttp.client_exceptions.ClientConnectionError:
        raise DocCacheException(f'Enable to connect to {document["url"]}.',
                                document)
    except asyncio.TimeoutError:
        raise DocCacheException(
            f'Time out when running task for {document["url"]}.', document)

    update_row = await save_content(collection, document['_id'], content)
    if update_row != 1:
        raise DocCacheException(
            f'Update for content ...{content[100:300]}... of {document["url"]} affected {update_row} row.',
            document)

    return True


async def doc_cache_task(db_name, collection_name):
    with closing(AsyncIOMotorClient()) as client:
        db = client[db_name]
        collection = db[collection_name]
        async with ClientSession() as session:
            tasks = [
                crawl_and_cache(collection, session, document)
                async for document in get_document(collection)
            ]
            for task_to_complete in asyncio.as_completed(tasks):
                try:
                    print(await task_to_complete)
                except MindPalaceException as exe:
                    print(f'{exe.__class__.__name__}: {exe}')
                    if isinstance(exe, DocCacheException):
                        print('Should Requeue.')
                    else:
                        print('Add unable to queue tag.')


def doc_cache():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        asyncio.get_event_loop().run_until_complete(
            doc_cache_task(
                db_name=app.config['MONGODB_DB'],
                collection_name=DocumentMeta._meta['collection']))


if __name__ == '__main__':
    doc_cache()
