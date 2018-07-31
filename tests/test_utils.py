import pytest

from app.models import Category, DocumentMeta
from app.utils import generate_documents_for_user, get_queue


@pytest.mark.usefixtures('db')
def test_generate_documents_for_user(admin):
    doc_list = generate_documents_for_user(admin)
    assert set(doc_list) == set(DocumentMeta.objects(create_by=admin).all())
    assert len(doc_list) == sum(range(1, len(Category) + 1))


def test_get_queue():
    queue_boy = get_queue('boy')
    queuer_same_boy = get_queue('boy')
    queue_girl = get_queue('girl')
    assert queue_boy is queuer_same_boy
    assert queue_boy is not queue_girl
