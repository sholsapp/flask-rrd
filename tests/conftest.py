import pytest
from flask import Flask

from flaskrrd import init_webapp


@pytest.fixture(scope='module')
def app(request):
    app = Flask(__name__)
    app = init_webapp()
    app.config['SERVER_NAME'] = 'localhost'
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app
