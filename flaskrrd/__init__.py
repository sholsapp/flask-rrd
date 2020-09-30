import logging
import os
import re

from flask import Flask, Response, render_template, jsonify, request, url_for, safe_join
from flask_bootstrap import Bootstrap
import rrdtool

from flaskrrd.color import ColorWheel
from flaskrrd.model import make_conn_str, db, RRD


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


app = Flask(__name__)


def init_webapp(test=False):
    """Initialize the web application.

    This function takes care to initialize:

      - The Flask web application.
      - The Flask-SQLAlchemy library.
      - The Flask-Restless library.

    If initialized with `test=True` the application will use an in-memory
    SQLite database, and should be used for unit testing, but not much else.

    """
    global app

    if test:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()

    Bootstrap(app)
    with app.app_context():
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
    """Get an RRD path on local disk by name.

    Uses :func:`flask.safe_join` to safely fetch an RRD path on local disk by
    name.

    """
    rrd_dir = os.path.join(app.static_folder, 'rrds')
    return safe_join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))


def get_png_path(rrd):
    """Get an RRD's image path on local disk by name.

    Uses :func:`flask.safe_join` to safely fetch an RRD path on local disk by
    name.

    """
    rrd_dir = os.path.join(app.static_folder, 'rrds')
    return safe_join(rrd_dir, '{rrd}-day.png'.format(rrd=rrd))


def create_rrd(rrd, description):
    """Create an RRD.

    :param description: A :class:`dict` that describes the new RRD.

    """
    rrd_path = get_rrd_path(rrd)

    metrics_names = []
    metrics = []

    for ds_type in description['metrics']:
        for ds in description['metrics'][ds_type]:
            metrics_names.append(sanitized_ds(ds))
            metrics.append('DS:{name}:{type}:120:U:U'.format(name=sanitized_ds(ds), type=ds_type))

    rrdtool.create(
        rrd_path,
        '--step', '60',
        '--start', '0',
        metrics,
        # See http://oss.oetiker.ch/rrdtool/doc/rrdcreate.en.html for more about
        # RRA.
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
        'RRA:MAX:0:7:2400',
    )

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
    desc = request.get_json()
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

    This functionality is a default that graphs all metrics contained in a
    single RRD database. For example, for a theoretical RRD database named
    "weather", this route will print RRD charts for each metric "temperature",
    "humidity", etc.

    Accepts query parameters for the following::

        - `start` - Should be an meaningful string for RRD to indicate the
          desired start of the RRD. For example, can be `-1h` to indicate to
          show data from 1 hour ago to now, or `-24h` to show data from 24
          hours ago to now.
        - `width` - Should be a width in pixels, and must be greater than 10
          pixels, per RRD's requirement.


    """

    start = request.args.get('start', '-1h')
    width = request.args.get('width', '450')

    rrd_path = get_rrd_path(rrd)
    if not os.path.exists(rrd_path):
        log.error('The rrd [%s] does not exist!', rrd)
        return Response(status=500)

    png_path = get_png_path(rrd)
    rrd_entry = RRD.query.filter_by(name=rrd).first()

    if not rrd_entry:
        log.error('No existing entry for rrd [%s].', rrd)
        return Response(405)

    color_wheel = ColorWheel()

    acc = []
    for metric in rrd_entry.cols_desc.split(','):
        metric = sanitized_ds(metric)
        acc.append('DEF:{metric}_num={rrd_path}:{metric}:AVERAGE'.format(metric=metric, rrd_path=rrd_path))
        acc.append('LINE1:{metric}_num{color}:{metric}'.format(metric=metric, color=color_wheel.next()))
        acc.append('GPRINT:{metric}_num:MIN:Min %2.1lf%s'.format(metric=metric))
        acc.append('GPRINT:{metric}_num:AVERAGE:Avg %2.1lf%s'.format(metric=metric))
        acc.append('GPRINT:{metric}_num:MAX:Max %2.1lf%s\j'.format(metric=metric))

    ret = rrdtool.graph(
      png_path,
        '--start', str(start),
        '--title={title}'.format(title=rrd),
        '--vertical-label=Default',
        '--slope-mode',
        '--width', str(width),
        acc,
    )

    return render_template('index.html', png_urls=[url_for('static', filename='rrds/{rrd}-day.png'.format(rrd=rrd))])


@app.route('/dashboard')
def dashboard():
    """Graph all RRD databases on a single page.

    Accepts query parameters for the following::

        - `start` - Should be an meaningful string for RRD to indicate the
          desired start of the RRD. For example, can be `-1h` to indicate to
          show data from 1 hour ago to now, or `-24h` to show data from 24
          hours ago to now.
        - `width` - Should be a width in pixels, and must be greater than 10
          pixels, per RRD's requirement.

    """

    start = request.args.get('start', '-1h')
    width = request.args.get('width', '450')

    rrds = []

    for rrd_entry in RRD.query.all():

        rrd_path = get_rrd_path(rrd_entry.name)
        if not os.path.exists(rrd_path):
            log.error('The rrd [%s] does not exist!', rrd)
            return Response(status=500)

        png_path = get_png_path(rrd_entry.name)

        color_wheel = ColorWheel()

        acc = []
        for metric in rrd_entry.cols_desc.split(','):
            metric = sanitized_ds(metric)
            acc.append('DEF:{metric}_num={rrd_path}:{metric}:AVERAGE'.format(metric=metric, rrd_path=rrd_path))
            acc.append('LINE1:{metric}_num{color}:{metric}'.format(metric=metric, color=color_wheel.next()))
            acc.append('GPRINT:{metric}_num:MIN:Min %2.1lf%s'.format(metric=metric))
            acc.append('GPRINT:{metric}_num:AVERAGE:Avg %2.1lf%s'.format(metric=metric))
            acc.append('GPRINT:{metric}_num:MAX:Max %2.1lf%s\j'.format(metric=metric))

        ret = rrdtool.graph(
            png_path,
            '--start', str(start),
            '--title={title}'.format(title=rrd_entry.name),
            '--vertical-label=Default',
            '--slope-mode',
            '--width', str(width),
            acc,
        )

        rrds.append(url_for('static', filename='rrds/{name}-day.png'.format(name=rrd_entry.name)))

    return render_template('index.html', png_urls=rrds)
