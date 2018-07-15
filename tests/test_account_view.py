import pytest
from flask import url_for
from flask_login import current_user

import app.account.views
from app.account.forms import LoginForm, ChangePasswordForm
from app.models import User
from utils import captured_templates, login, logout, redirect_to, real_url, MockRedisQueue, INVALID_OBJECT_ID


def test_login_success(client, admin):
    with captured_templates(client.application) as templates:
        assert client.get(url_for('account.login')).status_code == 200
        template, context = templates.pop()
        assert template.name == 'account/login.html'
        assert isinstance(context['form'], LoginForm)
    assert current_user.is_anonymous
    login(client, admin)
    assert not current_user.is_anonymous
    assert current_user == admin


def test_login_failure(client, admin):
    assert client.post(url_for('account.login'), data={
        'email': admin.email,
        'password': 'not valid'
    }).status_code == 200
    assert current_user.is_anonymous


def test_login_with_valid_next_endpoint(client, admin):
    assert redirect_to(client.post(url_for('account.login', next='/task/doc_meta/my_documents'), data={
        'email': admin.email,
        'password': 'test'
    })) == real_url('task.my_doc_meta')


@pytest.mark.usefixtures('db')
def test_register(client, monkeypatch):
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


def test_logout(client, admin):
    login(client, admin)
    assert current_user == admin
    assert redirect_to(client.get(url_for('account.logout'))
                       ) == real_url('main.index')
    assert current_user.is_anonymous


def test_post_reset_password_request_success(client, admin, monkeypatch):
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


def test_post_reset_password_request_failure(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_password_reset_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert redirect_to(client.post(url_for('account.reset_password_request'), data={
        'email': 'not@valid.com'})) == real_url('account.login')


def test_post_reset_password_success(client, admin):
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


def test_post_reset_password_failure(client, admin):
    data = {
        'email': admin.email,
        'new_password': '54321t',
        'new_password2': '54321t'
    }

    assert redirect_to(client.post(
        url_for('account.reset_password', token='notvalid'), data=data)) == real_url('main.index')
    admin.reload()
    assert not admin.verify_password(data['new_password'])


def test_post_change_password_success(client, admin):
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


def test_post_change_password_failure(client, admin):
    login(client, admin)
    data = {
        'old_password': 'invalid',
        'new_password': 't12345',
        'new_password2': 't12345'
    }

    with captured_templates(client.application) as templates:
        assert client.post(
            url_for('account.change_password'), data=data).status_code == 200
        template, context = templates.pop()
        assert template.name == 'account/manage.html'
        assert isinstance(context['form'], ChangePasswordForm)
    admin.reload()
    assert not admin.verify_password(data['new_password'])
    assert admin.verify_password('test')


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
    assert queued_object['recipient'] == data['email']
    assert queued_object['user'] == admin
    assert queued_object['change_email_link'] == url_for(
        'account.change_email', token='token', _external=True)


def test_post_change_email_request_failure(client, admin, monkeypatch):
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


def test_get_change_email_success(client, admin):
    login(client, admin)
    token = admin.generate_email_change_token('new@admin.com')

    assert redirect_to(client.get(url_for('account.change_email',
                                          token=token))) == real_url('main.index')
    admin.reload()
    assert admin.email == 'new@admin.com'


def test_get_change_email_failure(client, admin):
    login(client, admin)
    admin.generate_email_change_token('another_new@admin.com')

    assert redirect_to(client.get(url_for('account.change_email',
                                          token='notvalid'))) == real_url('main.index')
    admin.reload()
    assert admin.email == 'admin@admin.com'


def test_get_confirm_request(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(
        User, 'generate_confirmation_token', lambda s: 'token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert redirect_to(client.get(
        url_for('account.confirm_request'))) == real_url('main.index')
    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == admin.email
    assert queued_object['user'] == admin
    assert queued_object['confirm_link'] == url_for(
        'account.confirm', token='token', _external=True)


def test_get_confirm_success(client, admin):
    login(client, admin)
    admin.confirmed = False
    admin.save()
    token = admin.generate_confirmation_token()

    assert redirect_to(client.get(
        url_for('account.confirm', token=token))) == real_url('main.index')
    admin.reload()
    assert admin.confirmed


def test_get_confirm_failure(client, admin):
    login(client, admin)
    admin.confirmed = False
    admin.save()
    admin.generate_confirmation_token()

    assert redirect_to(client.get(
        url_for('account.confirm', token='invalid'))) == real_url('main.index')
    admin.reload()
    assert not admin.confirmed


@pytest.mark.usefixtures('db')
def test_post_join_from_invite_success(client):
    new_user = User(email='user@user.com')
    new_user.save()
    token = new_user.generate_confirmation_token()
    data = {
        'password': 't12345',
        'password2': 't12345'
    }

    assert redirect_to(client.post(url_for('account.join_from_invite',
                                           user_id=str(new_user.id), token=token), data=data)) == real_url(
        'account.login')
    new_user.reload()
    assert new_user.verify_password('t12345')


@pytest.mark.usefixtures('db')
def test_post_join_from_invite_failure(client, admin, monkeypatch):
    new_user = User(email='user@user.com')
    new_user.save()
    token = new_user.generate_confirmation_token()

    login(client, admin)
    assert redirect_to(client.post(url_for('account.join_from_invite',
                                           user_id=str(new_user.id), token=token))) == real_url('main.index')

    logout(client)
    assert client.post(url_for('account.join_from_invite',
                               user_id=INVALID_OBJECT_ID, token=token)).status_code == 404

    assert redirect_to(client.post(url_for('account.join_from_invite',
                                           user_id=str(admin.id), token=token))) == real_url('main.index')

    mock_queue = MockRedisQueue()
    monkeypatch.setattr(User, 'generate_confirmation_token',
                        lambda s: 'new_token')
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)
    assert redirect_to(client.post(url_for('account.join_from_invite',
                                           user_id=str(new_user.id), token='invalid'))) == real_url('main.index')
    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == new_user.email
    assert queued_object['user'] == new_user
    assert queued_object['invite_link'] == url_for(
        'account.join_from_invite', user_id=str(new_user.id), token='new_token', _external=True)


def test_get_unconfirmed(client, admin):
    login(client, admin)
    admin.confirmed = False
    admin.save()

    with captured_templates(client.application) as templates:
        assert client.get(url_for('account.unconfirmed')).status_code == 200
        template, context = templates.pop()
        assert template.name == 'account/unconfirmed.html'

    admin.confirmed = True
    admin.save()
    assert redirect_to(client.get(
        url_for('account.unconfirmed'))) == real_url('main.index')
