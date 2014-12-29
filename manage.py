#!/usr/bin/env python

import json
import requests

from configobj import ConfigObj
from validate import Validator
from flask.ext.script import Manager
import rrdtool

from flaskrrd import app, init_webapp
from flaskrrd.model import db, RRD


manager = Manager(app)


@manager.command
def update_database():
  import random
  import time
  while True:
    print '.'
    m1 = random.randint(0, 100)
    m2 = random.randint(0, 100)
    m3 = random.randint(0, 100)
    ret = rrdtool.update('test.rrd', 'N:%s:%s:%s' % (m1, m2, m3))
    time.sleep(1)


@manager.command
def graph_rrd():
  print requests.get(
    'http://localhost:5000/graph/test').status_code

@manager.command
def create_rrd():
  print requests.post(
    'http://localhost:5000/create/test',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'metrics': ['metric1', 'metric2', 'metric3'], 'type': 'GAUGE'})).status_code


@manager.command
def dump_database():
  init_webapp()
  for r in RRD.query.all():
    print r


@manager.command
def runserver(*args, **kwargs):
  """Override default `runserver` to init webapp before running."""
  app = init_webapp()
  # TODO(sholsapp): parameterize this, but don't clobber the *args, **kwargs
  # space, because it's annoying to have to pass these in to the `run` method.
  config = ConfigObj('config/sample.config', configspec='config/sample.configspec')
  app.config_obj = config
  app.run(*args, **kwargs)


if __name__ == "__main__":
  manager.run()
