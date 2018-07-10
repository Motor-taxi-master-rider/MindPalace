import pytest
from flask import url_for
from flask_login import current_user

import app.account.views
from app.models import User
from utils import login, redirect_to, real_url,  MockRedisQueue


@pytest.mark.usefixtures('app')
@pytest.mark.parametrize("endpoint, redirect", [
    ('account.manage', None),
    ('account.change_email_request', None),
    ('account.change_password', None),
    ('account.change_email_request', None),
    ('account.confirm_request', 'main.index'),
])
def test_direct_api_require_login(client, admin, monkeypatch, endpoint, redirect):
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert redirect_to(client.get(url_for(endpoint))
                       ) == real_url('account.login')
    login(client, admin)
    if redirect:
        assert redirect_to(client.get(url_for(endpoint))) == real_url(redirect)
    else:
        assert client.get(url_for(endpoint)).status_code == 200


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
    assert redirect_to(client.post(url_for('account.register'),
                                   data=data)) == real_url('main.index')
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
    assert redirect_to(client.get(url_for('account.logout'))
                       ) == real_url('main.index')
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app')
def test_get_reset_password_request_api(client, admin):
    assert redirect_to(client.get(
        url_for('account.reset_password_request'))) == real_url('main.index')
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

    assert redirect_to(client.post(url_for('account.reset_password_request'),
                                   data={'email': admin.email})) == real_url('account.login')
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

    assert redirect_to(client.post(url_for('account.reset_password_request'), data={
        'email': 'not@valid.com'})) == real_url('account.login')


@pytest.mark.usefixtures('app')
def test_post_reset_password_api_success(client, admin):
    data = {
        'email': admin.email,
        'new_password': '54321t',
        'new_password2': '54321t'
    }
    token = admin.generate_password_reset_token()

    assert redirect_to(client.post(
        url_for('account.reset_password', token=token), data=data)) == real_url('account.login')
    admin.reload()
    assert admin.verify_password(data['new_password'])


@pytest.mark.usefixtures('app')
def test_post_reset_password_api_failure(client, admin):
    data = {
        'email': admin.email,
        'new_password': '54321t',
        'new_password2': '54321t'
    }

    assert redirect_to(client.post(
        url_for('account.reset_password', token='notvalid'), data=data)) == real_url('main.index')
    admin.reload()
    assert not admin.verify_password(data['new_password'])


@pytest.mark.usefixtures('app')
def test_post_change_password_api_success(client, admin):
    login(client, admin)
    data = {
        'old_password': 'test',
        'new_password': 't12345',
        'new_password2': 't12345'
    }

    assert redirect_to(client.post(
        url_for('account.change_password'), data=data)) == real_url('main.index')
    admin.reload()
    assert admin.verify_password(data['new_password'])


@pytest.mark.usefixtures('app')
def test_post_change_password_api_failure(client, admin):
    login(client, admin)
    data = {
        'old_password': 'invalid',
        'new_password': 't12345',
        'new_password2': 't12345'
    }

    assert client.post(
        url_for('account.change_password'), data=data).status_code == 200
    admin.reload()
    assert not admin.verify_password(data['new_password'])
    assert admin.verify_password('test')


@pytest.mark.usefixtures('app')
def test_post_change_email_request_success(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_email_change_token', lambda s, e: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)
    data = {
        'email': 'new@admin.com',
        'password': 'test',
    }

    assert redirect_to(client.post(
        url_for('account.change_email_request'), data=data)) == real_url('main.index')
    admin.reload()
    queued_object = mock_queue.get(False)
    queued_object['recipient'] = data['email']
    queued_object['user'] = admin
    queued_object['change_email_link'] = url_for(
        'account.change_email', token='token', _external=True)


@pytest.mark.usefixtures('app')
def test_post_change_email_request_faliure(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_email_change_token', lambda s, e: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)
    duplicate_email = {
        'email': 'admin@admin.com',
        'password': 'test',
    }
    wrong_password = {
        'email': 'new@admin.com',
        'password': 'test1',
    }

    client.post(url_for('account.change_email_request'), data=duplicate_email)
    admin.reload()
    assert admin.email == 'admin@admin.com'

    client.post(url_for('account.change_email_request'), data=wrong_password)
    admin.reload()
    assert admin.email == 'admin@admin.com'
