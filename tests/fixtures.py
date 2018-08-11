import functools
from collections import defaultdict
from unittest.mock import MagicMock, Mock, patch

import mongomock
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
        import pymongo
        import mongomock

        class MockClient(pymongo.MongoClient):
            def __new__(cls, *args, **kwargs):
                return db

        class MockDatabase(mongomock.Database):
            def __new__(cls, *args, **kwargs):
                return db.get_database()

        class MockCollection(mongomock.Collection,
                             pymongo.collection.Collection):
            def __new__(cls, *args, **kwargs):
                return db.get_database().get_collection('document_meta')

        class Cursor(mongomock.collection.Cursor, pymongo.collection.Cursor):
            def __init__(self, *args, **kwargs):
                pymongo.collection.Collection.__init__(*args, **kwargs)
                mongomock.collection.Cursor.__init__(*args, **kwargs)

        return MockClient, MockDatabase, MockCollection, Cursor

    def mock_cursor_data(self):
        try:
            data = next(self.delegate)
            self.__class__.alive = True
        except StopIteration:
            data = {}
            self.__class__.alive = False

        return data

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
    patch_list.append(
        patch('motor.core.AgnosticCursor._data', mock_cursor_data))
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
