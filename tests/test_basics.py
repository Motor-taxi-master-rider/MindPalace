from flask import current_app


def test_app_exists(test_app):
    assert not (current_app is None)


def test_app_is_testing(test_app):
    assert current_app.config['TESTING']
