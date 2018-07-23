import itertools
from typing import List
from urllib.parse import urljoin, urlparse

from faker import Faker
from flask import Response, redirect, request, url_for

from app.models import Category, DocumentMeta, User

INVALID_OBJECT_ID = '1' * 24


def register_template_utils(app):
    """Register Jinja 2 helpers (called from __init__.py)."""

    @app.template_test()
    def equalto(value, other):
        return value == other

    @app.template_global()
    def is_hidden_field(field):
        from wtforms.fields import HiddenField
        return isinstance(field, HiddenField)

    app.add_template_global(index_for_role)


def index_for_role(role):
    return url_for(role.index)


def generate_documents_for_user(user: User) -> List[DocumentMeta]:
    """Generate document list for given user."""
    faker = Faker()
    doc_list = []
    for category, doc_amount in zip(Category, range(1, len(Category) + 1)):
        for _ in itertools.repeat(None, doc_amount):
            doc_meta = DocumentMeta(
                theme=faker.sentence(),
                category=category.value,
                url=faker.url(),
                priority=1,
                create_by=user)
            doc_meta.save()
            doc_list.append(doc_meta)
    return doc_list


def is_safe_url(target: str) -> bool:
    """Verdict whether a url is safe to redirect to."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def redirect_back(endpoint: str, **values) -> Response:
    """Redirect to next url if possible, else redirect to endpoint."""
    target = request.args.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)
