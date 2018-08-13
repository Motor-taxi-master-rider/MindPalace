import datetime

import pytest

from app.exceptions import DataBaseException
from app.globals import INVALID_OBJECT_ID
from app.jobs.doc_cache import get_document, save_content
from app.models import SystemTag, UserTag

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures('tagged_docs')
async def test_get_document(motor_collection):
    docs = await get_document(motor_collection)
    assert len(docs) > 1


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
