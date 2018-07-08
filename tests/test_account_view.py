import pytest
from flask import url_for, session
from flask_login import current_user

from utils import login


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
    assert client.get(url_for('account.logout')).status_code == 302
    assert current_user.is_anonymous


@pytest.mark.usefixtures('app')
def test_manage_api(client, admin):
    assert client.get(url_for('account.manage')).status_code == 302
    login(client, admin)
    assert client.get(url_for('account.manage')).status_code == 200


@pytest.mark.usefixtures('app')
def test_get_reset_password_request_api(client, admin):
    assert client.get(url_for('account.reset_password_request')).status_code == 302
    login(client, admin)
    assert client.get(url_for('account.reset_password_request')).status_code == 200

@pytest.mark.usefixtures('app')
def test_post_reset_password_request_api_success(client, admin):
    login(client, admin)
    assert client.get(url_for('account.reset_password_request')).status_code == 200