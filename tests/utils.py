from queue import Queue
from urllib.parse import urlparse, urlunparse

from flask import url_for, Response
from flask.testing import FlaskClient

from app.models import User


def login(client: FlaskClient, user: User, password: str = 'test') -> Response:
    return client.post(url_for('account.login'), data={
        'email': user.email,
        'password': password
    })


def logout(client: FlaskClient) -> Response:
    return client.get(url_for('account.logout'))


def redirect_to(response: Response) -> str:
    """ Remove argument and query of the response url. """
    url_parse = urlparse(response.headers.get('location'))
    return urlunparse((url_parse.scheme, url_parse.netloc, url_parse.path, '', '', ''))


def real_url(route: str) -> str:
    return url_for(route, _external=True)


class MockRedisQueue(Queue):
    def enqueue(self, _, **kwargs):
        return self.put(kwargs)
