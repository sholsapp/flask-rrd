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
        url_for('update', rrd='test-{0}'.format(uuid.uuid4())),
        content_type='application/json',
        data=json.dumps(payload),
    )

    assert rsp.status_code == 200


def test_evil_create(client):
    """Test that a malicious path cannot be used as RRD name."""

    payload = {
        'metrics': {
            'COUNTER': {
                'a': 1,
                'b': 2,
            }
        },
    }

    rsp = client.post(
        url_for('update', rrd='../evil-{0}'.format(uuid.uuid4())),
        content_type='application/json',
        data=json.dumps(payload),
    )
    assert rsp.status_code == 404


def test_info(client):

    payload = {
        'metrics': {
            'COUNTER': {
                'a': 1,
                'b': 2,
            }
        },
    }

    rrd_name = 'test-{0}'.format(uuid.uuid4())

    rsp = client.post(
        url_for('update', rrd=rrd_name),
        content_type='application/json',
        data=json.dumps(payload),
    )

    assert rsp.status_code == 200

    rsp = client.get(url_for('info', rrd=rrd_name))

    # Yuck, this key is from rrdinfo tool.
    assert rsp.json['ds[b].type'] == 'COUNTER'
    assert rrd_name in rsp.json['filename']


def test_dashboard(client):
    """Test that the dashboard works."""

    rsp = client.get(url_for('dashboard'))
    assert rsp.status_code == 200
