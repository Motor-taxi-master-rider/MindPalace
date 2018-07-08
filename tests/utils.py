from flask import url_for


def login(client, user, password='test'):
    return client.post(url_for('account.login'), data=dict(
        email=user.email,
        password=password
    ))


def logout(client):
    return client.get(url_for('account.logout'))
