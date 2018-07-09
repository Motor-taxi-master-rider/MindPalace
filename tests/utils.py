from queue import Queue

from flask import url_for


def login(client, user, password='test'):
    return client.post(url_for('account.login'), data={
        'email': user.email,
        'password': password
    })


def logout(client):
    return client.get(url_for('account.logout'))


def is_redirect_to(response, route):
    return response.headers.get('location') == url_for(route, _external=True)


class MockRedisQueue(Queue):
    def enqueue(self, _, **kwargs):
        return self.put(kwargs)
