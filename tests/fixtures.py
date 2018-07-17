import pytest
from mongoengine import connect

from app import create_app
from app.models import User, Role, DocumentMeta, Category


@pytest.fixture(scope='module')
def app():
    app = create_app('testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    connection = connect()
    Role.insert_roles()
    yield connection
    connection.drop_database(app.config['MOCK_MONGO'])


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
        category=Category.REVIEWED.value,
        url='https://www.test.com',
        priority=1,
        create_by=user)
    dup_doc_meta = DocumentMeta(
        theme='duplicate',
        category=Category.REVIEWED.value,
        url='https://www.duplicate.com',
        priority=1,
        create_by=user)
    doc_meta.save()
    dup_doc_meta.save()
    yield doc_meta
    doc_meta.delete()
    dup_doc_meta.delete()
