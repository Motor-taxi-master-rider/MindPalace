import pytest
from flask import current_app


@pytest.mark.usefixtures('app')
def test_app_exists():
    assert not (current_app is None)


@pytest.mark.usefixtures('app')
def test_app_is_testing():
    assert current_app.config['TESTING']
