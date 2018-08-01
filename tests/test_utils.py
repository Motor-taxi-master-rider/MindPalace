import pytest

from app.models import Category, DocumentMeta
from app.utils import generate_documents_for_user


@pytest.mark.usefixtures('db')
def test_generate_documents_for_user(admin):
    doc_list = generate_documents_for_user(admin)
    assert set(doc_list) == set(DocumentMeta.objects(create_by=admin).all())
    assert len(doc_list) == sum(range(1, len(Category) + 1))
