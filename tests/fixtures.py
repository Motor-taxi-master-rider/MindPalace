import pytest
from mongoengine import connect

from app import create_app
from app.models import User, Role


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
