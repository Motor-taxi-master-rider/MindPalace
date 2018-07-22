from contextlib import contextmanager
from queue import Queue
from urllib.parse import urlparse, urlunparse

from flask import Response, template_rendered, url_for
from flask.testing import FlaskClient

from app.models import User


@contextmanager
def captured_templates(app):
    """Context manger to capture all rendered templates into a list."""

    def record(sender, template, context, **extra):
        nonlocal recorded
        recorded.append((template, context))

    recorded = []
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def login(client: FlaskClient, user: User, password: str = 'test') -> Response:
    """Login a user."""
    return client.post(
        url_for('account.login'),
        data={
            'email': user.email,
            'password': password
        })


def logout(client: FlaskClient) -> Response:
    """Log out current user."""
    return client.get(url_for('account.logout'))


def redirect_to(response: Response) -> str:
    """ Remove argument and query of the response url. """
    url_parse = urlparse(response.headers.get('location'))
    return urlunparse((url_parse.scheme, url_parse.netloc, url_parse.path, '',
                       '', ''))


def real_url(route: str, **arguments) -> str:
    """Return full url of given endpoint."""
    return url_for(route, **arguments, _external=True)


class MockRedisQueue(Queue):
    def enqueue(self, _, **kwargs):
        return self.put(kwargs)
