from contextlib import contextmanager
from queue import Queue
from typing import Tuple
from urllib.parse import urlparse, urlunparse

from flask import Response, template_rendered, url_for
from flask.testing import FlaskClient
from mock import MagicMock
from mongomock import MongoClient

from app.models import User


@contextmanager
def captured_templates(app):
    """Context manger to capture all rendered templates into a list."""

    def record(sender, template, context, **extra):
        nonlocal recorded
        recorded.append((template, context))

    recorded = []
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def create_mock_motor_connection(db: MongoClient) -> Tuple:
    import mongomock
    from collections import deque

    class MockBaseBaseProperties(object):
        codec_options = None
        read_preference = None
        read_concern = None
        write_concern = None

    class MockClient(mongomock.MongoClient):
        def __new__(cls, *args, **kwargs):
            return db

    class MockDatabase(mongomock.Database):
        def __new__(cls, *args, **kwargs):
            def _fix_outgoing(data, _):
                return data

            database_singleton = db.get_database()
            database_singleton._fix_outgoing = _fix_outgoing
            return database_singleton

    class MockCollection(mongomock.Collection, MockBaseBaseProperties):
        count_documents = lambda: True
        create_indexes = lambda: True
        estimated_document_count = lambda: True
        find_one_and_update = lambda: True
        full_name = lambda: True
        name = lambda: True
        options = lambda: True
        aggregate_raw_batches = lambda: True

        def __new__(cls, *args, **kwargs):
            def find(filter=None,
                     projection=None,
                     skip=0,
                     limit=0,
                     no_cursor_timeout=False,
                     cursor_type=None,
                     sort=None,
                     allow_partial_results=False,
                     oplog_replay=False,
                     modifiers=None,
                     batch_size=0,
                     manipulate=True,
                     collation=None,
                     session=None):
                spec = filter
                if spec is None:
                    spec = {}
                return Cursor(
                    collection_singleton,
                    spec,
                    sort,
                    projection,
                    skip,
                    limit,
                    collation=collation)

            collection_singleton = db.get_database().get_collection(
                'document_meta')
            collection_singleton.find = find
            return collection_singleton

    class Cursor(mongomock.collection.Cursor):
        address = None
        cursor_id = None
        alive = True
        session = lambda: True
        collation = lambda: True
        explain = lambda: True
        add_option = lambda: True
        remove_option = lambda: True
        max_scan = lambda: True
        hint = lambda: True
        where = lambda: True
        max_await_time_ms = lambda: True
        max_time_ms = lambda: True
        min = lambda: True
        max = lambda: True
        comment = lambda: True
        _Cursor__die = lambda: False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.__data = deque()
            self.__query_flags = 0

        def _refresh(self):
            try:
                self.__data.append(next(self))
            except StopIteration:
                self.alive = False
            return len(self.__data)

    return MockClient, MockDatabase, MockCollection, Cursor


def login(client: FlaskClient, user: User, password: str = 'test') -> Response:
    """Login a user."""
    return client.post(
        url_for('account.login'),
        data={
            'email': user.email,
            'password': password
        })


def logout(client: FlaskClient) -> Response:
    """Log out current user."""
    return client.get(url_for('account.logout'))


def redirect_to(response: Response) -> str:
    """ Remove argument and query of the response url. """
    url_parse = urlparse(response.headers.get('location'))
    return urlunparse((url_parse.scheme, url_parse.netloc, url_parse.path, '',
                       '', ''))


def real_url(route: str, **arguments) -> str:
    """Return full url of given endpoint."""
    return url_for(route, **arguments, _external=True)


class MockRedisQueue(Queue):
    def enqueue_call(self, _, **kwargs):
        return self.put(kwargs)

    def get_kwargs(self):
        return self.get(False)['kwargs']

    def __getattr__(self, item):
        return MagicMock()
