# flask-rrd

The flask-rrd project is a simple Flask web application that acts as an API to
create, update and graph RRD databases using
[rrdtool](http://oss.oetiker.ch/rrdtool/).

## development

The following is helpful for setting up a development environment or getting
started with a sample RRD. For actual deployment, see the `deployment` section.

### dependencies

```bash
apt-get install python-dev librrd-dev libxml2-dev libglib2.0-dev libcairo2-dev libpango1.0-dev```
```

### samples

Included in flask-rrd's manage.py script are a few commands to help create a
test RRD, update the test RRD, and lastly, graph the test RRD. All of the
manage.py commands depend on the flask-rrd web application being up and
healthy.


Start the web application.

```bash
manage.py runserver
```

Create the RRD.

```bash
manage.py create_rrd
```

Update the RRD. Note, this loops indefinitely (until you press CTRL+C) and will
update the RRD database every second.

```bash
manage.py update_rrd
```

Graph the RRD.

```bash
manage.py graph_rrd
```

Alternatively, you can navigate to
[http://localhost:5000/graph/test](http://localhost:5000/graph/test) to see the
RRD graph itself instead of
the response code.

## deployment

The RRD collectors provided in the `bin` directory depend on CRONd to invoke
them every minute. I'm not a huge fan of this, but this is easier for now.

```
VENV=/path/to/venv
FLASK_RRD_GIT=/path/to/flask-rrd/
* * * * * $VENV/bin/python $FLASK_RRD_GIT/bin/meminfo-to-rrd
* * * * * $VENV/bin/python $FLASK_RRD_GIT/bin/netdev-to-rrd eth0
```
