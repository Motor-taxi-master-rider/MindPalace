import pytest

from app.jobs.doc_cache import get_document, save_content

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures('tagged_docs')
async def nottest_get_document(motor_collection):
    docs = [document async for document in get_document(motor_collection)]
    assert len(docs) > 1


async def test_save_content(tagged_docs, motor_collection):
    await save_content(motor_collection, tagged_docs.id, 'mock_content')
    tagged_docs.reload()
    assert tagged_docs.cache.content == 'mock_content'
