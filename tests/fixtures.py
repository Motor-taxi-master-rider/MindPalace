from collections import defaultdict
from unittest.mock import patch

import motor
import pytest
from mongoengine import Q, connect

from app import create_app
from app.models import Category, DocumentMeta, Role, User, UserTag
from app.utils import generate_documents_for_user
from tests.utils import MockRedisQueue


@pytest.fixture(scope='module')
def app():
    queues = defaultdict(MockRedisQueue)
    with patch('flask_rq2.RQ.get_queue', lambda _, name: queues[name]):
        app = create_app('testing')
        with app.app_context():
            yield app


@pytest.fixture(scope='module')
def mongo_client(app):
    client = connect()
    yield client


@pytest.fixture(scope='function')
def database(app, mongo_client):
    Role.insert_roles()
    yield
    mongo_client.drop_database(app.config['MOCK_MONGO'])


@pytest.fixture(scope='function')
def admin(database):
    admin_role = Role.objects(name='Administrator').first()
    admin = User(
        first_name='Admin',
        last_name='Account',
        password='test',
        confirmed=True,
        email='admin@admin.com',
        role=admin_role)
    admin.save()
    yield admin
    admin.delete()


@pytest.fixture(scope='function')
def user(database):
    user_role = Role.objects(name='User').first()
    user = User(
        first_name='User',
        last_name='Account',
        password='test',
        confirmed=True,
        email='user@user.com',
        role=user_role)
    user.save()
    yield user
    user.delete()


@pytest.fixture(scope='function')
def another_user(database):
    user_role = Role.objects(name='User').first()
    user = User(
        first_name='User another',
        last_name='Account',
        password='test',
        confirmed=True,
        email='another_user@user.com',
        role=user_role)
    user.save()
    yield user
    user.delete()


@pytest.fixture(scope='function')
def doc(database, user):
    doc_meta = DocumentMeta(
        theme='hello world',
        category=Category.SHORT_TERM.value,
        url='https://www.test.com',
        priority=1,
        create_by=user)
    dup_doc_meta = DocumentMeta(
        theme='duplicate',
        category=Category.SHORT_TERM.value,
        url='https://www.duplicate.com',
        priority=1,
        create_by=user)
    doc_meta.save()
    dup_doc_meta.save()
    yield doc_meta
    doc_meta.delete()
    dup_doc_meta.delete()


@pytest.fixture(scope='function')
def doc_list(database, admin):
    doc_list = generate_documents_for_user(admin)
    yield list(reversed(doc_list))
    for doc in doc_list:
        doc.delete()


@pytest.fixture(scope='function')
def tagged_docs(doc_list):
    docs_to_tag = DocumentMeta.objects(
        Q(category=Category.LONG_TERM.value)
        | Q(category=Category.SHORT_TERM.value))
    for document in docs_to_tag:
        document.tags.append(UserTag.cache.value)
        document.save()
        document.reload()
    yield docs_to_tag


@pytest.fixture(scope='module')
def patch_motor(mongo_client):
    def create_mock_db(db):
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

    client, database, collection, cursor = create_mock_db(mongo_client)
    patch_list = []
    patch_list.append(patch('motor.metaprogramming._class_cache', {}))
    patch_list.append(
        patch('motor.core.AgnosticClient.__delegate_class__', client))
    patch_list.append(
        patch('motor.core.AgnosticCollection.__delegate_class__', collection))
    patch_list.append(
        patch('motor.core.AgnosticCursor.__delegate_class__', cursor))
    patch_list.append(patch('motor.core.Database', database))
    patch_list.append(patch('motor.core.Collection', collection))
    for patch_item in patch_list:
        patch_item.start()
    yield
    for patch_item in patch_list:
        patch_item.stop()


@pytest.fixture(scope='function')
def motor_collection(app, patch_motor, doc_list, event_loop):
    client = motor.motor_asyncio.AsyncIOMotorClient(io_loop=event_loop)
    collection = client[app.config['MONGODB_DB']][DocumentMeta._meta[
        'collection']]
    yield collection
    client.close()
