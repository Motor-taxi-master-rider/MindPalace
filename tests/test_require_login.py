import pytest
from utils import login, redirect_to, real_url,  MockRedisQueue

import app.account.views
from flask import url_for


@pytest.mark.parametrize("endpoint, redirect", [
    ('account.manage', None),
    ('account.change_email_request', None),
    ('account.change_password', None),
    ('account.change_email_request', None),
    ('account.confirm_request', 'main.index'),
])
def test_direct_api_require_login(client, admin, monkeypatch, endpoint, redirect):
    mock_queue = MockRedisQueue()
    monkeypatch.setattr(app.account.views, 'get_queue', lambda: mock_queue)

    assert redirect_to(client.get(url_for(endpoint))
                       ) == real_url('account.login')
    login(client, admin)
    if redirect:
        assert redirect_to(client.get(url_for(endpoint))) == real_url(redirect)
    else:
        assert client.get(url_for(endpoint)).status_code == 200
