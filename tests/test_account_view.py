import pytest
from flask import url_for
from flask_login import current_user

import app.account.views
from app.models import User
from utils import login, is_redirect_to, MockRedisQueue


@pytest.mark.usefixtures('app')
def test_login_api_success(client, admin):
    assert client.get(url_for('account.login')).status_code == 200
    assert current_user.is_anonymous
    login(client, admin)
    assert not current_user.is_anonymous
    assert current_user == admin


@pytest.mark.usefixtures('app')
def test_login_api_failure(client, admin):
    assert client.post(url_for('account.login'), data={
        'email': admin.email,
        'password': 'not valid'
    }).status_code == 200
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app', 'db')
def test_register_api(client, db, monkeypatch):
    assert client.get(url_for('account.register')).status_code == 200

    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_confirmation_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    data = {
        'first_name': 'first',
        'last_name': 'last',
        'email': 'test@test.com',
        'password': 't12345',
        'password2': 't12345',
    }
    assert is_redirect_to(client.post(url_for('account.register'),
                                      data=data), 'main.index')
    user = User.objects(email=data['email']).first()
    assert user.first_name == data['first_name']
    assert user.last_name == data['last_name']
    assert user.verify_password(data['password'])

    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == data['email']
    assert queued_object['user'] == user
    assert queued_object['confirm_link'] == url_for(
        'account.confirm', token='token', _external=True)


@pytest.mark.usefixtures('app')
def test_logout_api(client, admin):
    login(client, admin)
    assert current_user == admin
    assert is_redirect_to(client.get(url_for('account.logout')), 'main.index')
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app')
def test_manage_api(client, admin):
    assert is_redirect_to(client.get(
        url_for('account.manage')), 'account.login')
    login(client, admin)
    assert client.get(url_for('account.manage')).status_code == 200


@pytest.mark.usefixtures('app')
def test_get_reset_password_request_api(client, admin):
    assert is_redirect_to(client.get(
        url_for('account.reset_password_request')), 'main.index')
    login(client, admin)
    assert client.get(
        url_for('account.reset_password_request')).status_code == 200


@pytest.mark.usefixtures('app')
def test_post_reset_password_request_api_success(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_password_reset_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert is_redirect_to(client.post(url_for('account.reset_password_request'),
                                      data={'email': admin.email}), 'account.login')
    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == admin.email
    assert queued_object['user'] == admin
    assert queued_object['reset_link'] == url_for(
        'account.reset_password', token='token', _external=True)


@pytest.mark.usefixtures('app')
def test_post_reset_password_request_api_failure(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_password_reset_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert is_redirect_to(client.post(url_for('account.reset_password_request'), data={
        'email': 'not@valid.com'}), 'account.login')


@pytest.mark.usefixtures('app')
def test_post_reset_password_api_success(client, admin):
    data = {
        'email': admin.email,
        'new_password': '54321t',
        'new_password2': '54321t'
    }
    token = admin.generate_password_reset_token()
    assert is_redirect_to(client.post(
        url_for('account.reset_password', token=token), data=data), 'account.login')
    admin.reload()
    assert admin.verify_password(data['new_password'])


@pytest.mark.usefixtures('app')
def test_post_reset_password_api_failure(client, admin):
    data = {
        'email': admin.email,
        'new_password': '54321t',
        'new_password2': '54321t'
    }
    assert is_redirect_to(client.post(
        url_for('account.reset_password', token='notvalid'), data=data), 'main.index')

    admin.reload()
    assert not admin.verify_password(data['new_password'])
