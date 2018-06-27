import pytest

from app import create_app, db
from mongoengine import connect


@pytest.fixture(scope='function')
def test_app():
    db.connect('mongoenginetest',
               host='mongomock://localhost', alias='testdb')
    app = create_app('testing')
    app_context = app.app_context()
    app_context.push()
    yield app
    db.connection.drop_database('test')
    app_context.pop()
