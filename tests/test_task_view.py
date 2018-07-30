import pytest
from flask import url_for
from utils import captured_templates, login, real_url, redirect_to

from app.models import Category, DocumentMeta
from app.task.forms import DocMetaForm
from app.task.views import ALL_CATEGORY
from app.utils import INVALID_OBJECT_ID


@pytest.mark.usefixtures('doc_list')
def test_get_my_doc_meta(client, admin, monkeypatch):
    login(client, admin)
    monkeypatch.setattr('app.task.views.DOCUMENT_PER_PAGE', 3)

    with captured_templates(client.application) as templates:
        assert client.get(url_for('task.my_doc_meta')).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['categories'] == {c.value: c.name for c in Category}
        assert context['current_category'] == ALL_CATEGORY
        assert list(context['documents'].items) == list(
            DocumentMeta.objects(create_by=admin).order_by(
                '-priority', '-update_at').all()[:3])

        assert client.get(url_for('task.my_doc_meta',
                                  page=2)).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['current_category'] == ALL_CATEGORY
        assert list(context['documents'].items) == list(
            DocumentMeta.objects(create_by=admin).order_by(
                '-priority', '-update_at').all()[3:6])


@pytest.mark.usefixtures('doc_list')
def test_get_my_doc_meta_with_category(client, admin, monkeypatch):
    login(client, admin)
    monkeypatch.setattr('app.task.views.DOCUMENT_PER_PAGE', 3)

    with captured_templates(client.application) as templates:
        assert client.get(
            url_for('task.my_doc_meta',
                    category=Category.FLIP.name)).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['current_category'] == Category.FLIP.name
        assert list(context['documents'].items) == list(
            DocumentMeta.objects(
                create_by=admin, category=Category.FLIP.value).order_by(
                    '-priority', '-update_at').all())

        assert client.get(
            url_for(
                'task.my_doc_meta', category=Category.REVIEWED.name,
                page=2)).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['current_category'] == Category.REVIEWED.name
        assert list(context['documents'].items) == list(
            DocumentMeta.objects(
                create_by=admin, category=Category.REVIEWED.value).order_by(
                    '-priority', '-update_at').all()[3:6])


@pytest.mark.usefixtures('doc_list')
def test_get_my_doc_meta_with_search(client, admin, monkeypatch):
    login(client, admin)
    monkeypatch.setattr('app.task.views.DOCUMENT_PER_PAGE', 3)

    with captured_templates(client.application) as templates:
        # search empty string to return all documents
        assert client.get(url_for('task.my_doc_meta',
                                  search='')).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/document_dashboard.html'
        assert context['current_search'] == ''
        assert list(context['documents'].items) == list(
            DocumentMeta.objects(create_by=admin).order_by(
                '-priority', '-update_at').all()[:3])


@pytest.mark.usefixtures('doc')
def test_post_new_doc_meta_success(client, admin):
    login(client, admin)
    data = {
        'theme': 'whats up',
        'category': Category.REVIEWED.value,
        'url': 'https://www.helloword.com',
    }

    assert redirect_to(client.post(url_for('task.new_doc_meta'),
                                   data=data)) == real_url('task.new_doc_meta')
    assert DocumentMeta.objects.get(theme=data['theme']).url == data['url']
    assert DocumentMeta.objects(theme=data['theme']).first()


def test_post_new_doc_meta_failure(client, admin, doc):
    login(client, admin)
    data = {
        'theme': doc.theme,
        'category': doc.category,
        'url': doc.url,
    }

    client.post(url_for('task.new_doc_meta'), data=data)
    assert len(DocumentMeta.objects(theme=data['theme']).all()) == 1


def test_post_update_doc_meta_success(client, admin, doc):
    login(client, admin)

    with captured_templates(client.application) as templates:
        assert client.get(
            url_for('task.update_doc_meta',
                    doc_meta_id=str(doc.id))).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/manage_document.html'
        assert context['action'] == 'Update'
        assert context['data_type'] == str(doc)
        form = context['form']
        assert isinstance(form, DocMetaForm)

    form.theme.data = 'new theme'
    form.category.data = Category.HIGHLIGHT.value
    form.url.data = 'https://www.newtest.com'
    form.priority.data = 3
    assert redirect_to(client.post(url_for('task.update_doc_meta', doc_meta_id=str(doc.id)), data=form.data)) == \
           real_url('task.update_doc_meta', doc_meta_id=str(doc.id))
    doc.reload()
    assert doc.theme == 'new theme'
    assert doc.category == Category.HIGHLIGHT.value
    assert doc.url == 'https://www.newtest.com'
    assert doc.priority == 3


def test_post_update_doc_meta_failure(client, admin, doc):
    login(client, admin)
    data = {
        'theme': 'duplicate',
        'category': Category.REVIEWED.value,
        'url': 'https://www.helloword.com',
        'priority': 1
    }

    assert client.post(
        url_for('task.update_doc_meta', doc_meta_id=INVALID_OBJECT_ID),
        data=data).status_code == 404
    doc.reload()
    assert doc.url == 'https://www.test.com'

    with captured_templates(client.application) as templates:
        assert client.post(
            url_for('task.update_doc_meta', doc_meta_id=str(doc.id)),
            data=data).status_code == 200
        template, context = templates.pop()
        assert template.name == 'task/manage_document.html'
        form = context['form']
        assert not form.validate()
    doc.reload()
    assert doc.url == 'https://www.test.com'


def test_post_delete_doc_meta_success_for_admin(client, admin, doc):
    login(client, admin)

    assert redirect_to(
        client.post(url_for('task.delete_doc_meta', doc_meta_id=str(
            doc.id)))) == real_url('task.my_doc_meta')
    assert not DocumentMeta.objects(theme=doc.theme).first()


def test_post_delete_doc_meta_success_for_author(client, user, doc):
    login(client, user)

    assert redirect_to(
        client.post(url_for('task.delete_doc_meta', doc_meta_id=str(
            doc.id)))) == real_url('task.my_doc_meta')
    assert not DocumentMeta.objects(theme=doc.theme).first()


def test_post_delete_doc_meta_failure(client, another_user, doc):
    login(client, another_user)

    assert client.post(
        url_for('task.delete_doc_meta',
                doc_meta_id=INVALID_OBJECT_ID)).status_code == 404
    assert DocumentMeta.objects(theme=doc.theme).first()

    assert client.post(
        url_for('task.delete_doc_meta',
                doc_meta_id=str(doc.id))).status_code == 401
    assert DocumentMeta.objects(theme=doc.theme).first()
