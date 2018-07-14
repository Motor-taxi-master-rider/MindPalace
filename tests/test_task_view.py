import pytest
from flask import url_for

from app.models import Category, DocumentMeta
from app.task.forms import DocMetaForm
from utils import captured_templates, login, redirect_to, real_url, INVALID_OBJECT_ID


@pytest.mark.usefixtures('doc')
def test_get_my_doc_meta(client, admin):
    login(client, admin)

    with captured_templates(client.application) as templates:
        assert client.get(url_for('task.my_doc_meta')).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['categories'] == Category
        assert list(context['documents']) == list(DocumentMeta.objects(create_by=admin).all())


@pytest.mark.usefixtures('doc')
def test_post_new_doc_meta_success(client, admin):
    login(client, admin)
    data = {
        'theme': 'whats up',
        'category': Category.REVIEWED.value,
        'url': 'https://www.helloword.com',
    }

    with captured_templates(client.application) as templates:
        assert client.post(url_for('task.new_doc_meta'), data=data).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/manage_document.html'
        assert context['action'] == 'Create'
        assert context['data_type'] == 'New Document'
        assert isinstance(context['form'], DocMetaForm)
        assert DocumentMeta.objects.get(theme=data['theme']).url == data['url']
        assert len(DocumentMeta.objects().all()) == 2


def test_post_new_doc_meta_failure(client, admin, doc):
    login(client, admin)
    data = {
        'theme': doc.theme,
        'category': doc.category,
        'url': doc.url,
    }

    client.post(url_for('task.new_doc_meta'), data=data)
    assert len(DocumentMeta.objects().all()) == 1


def test_post_update_doc_meta_success(client, admin, doc):
    login(client, admin)

    with captured_templates(client.application) as templates:
        assert client.get(url_for('task.update_doc_meta', doc_meta_id=str(doc.id))).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/manage_document.html'
        assert context['action'] == 'Update'
        assert context['data_type'] == str(doc)
        form = context['form']
        assert isinstance(form, DocMetaForm)

    form.url.data = 'https://www.newtest.com'
    assert client.post(url_for('task.update_doc_meta', doc_meta_id=str(doc.id)), data=form.data).status_code == 200
    doc.reload()
    assert doc.url == 'https://www.newtest.com'


def test_post_update_doc_meta_failure(client, admin, doc):
    login(client, admin)
    data = {
        'theme': 'whats up',
        'category': Category.REVIEWED.value,
        'url': 'https://www.helloword.com',
    }

    assert client.post(url_for('task.update_doc_meta', doc_meta_id=INVALID_OBJECT_ID), data=data).status_code == 404
    doc.reload()
    assert doc.url == 'https://www.test.com'


def test_post_delete_doc_meta_success_for_admin(client, admin, doc):
    login(client, admin)

    assert redirect_to(client.post(url_for('task.delete_doc_meta', doc_meta_id=str(doc.id)))) == real_url(
        'task.my_doc_meta')
    assert not DocumentMeta.objects(theme=doc.theme).first()


def test_post_delete_doc_meta_success_for_author(client, user, doc):
    login(client, user)

    assert redirect_to(client.post(url_for('task.delete_doc_meta', doc_meta_id=str(doc.id)))) == real_url(
        'task.my_doc_meta')
    assert not DocumentMeta.objects(theme=doc.theme).first()


def test_post_delete_doc_meta_failure(client, another_user, doc):
    login(client, another_user)

    assert client.post(url_for('task.delete_doc_meta', doc_meta_id=INVALID_OBJECT_ID)).status_code == 404
    assert DocumentMeta.objects(theme=doc.theme).first()

    assert client.post(url_for('task.delete_doc_meta', doc_meta_id=str(doc.id))).status_code == 401
    assert DocumentMeta.objects(theme=doc.theme).first()