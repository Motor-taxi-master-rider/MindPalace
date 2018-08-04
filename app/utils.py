import itertools
import re
from collections import namedtuple
from typing import List
from urllib.parse import urljoin, urlparse

from faker import Faker
from flask import Response, redirect, request, url_for

from app.models import Category, DocumentMeta, User

INVALID_OBJECT_ID = '1' * 24
CONTENT_TYPE_REG = re.compile(
    '(?P<type>\w+/\w+)(;\s*charset=(?P<encoding>[\w-]+))?')
ContentType = namedtuple('ContentType', ['type', 'encoding'])


def register_template_utils(app):
    """Register Jinja 2 helpers (called from __init__.py)."""

    @app.template_test()
    def equalto(value, other):
        return value == other

    @app.template_global()
    def is_hidden_field(field):
        from wtforms.fields import HiddenField
        return isinstance(field, HiddenField)

    app.add_template_global(beautify_static)


def beautify_static(name: str) -> str:
    return name.lower().replace('_', ' ').capitalize()


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
                priority=0,
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


def parse_content_type(content_type: str) -> ContentType:
    parse = CONTENT_TYPE_REG.match(content_type)
    if parse:
        match = parse.groupdict()
    else:
        raise TypeError(f'Invalid header content type {content_type}.')
    return ContentType(match.get('type'), match.get('encoding'))


def redirect_back(endpoint: str, **values) -> Response:
    """Redirect to next url if possible, else redirect to endpoint."""
    target = request.args.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)
