import pytest

from app import create_app
from mongoengine import connect


@pytest.fixture(scope='module')
def app():
    app = create_app('testing')
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def db(app):
    connection = connect()
    yield connection
    connection.drop_database(app.config['MOCK_MONGO'])
