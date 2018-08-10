from collections import defaultdict
from unittest.mock import MagicMock, Mock, patch

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


@pytest.fixture(scope='function')
def mongo_client(app):
    client = connect()
    Role.insert_roles()
    yield client
    client.drop_database(app.config['MOCK_MONGO'])


@pytest.fixture(scope='function')
def admin(mongo_client):
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
def user(mongo_client):
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
def another_user(mongo_client):
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
def doc(mongo_client, user):
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
def doc_list(mongo_client, admin):
    doc_list = generate_documents_for_user(admin)
    yield list(reversed(doc_list))
    for doc in doc_list:
        doc.delete()


@pytest.fixture(scope='function')
def tagged_docs(doc_list):
    for document in DocumentMeta.objects(
            Q(category=Category.LONG_TERM.value)
            | Q(category=Category.SHORT_TERM.value)):
        document.tags.append(UserTag.cache.value)
        document.save()
    document.reload()
    yield document


@pytest.fixture(scope='function')
def motor_collection(app, mongo_client, doc_list, event_loop):
    patch('motor.metaprogramming._class_cache', {}).start()
    client, database, collection = create_mock_db(mongo_client)
    patch('motor.core.AgnosticClient.__delegate_class__', client).start()
    # motor.core.AgnosticDatabase.__delegate_class__ = database
    patch('motor.core.AgnosticCollection.__delegate_class__',
          collection).start()
    patch('motor.core.Database', database).start()
    patch('motor.core.Collection', collection).start()
    # motor.motor_asyncio.AsyncIOMotorClient = motor.motor_asyncio.create_asyncio_class(
    #     motor.core.AgnosticClient)
    # motor.motor_asyncio.AsyncIOMotorDatabase = motor.motor_asyncio.create_asyncio_class(
    #     motor.core.AgnosticDatabase)
    # motor.motor_asyncio.AsyncIOMotorCollection = motor.motor_asyncio.create_asyncio_class(
    #     motor.core.AgnosticCollection)

    client = motor.motor_asyncio.AsyncIOMotorClient(io_loop=event_loop)
    collection = client[app.config['MONGODB_DB']][DocumentMeta._meta[
        'collection']]
    yield collection
    client.close()


def create_mock_db(db):
    import pymongo
    import mongomock

    class MockClient(pymongo.MongoClient):
        def __new__(cls, *args, **kwargs):
            return db

    class MockDatabse(mongomock.Database):
        def __new__(cls, *args, **kwargs):
            return db.get_database()

    class MockCollection(mongomock.Collection, pymongo.collection.Collection):
        def __new__(cls, *args, **kwargs):
            return db.get_database().get_collection('document_meta')

    return MockClient, MockDatabse, MockCollection
