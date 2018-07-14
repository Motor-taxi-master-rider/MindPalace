import pytest
from flask import url_for
from mongoengine import DoesNotExist

import app.admin.views
from app.admin.forms import ChangeUserEmailForm, ChangeAccountTypeForm
from app.models import User, Role, EditableHTML
from utils import captured_templates, login, MockRedisQueue, redirect_to, real_url, INVALID_OBJECT_ID


def test_post_new_user(client, admin):
    login(client, admin)
    user_role = Role.objects(name='User').first()
    data = {
        'role': str(user_role.id),
        'first_name': 'test',
        'last_name': 'test',
        'email': 'test@test.com',
        'password': 't12345',
        'password2': 't12345'
    }

    assert client.post(url_for('admin.new_user'), data=data).status_code == 200
    new_user = User.objects(email='test@test.com').first()
    assert new_user is not None
    assert new_user.role == user_role
    assert new_user.verify_password(data['password'])


def test_post_invite_user(client, admin, monkeypatch):
    login(client, admin)
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(User, 'generate_confirmation_token', lambda s: 'token')
    monkeypatch.setattr(app.admin.views, 'get_queue', lambda: mock_queue)
    user_role = Role.objects(name='User').first()
    data = {
        'role': str(user_role.id),
        'first_name': 'test',
        'last_name': 'test',
        'email': 'test@test.com',
    }

    assert client.post(url_for('admin.invite_user'), data=data).status_code == 200
    new_user = User.objects(email='test@test.com').first()
    assert new_user is not None
    assert new_user.role == user_role

    queued_object = mock_queue.get(False)
    assert queued_object['recipient'] == data['email']
    assert queued_object['user'] == new_user
    assert queued_object['invite_link'] == url_for('account.join_from_invite',
                                                   user_id=new_user.id,
                                                   token='token',
                                                   _external=True)


def test_get_user_info(client, admin):
    login(client, admin)

    with captured_templates(client.application) as templates:
        assert client.get(url_for('admin.user_info', user_id=str(admin.id))).status_code == 200
        template, context = templates.pop()
        assert template.name == 'admin/manage_user.html'
        assert context['user'] == admin

    assert client.get(url_for('admin.user_info', user_id=INVALID_OBJECT_ID)).status_code == 404


def test_post_change_user_email(client, admin):
    login(client, admin)
    data = {'email': 'new@admin.com'}

    with captured_templates(client.application) as templates:
        assert client.post(url_for('admin.change_user_email', user_id=str(admin.id)), data=data).status_code == 200
        template, context = templates.pop()
        assert template.name == 'admin/manage_user.html'
        assert context['user'] == admin
        assert isinstance(context['form'], ChangeUserEmailForm)
        admin.reload()
        assert admin.email == data['email']

    assert client.post(url_for('admin.change_user_email', user_id=INVALID_OBJECT_ID)).status_code == 404


def test_post_change_account_type(client, admin, user):
    login(client, admin)
    admin_role = Role.objects(name='Administrator').first()
    data = {'role': str(admin_role.id)}

    with captured_templates(client.application) as templates:
        assert client.post(url_for('admin.change_account_type', user_id=str(user.id)), data=data).status_code == 200
        template, context = templates.pop()
        assert template.name == 'admin/manage_user.html'
        assert context['user'] == user
        assert isinstance(context['form'], ChangeAccountTypeForm)
        user.reload()
        assert user.role == admin_role

    assert redirect_to(client.post(url_for('admin.change_account_type', user_id=str(admin.id)), data=data)) == \
           real_url('admin.user_info', user_id=admin.id)

    assert client.post(url_for('admin.change_account_type', user_id=INVALID_OBJECT_ID), data=data).status_code == 404


def test_get_delete_user_request(client, admin):
    login(client, admin)

    with captured_templates(client.application) as templates:
        assert client.get(url_for('admin.delete_user_request', user_id=str(admin.id))).status_code == 200
        template, context = templates.pop()
        assert template.name == 'admin/manage_user.html'
        assert context['user'] == admin

    assert client.get(url_for('admin.delete_user_request', user_id=INVALID_OBJECT_ID)).status_code == 404


def test_get_delete_user(client, admin, user):
    login(client, admin)

    assert redirect_to(client.get(url_for('admin.delete_user', user_id=str(user.id)))) == \
           real_url('admin.registered_users')
    with pytest.raises(DoesNotExist):
        User.objects.get(id=user.id)

    assert redirect_to(client.get(url_for('admin.delete_user', user_id=str(admin.id)))) == \
           real_url('admin.registered_users')
    assert User.objects.get(id=admin.id) == admin


def test_get_update_editor_contents(client, admin):
    login(client, admin)
    data = {
        'edit_data': 'test',
        'editor_name': 'admin'
    }

    client.post(url_for('admin.update_editor_contents'), data=data)
    editor_contents = EditableHTML.objects(editor_name='admin').first()
    assert editor_contents.value == 'test'
