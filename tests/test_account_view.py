import pytest
from flask import url_for
from flask_login import current_user

import app.account.views
from app.models import User
from utils import login, is_redirect_to_login, MockRedisQueue


@pytest.mark.usefixtures('app')
def test_login_api_success(client, admin):
    assert client.get(url_for('account.login')).status_code == 200
    assert current_user.is_anonymous
    login(client, admin)
    assert not current_user.is_anonymous
    assert current_user == admin


@pytest.mark.usefixtures('app')
def test_login_api_failure(client, admin):
    assert client.post(url_for('account.login'), data=dict(
        email=admin.email,
        password='not valid'
    )).status_code == 200
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app')
def test_logout_api(client, admin):
    login(client, admin)
    assert current_user == admin
    assert is_redirect_to_login(client.get(url_for('account.logout')))
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app')
def test_manage_api(client, admin):
    assert is_redirect_to_login(client.get(url_for('account.manage')))
    login(client, admin)
    assert client.get(url_for('account.manage')).status_code == 200


@pytest.mark.usefixtures('app')
def test_get_reset_password_request_api(client, admin):
    assert is_redirect_to_login(client.get(url_for('account.reset_password_request')))
    login(client, admin)
    assert client.get(url_for('account.reset_password_request')).status_code == 200


@pytest.mark.usefixtures('app')
def test_post_reset_password_request_api_success(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(User, 'generate_password_reset_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert client.post(url_for('account.reset_password_request'), data={'email': admin.email}).status_code == 302
    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == admin.email
    assert queued_object['user'] == admin
    assert queued_object['reset_link'] == url_for('account.reset_password', token='token', _external=True)


@pytest.mark.usefixtures('app')
def test_post_reset_password_request_api_failure(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(User, 'generate_password_reset_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert is_redirect_to_login(client.post(url_for('account.reset_password_request'), data={'email': 'not@valid.com'}))
