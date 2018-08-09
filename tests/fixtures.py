from collections import defaultdict
from unittest.mock import Mock, patch, MagicMock

import motor
import pytest
from mongoengine import Q, connect
import motor

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
def db(app):
    client = connect()
    Role.insert_roles()
    yield client
    client.drop_database(app.config['MOCK_MONGO'])


@pytest.fixture(scope='function')
def admin(db):
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
def user(db):
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
def another_user(db):
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
def doc(db, user):
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
def doc_list(db, admin):
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
def motor_collection(app, db, doc_list, event_loop):
    motor.metaprogramming._class_cache={}
    motor.core.AgnosticClient.__delegate_class__ = Mock(return_value=db)
    motor.core.AgnosticDatabase.__delegate_class__ = Mock(return_value=db.get_database().get_collection('doc_meta'))
    motor.motor_asyncio.AsyncIOMotorClient=motor.motor_asyncio.create_asyncio_class(motor.core.AgnosticClient)
    motor.motor_asyncio.AsyncIOMotorDatabase = motor.motor_asyncio.create_asyncio_class(motor.core.AgnosticDatabase)
    # patch('motor.motor_asyncio.AsyncIOMotorClient.__delegate_class__', return_value=db).start()
    # patch('motor.motor_asyncio.AsyncIOMotorDatabase.__delegate_class__',
    #       return_value=db.get_database().get_collection('doc_meta')).start()
    patch('motor.core.Database', return_value=db.get_database()).start()
    patch('motor.core.Collection', return_value=db.get_database().get_collection('document_meta')).start()

    client = motor.motor_asyncio.AsyncIOMotorClient(io_loop=event_loop)
    collection = client[app.config['MONGODB_DB']][DocumentMeta._meta[
        'collection']]
    yield collection
    client.close()
