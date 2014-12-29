import logging

from flask import Flask, Response, render_template, jsonify, request
from flask.ext.bootstrap import Bootstrap
from flask.ext.restless import APIManager
import rrdtool

from flaskrrd.api import api
from flaskrrd.model import make_conn_str, db, RRD


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


# Initialize Flask and register a blueprint
app = Flask(__name__)
# Note, this url namespace also exists for the Flask-Restless
# extension and is where CRUD interfaces live, so be careful not to
# collide with model names here. We could change this, but it's nice
# to have API live in the same url namespace.
app.register_blueprint(api, url_prefix='/api')

# Initialize Flask-Restless
manager = APIManager(app, flask_sqlalchemy_db=db)
#manager.create_api(Messages, methods=['GET', 'POST'])

# Initialize Flask-Bootstrap
Bootstrap(app)


def init_webapp():
  """Initialize the web application."""
  app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
  db.app = app
  db.init_app(app)
  db.create_all()
  return app


@app.route('/')
def index():
  log.debug('Someone accessed index.html!')
  return render_template('index.html', messages=Messages.query.all())


@app.route('/create/<rrd>', methods=['POST'])
def create(rrd):
  """Creates a new RRD database.

  The request should contain a JSON payload that specifies parameters to the
  `rrdtool.create` function.

  """

  desc = request.json

  log.debug('Creating database for [%s] with description [%s]', rrd, desc)

  metrics = []
  for name in desc['metrics']:
    metrics.append(
      'DS:{name}:{type}:2000:U:U'.format(name=name, type=desc['type'])
    )

  rrdtool.create(
    '{rrd}.rrd'.format(rrd=rrd),
    '--step', '300',
    '--start', '0',
    metrics,
    'RRA:MIN:0:360:576',
    'RRA:MIN:0:30:576',
    'RRA:MIN:0:7:576',
    'RRA:AVERAGE:0:360:576',
    'RRA:AVERAGE:0:30:576',
    'RRA:AVERAGE:0:7:576',
    'RRA:AVERAGE:0:1:576',
    'RRA:MAX:0:360:576',
    'RRA:MAX:0:30:576',
    'RRA:MAX:0:7:576',)

  new_rrd = RRD(rrd, desc['metrics'], desc['type'])
  db.session.add(new_rrd)
  db.session.commit()

  return Response(status=200)


# XXX: This no worky.
@app.route('/update/<rrd>', methods=['POST'])
def update(rrd):
  """Update a RRD database."""
  return Response(status=405)


# XXX: This only works for the sample graph that we generated from the
# manage.py `create_rrd` command for now. We'll need a database to record this
# sort of stuff and do validation in the future.
@app.route('/graph/<rrd>')
def graph(rrd):
  """Graph a RRD database."""
  ret = rrdtool.graph(
    "{rrd}-day.png".format(rrd=rrd),
    "--start", "-1d",
    "--vertical-label=Num",
    "-w 600",
    "DEF:m1_num={rrd}.rrd:metric1:AVERAGE".format(rrd=rrd),
    "DEF:m2_num={rrd}.rrd:metric2:AVERAGE".format(rrd=rrd),
    "DEF:m3_num={rrd}.rrd:metric3:AVERAGE".format(rrd=rrd),
    "LINE1:m1_num#0000FF:metric1",
    "LINE2:m2_num#00FF00:metric2",
    "LINE3:m3_num#FF0000:metric3",
    'GPRINT:m1_num:LAST:Last m1 value\: %2.1lf X',
    'GPRINT:m2_num:LAST:Last m2 value\: %2.1lf X',
    'GPRINT:m3_num:LAST:Last m3 value\: %2.1lf X',)
  return Response(status=200)
