import pytest

import app
from app.jobs.doc_cache import get_document, save_content

# pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures('tagged_docs')
async def nottest_get_document(motor_collection):
    list = [document async for document in get_document(motor_collection)]
    assert len(docs) > 1


def test_save_content(event_loop, tagged_docs, motor_collection):
    event_loop.run_until_complete(
        save_content(motor_collection, tagged_docs.id, 'mock_content'))
    tagged_docs.reload()
    assert tagged_docs.cache.content == 'mock_content111'
