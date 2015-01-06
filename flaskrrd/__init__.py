import logging
import os
import re

from flask import Flask, Response, render_template, jsonify, request, url_for
from flask.ext.bootstrap import Bootstrap
from flask.ext.restless import APIManager
import rrdtool

from flaskrrd.api import api
from flaskrrd.model import make_conn_str, db, RRD


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(RRD, methods=['GET', 'POST'])
Bootstrap(app)


class ColorWheel(object):

  i = 0

  CRAFTSMAN = [
    '#d7c797', # (215,199,151)
    '#845422', # (132,84,34)
    '#ead61c', # (234,214,28)
    '#a47c48', # (164,124,72)
    '#000000', # (0,0,0)
  ]

  GRYFFINDOR = [
    '#740001', # (116,0,1)
    '#ae0001', # (174,0,1)
    '#eeba30', # (238,186,48)
    '#d3a625', # (211,166,37)
    '#000000', # (0,0,0)
  ]

  WHEEL = list(GRYFFINDOR)


  @classmethod
  def hex_to_rgb(cls, value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

  @classmethod
  def rgb_to_hex(cls, rgb):
    return '#%02x%02x%02x' % rgb

  def next(self):
    color = self.WHEEL[self.i % len(self.WHEEL)]
    self.i += 1
    return color


def init_webapp():
  """Initialize the web application."""
  app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
  db.app = app
  db.init_app(app)
  db.create_all()
  rrd_dir = os.path.join(app.static_folder, 'rrds')
  if not os.path.exists(rrd_dir):
    os.makedirs(rrd_dir)
  return app


@app.route('/')
def index():
  return 'GOOD'


def sanitized_ds(ds):
  """Remove illegal characters from a data source name."""
  return re.sub('[^A-Za-z0-9_]+', '', ds)


def get_rrd_path(rrd):
  rrd_dir = os.path.join(app.static_folder, 'rrds')
  return os.path.join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))


def create_rrd(rrd, description):
  """Create an RRD.

  :param description: A :class:`dict` that describes the new RRD.

  """
  rrd_path = get_rrd_path(rrd)
  metrics_names = []
  metrics = []
  for ds_type in description['metrics']:
    for ds in description['metrics'][ds_type]:
      metrics_names.append(ds)
      metrics.append(
        'DS:{name}:{type}:2000:U:U'.format(name=sanitized_ds(ds), type=ds_type)
      )
  rrdtool.create(
    rrd_path,
    '--step', '60',
    '--start', '0',
    metrics,
    # See http://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html#___top for more
    # about RRA.
    # RRA:AVERAGE | MIN | MAX | LAST:xff:steps:rows
    'RRA:MIN:0:360:2400',
    'RRA:MIN:0:30:2400',
    'RRA:MIN:0:7:2400',
    'RRA:AVERAGE:0:360:2400',
    'RRA:AVERAGE:0:30:2400',
    'RRA:AVERAGE:0:7:2400',
    'RRA:AVERAGE:0:1:2400',
    'RRA:MAX:0:360:2400',
    'RRA:MAX:0:30:2400',
    'RRA:MAX:0:7:2400',)
  new_rrd = RRD(rrd, metrics_names, rrd_path)
  db.session.add(new_rrd)
  db.session.commit()
  return True


@app.route('/info/<rrd>', methods=['GET'])
def info(rrd):
  return jsonify(rrdtool.info(get_rrd_path(rrd)))


@app.route('/update/<rrd>', methods=['POST'])
def update(rrd):
  """Update or create a RRD database."""
  desc = request.json
  rrd_entry = RRD.query.filter_by(name=rrd).first()
  if not rrd_entry:
    if create_rrd(rrd, desc):
      log.info('Creating new rrd [%s] on update.', rrd)
    else:
      log.error('Could not create new rrd [%s] on update.', rrd)
      return Response(status=405)
  rrd_entry = RRD.query.filter_by(name=rrd).first()
  data = []
  for ds_type in desc['metrics']:
    for ds in desc['metrics'][ds_type]:
      data.append(str(desc['metrics'][ds_type][ds]))
  rrdtool.update(str(rrd_entry.path), 'N:{data}'.format(data=':'.join(data)))
  return Response(status=200)


@app.route('/graph/<rrd>')
def graph(rrd):
  """Graph an entire RRD database.

  This functionality is a generic default that graphs all metrics contained in
  an RRD database. For customized views on an RRD database, use <fill this in
  later>.

  """

  rrd_dir = os.path.join(app.static_folder, 'rrds')
  if not os.path.exists(rrd_dir):
    os.makedirs(rrd_dir)

  rrd_path = os.path.join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))
  if not os.path.exists(rrd_path):
    log.error('The rrd [%s] does not exist!', rrd)
    return Response(status=500)

  png_path = os.path.join(rrd_dir, '{rrd}-day.png'.format(rrd=rrd))

  rrd_entry = RRD.query.filter_by(name=rrd).first()
  if not rrd_entry:
    log.error('No existing entry for rrd [%s].', rrd)
    return Response(405)

  color_wheel = ColorWheel()

  acc = []
  for metric in rrd_entry.cols_desc.split(','):
    metric = sanitized_ds(metric)
    acc.append('DEF:{metric}_num={rrd_path}:{metric}:AVERAGE'.format(
      metric=metric,
      rrd_path=rrd_path))
    acc.append('LINE1:{metric}_num{color}:{metric}'.format(
      metric=metric,
      color=color_wheel.next()))
    acc.append('GPRINT:{metric}_num:MIN:Min %2.1lf%s'.format(
      metric=metric))
    acc.append('GPRINT:{metric}_num:AVERAGE:Avg %2.1lf%s'.format(
      metric=metric))
    acc.append('GPRINT:{metric}_num:MAX:Max %2.1lf%s\j'.format(
      metric=metric))

  ret = rrdtool.graph(
    png_path,
    '--start', '-1h',
    '--title={title}'.format(title=rrd),
    '--vertical-label=Default',
    '--slope-mode',
    '-w 450',
    acc)

  return render_template('index.html', png_url=url_for('static', filename='rrds/{rrd}-day.png'.format(rrd=rrd)))
