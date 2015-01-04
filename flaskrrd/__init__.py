import logging
import os

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
  WHEEL = []

  def __init__(self):
    for red in range(255, 64, -8):
      self.WHEEL.append(self.rgb_to_hex((red, 0, 0)))
    for green in range(255, 64, -8):
      self.WHEEL.append(self.rgb_to_hex((0, green, 0)))
    for blue in range(255, 64, -8):
      self.WHEEL.append(self.rgb_to_hex((0, 0, blue)))

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
  return app


@app.route('/')
def index():
  return 'GOOD'


@app.route('/create/<rrd>', methods=['POST'])
def create(rrd):
  """Creates a new RRD database.

  The request should contain a JSON payload that specifies parameters to the
  `rrdtool.create` function.

  """

  desc = request.json

  log.debug('Creating database for [%s] with description [%s]', rrd, desc)

  rrd_dir = os.path.join(app.static_folder, 'rrds')
  if not os.path.exists(rrd_dir):
    os.makedirs(rrd_dir)
  rrd_path = os.path.join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))

  metrics = []
  for name in desc['metrics']:
    metrics.append(
      'DS:{name}:{type}:2000:U:U'.format(name=name, type=desc['type'])
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

  new_rrd = RRD(rrd, desc['metrics'], desc['type'], rrd_path)
  db.session.add(new_rrd)
  db.session.commit()

  return Response(status=200)


@app.route('/update/<rrd>', methods=['POST'])
def update(rrd):
  """Update a RRD database."""
  desc = request.json
  rrd_entry = RRD.query.filter_by(name=rrd).first()
  if not rrd_entry:
    log.error('No existing entry for rrd [%s].', rrd)
    return Response(status=405)
  rrdtool.update(str(rrd_entry.path), 'N:{data}'.format(data=':'.join(desc['values'])))
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
    acc.append('DEF:{metric}_num={rrd_path}:{metric}:AVERAGE'.format(
      metric=metric,
      rrd_path=rrd_path))
    acc.append('LINE1:{metric}_num{color}:{metric}'.format(
      metric=metric,
      color=color_wheel.next()))

  ret = rrdtool.graph(
    png_path,
    '--start', '-1h',
    '--vertical-label=Num',
    '--slope-mode',
    '-w 600',
    acc)
    #'GPRINT:m1_num:LAST:Last m1 value\: %2.1lf X',
    #'GPRINT:m2_num:LAST:Last m2 value\: %2.1lf X',
    #'GPRINT:m3_num:LAST:Last m3 value\: %2.1lf X',)

  return render_template('index.html', png_url=url_for('static', filename='rrds/{rrd}-day.png'.format(rrd=rrd)))
