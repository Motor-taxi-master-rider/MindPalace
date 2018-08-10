import datetime
import time

import pytest
from flask import url_for
from utils import login

from app.models import AnonymousUser, Permission, Role, User


@pytest.mark.usefixtures('app')
def test_password_setter():
    u = User(password='password')
    assert u.password is not None


@pytest.mark.usefixtures('app')
def test_password_verification():
    u = User(password='password')
    assert u.verify_password('password')
    assert not u.verify_password('notpassword')


@pytest.mark.usefixtures('app')
def test_password_salts_are_random():
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    assert u1.password != u2.password


@pytest.mark.usefixtures('mongo_client')
def test_valid_confirmation_token():
    u = User(password='password')
    u.save()
    token = u.generate_confirmation_token()
    assert u.confirm_account(token)


@pytest.mark.usefixtures('mongo_client')
def test_invalid_confirmation_token():
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_confirmation_token()
    assert not u2.confirm_account(token)


@pytest.mark.usefixtures('mongo_client')
def test_expired_confirmation_token():
    u = User(password='password')
    u.save()
    token = u.generate_confirmation_token(1)
    time.sleep(2)
    assert not u.confirm_account(token)


@pytest.mark.usefixtures('mongo_client')
def test_valid_reset_token():
    u = User(password='password')
    u.save()
    token = u.generate_password_reset_token()
    assert u.reset_password(token, 'notpassword')
    assert u.verify_password('notpassword')


@pytest.mark.usefixtures('mongo_client')
def test_invalid_reset_token():
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_password_reset_token()
    assert not u2.reset_password(token, 'notnotpassword')
    assert u2.verify_password('notpassword')


@pytest.mark.usefixtures('mongo_client')
def test_valid_email_change_token():
    u = User(email='user@example.com', password='password')
    u.save()
    token = u.generate_email_change_token('otheruser@example.org')
    assert u.change_email(token)
    assert u.email == 'otheruser@example.org'


@pytest.mark.usefixtures('mongo_client')
def test_invalid_email_change_token():
    u1 = User(email='user@example.com', password='password')
    u2 = User(email='otheruser@example.org', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_email_change_token('otherotheruser@example.net')
    assert not u2.change_email(token)
    assert u2.email == 'otheruser@example.org'


@pytest.mark.usefixtures('mongo_client')
def test_duplicate_email_change_token():
    u1 = User(email='user@example.com', password='password')
    u2 = User(email='otheruser@example.org', password='notpassword')
    u1.save()
    u2.save()
    token = u2.generate_email_change_token('user@example.com')
    assert not u2.change_email(token)
    assert u2.email == 'otheruser@example.org'


@pytest.mark.usefixtures('mongo_client')
def test_roles_and_permissions():
    Role.insert_roles()
    u = User(email='user@example.com', password='password')
    assert u.can(Permission.GENERAL.value)
    assert not u.can(Permission.ADMINISTER.value)


@pytest.mark.usefixtures('mongo_client')
def test_make_administrator():
    Role.insert_roles()
    u = User(email='user@example.com', password='password')
    assert not u.can(Permission.ADMINISTER.value)
    u.role = Role.objects(permissions=Permission.ADMINISTER.value).first()
    assert u.can(Permission.ADMINISTER.value)


@pytest.mark.usefixtures('mongo_client')
def test_administrator():
    Role.insert_roles()
    r = Role.objects(permissions=Permission.ADMINISTER.value).first()
    u = User(email='user@example.com', password='password', role=r)
    assert u.can(Permission.ADMINISTER.value)
    assert u.can(Permission.GENERAL.value)
    assert u.is_admin()


@pytest.mark.usefixtures('app')
def test_anonymous():
    u = AnonymousUser()
    assert not u.can(Permission.GENERAL.value)


def test_last_seen(client, user):
    user.last_seen = datetime.datetime.utcfromtimestamp(1000000000)
    user.save()
    assert user.last_seen.timestamp() != pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)

    login(client, user)
    client.get(url_for('main.index'))
    user.reload()
    assert user.last_seen.timestamp() == pytest.approx(
        datetime.datetime.utcnow().timestamp(), abs=2)
