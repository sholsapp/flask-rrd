#!/usr/bin/env python

import os

from setuptools import setup

README = None
with open(os.path.abspath('README.md')) as fh:
  README = fh.read()

setup(
  name='flask-rrd',
  version='0.0.1',
  description=README,
  author='Stephen Holsapple',
  author_email='sholsapp@gmail.com',
  url='http://www.flask.com',
  packages=['flaskrrd'],
  install_requires=[
    'Flask-Bootstrap',
    'Flask-Script',
    'Flask-SQLAlchemy',
    'Flask-Restless',
    'Flask',
    'configobj',
    'procfs',
    'requests',
    'rrdtool',
  ],
  test_requires=[
    'pytest',
    'pytest-flask',
  ],
)
