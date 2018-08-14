from contextlib import contextmanager
from queue import Queue
from typing import Any, Coroutine, Generic, List, Optional, Tuple, Type, Union
from urllib.parse import urlparse, urlunparse

from flask import Response, template_rendered, url_for
from flask.testing import FlaskClient
from mock import MagicMock
from mongomock import MongoClient

from app.models import User
from app.utils import T


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
        def count_documents(mock):
            return True

        def create_indexes(mock):
            return True

        def estimated_document_count(mock):
            return True

        def find_one_and_update(mock):
            return True

        def full_name(mock):
            return True

        def name(mock):
            return True

        def options(mock):
            return True

        def aggregate_raw_batches(mock):
            return True

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

        def session(mock):
            return True

        def collation(mock):
            return True

        def explain(mock):
            return True

        def add_option(mock):
            return True

        def remove_option(mock):
            return True

        def max_scan(mock):
            return True

        def hint(mock):
            return True

        def where(mock):
            return True

        def max_await_time_ms(mock):
            return True

        def max_time_ms(mock):
            return True

        def min(mock):
            return True

        def max(mock):
            return True

        def comment(mock):
            return True

        def _Cursor__die(mock):
            return False

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


def mock_coroutine(return_value: Optional[T] = None,
                   side_effects: Optional[Union[List[Type], Type]] = None
                   ) -> Coroutine[Any, Any, Optional[T]]:
    async def _coroutine(*args, **kwargs) -> Optional[T]:
        if return_value:
            return return_value

        if side_effects:
            if isinstance(side_effects, list):
                side_effect = side_effects.pop(0)
            else:
                side_effect = side_effects
            if issubclass(side_effect, Exception):
                raise side_effect()
        return None

    return _coroutine  # type: ignore


class MockRedisQueue(Queue):
    def enqueue_call(self, _, **kwargs):
        return self.put(kwargs)

    def get_kwargs(self):
        return self.get(False)['kwargs']

    def __getattr__(self, item):
        return MagicMock()
