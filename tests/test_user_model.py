import time

from app.models import AnonymousUser, Permission, Role, User


def test_password_setter(test_app):
    u = User(password='password')
    assert u.password is not None


def test_password_verification(test_app):
    u = User(password='password')
    assert u.verify_password('password')
    assert not u.verify_password('notpassword')


def test_password_salts_are_random(test_app):
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    assert u1.password != u2.password


def test_valid_confirmation_token(test_app):
    u = User(password='password')
    u.save()
    token = u.generate_confirmation_token()
    assert u.confirm_account(token)


def test_invalid_confirmation_token(test_app):
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_confirmation_token()
    assert not u2.confirm_account(token)


def test_expired_confirmation_token(test_app):
    u = User(password='password')
    u.save()
    token = u.generate_confirmation_token(1)
    time.sleep(2)
    assert not u.confirm_account(token)


def test_valid_reset_token(test_app):
    u = User(password='password')
    u.save()
    token = u.generate_password_reset_token()
    assert u.reset_password(token, 'notpassword')
    assert u.verify_password('notpassword')


def test_invalid_reset_token(test_app):
    u1 = User(email='user1@example.com', password='password')
    u2 = User(email='user2@example.com', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_password_reset_token()
    assert not u2.reset_password(token, 'notnotpassword')
    assert u2.verify_password('notpassword')


def test_valid_email_change_token(test_app):
    u = User(email='user@example.com', password='password')
    u.save()
    token = u.generate_email_change_token('otheruser@example.org')
    assert u.change_email(token)
    assert u.email == 'otheruser@example.org'


def test_invalid_email_change_token(test_app):
    u1 = User(email='user@example.com', password='password')
    u2 = User(email='otheruser@example.org', password='notpassword')
    u1.save()
    u2.save()
    token = u1.generate_email_change_token('otherotheruser@example.net')
    assert not u2.change_email(token)
    assert u2.email == 'otheruser@example.org'


def test_duplicate_email_change_token(test_app):
    u1 = User(email='user@example.com', password='password')
    u2 = User(email='otheruser@example.org', password='notpassword')
    u1.save()
    u2.save()
    token = u2.generate_email_change_token('user@example.com')
    assert not u2.change_email(token)
    assert u2.email == 'otheruser@example.org'


def test_roles_and_permissions(test_app):
    Role.insert_roles()
    u = User(email='user@example.com', password='password')
    assert u.can(Permission.GENERAL.value)
    assert not u.can(Permission.ADMINISTER.value)


def test_make_administrator(test_app):
    Role.insert_roles()
    u = User(email='user@example.com', password='password')
    assert not u.can(Permission.ADMINISTER.value)
    u.role = Role.objects(
        permissions=Permission.ADMINISTER.value).first()
    assert u.can(Permission.ADMINISTER.value)


def test_administrator(test_app):
    Role.insert_roles()
    r = Role.objects(permissions=Permission.ADMINISTER.value).first()
    u = User(email='user@example.com', password='password', role=r)
    assert u.can(Permission.ADMINISTER.value)
    assert u.can(Permission.GENERAL.value)
    assert u.is_admin()


def test_anonymous(test_app):
    u = AnonymousUser()
    assert not u.can(Permission.GENERAL.value)
