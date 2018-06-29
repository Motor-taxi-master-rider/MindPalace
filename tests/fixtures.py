import pytest

from app import create_app
from mongoengine import connect


@pytest.fixture(scope='function')
def test_app():
    app = create_app('testing')
    connection = connect()
    app_context = app.app_context()
    app_context.push()
    yield app
    connection.drop_database('mongomock')
    app_context.pop()
