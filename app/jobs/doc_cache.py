import asyncio
from contextlib import closing
from pprint import pprint
from typing import AsyncGenerator, Dict

import aiohttp
from aiohttp import ClientSession
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


async def get_document(collection: AsyncIOMotorCollection,
                       **options) -> AsyncGenerator:
    """Async generator to  pop up fulfilled documents from db"""
    row_limit = options.get('limit', 5)
    filter = options.get('filter', {})
    async for document in collection.find(filter).limit(row_limit):
        yield document


async def fetch_content(session: ClientSession, url: str) -> str:
    async with session.get(url) as response:
        try:
            content = await response.text()
        except UnicodeDecodeError:
            content = response.headers
        return content


async def save_content(collection: AsyncIOMotorCollection, id: ObjectId,
                       content: str) -> int:
    result = await collection.update_one({
        '_id': id
    }, {'$set': {
        'cache': {
            'content': content
        }
    }})
    print(result.modified_count)
    return result.modified_count


async def crawl_and_cache(collection: AsyncIOMotorCollection,
                          session: ClientSession, document: Dict) -> bool:
    try:
        content = await fetch_content(session, document['url'])
    except aiohttp.client_exceptions.ClientConnectionError:
        print(f'Enable to connect to {document["url"]}')
        return False
    update_row = await save_content(collection, document['_id'], content)
    if update_row != 1:
        return False
    return True


async def doc_cache_task(db_name='doc_search',
                         collection_name='document_meta'):
    with closing(AsyncIOMotorClient()) as client:
        db = client[db_name]
        collection = db[collection_name]
        async with ClientSession() as session:
            tasks = [
                crawl_and_cache(collection, session, document)
                async for document in get_document(collection)
            ]
            for task_to_complete in asyncio.as_completed(tasks):
                pprint(await task_to_complete)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(doc_cache_task())
