import os

import pytest

from app import create_app
from tests.fixtures import test_app


@pytest.fixture
def app():
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    return app
