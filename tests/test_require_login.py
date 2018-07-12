import pytest
from utils import login, redirect_to, real_url,  MockRedisQueue

import app.account.views
from flask import url_for


@pytest.mark.parametrize("endpoint, arguments", [
    ('account.manage', {}),
    ('account.change_email_request', {}),
    ('account.change_password', {}),
    ('account.change_email_request', {}),
    ('account.change_email', {'token': 'token'}),
    ('account.confirm_request', {}),
    ('account.confirm', {'token': 'token'}),
    ('admin.index', {}),
    ('admin.new_user', {}),
    ('admin.invite_user', {}),
    ('admin.registered_users', {}),
    ('admin.user_info', {'user_id': 'id'}),
    ('admin.change_user_email', {'user_id': 'id'}),
    ('admin.change_account_type', {'user_id': 'id'}),
    ('admin.delete_user_request', {'user_id': 'id'}),
    ('admin.delete_user', {'user_id': 'id'}),
])
def test_api_require_login(client, admin, endpoint, arguments):
    assert redirect_to(client.get(url_for(endpoint, **arguments))
                       ) == real_url('account.login')


@pytest.mark.parametrize("endpoint, arguments", [
    ('admin.index', {}),
    ('admin.new_user', {}),
    ('admin.invite_user', {}),
    ('admin.registered_users', {}),
    ('admin.user_info', {'user_id': 'id'}),
    ('admin.change_user_email', {'user_id': 'id'}),
    ('admin.change_account_type', {'user_id': 'id'}),
    ('admin.delete_user_request', {'user_id': 'id'}),
    ('admin.delete_user', {'user_id': 'id'}),
])
def test_normal_user_can_not_access(client, user, endpoint, arguments):
    login(client, user)
    assert client.get(url_for(endpoint, **arguments)).status_code == 403
