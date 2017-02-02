import json
import uuid

from flask import url_for
from pytest_flask.fixtures import client


def test_app(app):
    """Test to make sure the app is loading properly."""

    assert app


def test_index(client):
    """Test that the index works."""

    assert client.get(url_for('index')).status_code == 200


def test_update(client):
    """Test that creating a new RRD works."""

    payload = {
        'metrics': {
            'COUNTER': {
                'a': 1,
                'b': 2,
            }
        },
    }

    rsp = client.post(
            url_for('update',
                rrd='test-{0}'.format(uuid.uuid4())),
            content_type='application/json',
            data=json.dumps(payload))

    assert rsp.status_code == 200


def test_dashboard(client):
    """Test that the dashboard works."""

    rsp = client.get(url_for('dashboard'))

    assert rsp.status_code == 200
