from queue import Queue

from flask import url_for, Response
from flask.testing import FlaskClient
from app.models import User
from urllib.parse import urlparse, urlunparse


def login(client: FlaskClient, user: User, password: str = 'test') -> Response:
    return client.post(url_for('account.login'), data={
        'email': user.email,
        'password': password
    })


def logout(client: FlaskClient) -> Response:
    return client.get(url_for('account.logout'))


def redirect_to(response: Response) -> str:
    url = response.headers.get('location')
    return urlunparse(urlparse(url)[:3] + ('',) * 3)


def real_url(route: str) -> str:
    return url_for(route, _external=True)


class MockRedisQueue(Queue):
    def enqueue(self, _, **kwargs):
        return self.put(kwargs)
