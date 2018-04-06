# flask-rrd

The flask-rrd project is a simple Flask web application that acts as an API to
create, update and graph RRD databases using
[rrdtool](http://oss.oetiker.ch/rrdtool/).

![A sample RRD made by flask-rrd!](https://github.com/sholsapp/flask-rrd/blob/master/docs/images/netdev.png)

## development

The following is helpful for setting up a local development environment or
getting started with a sample RRD. For actual deployment, see the `deployment`
section.

### dependencies

Several native dependencies need to be installed so that the Python `rrdtool`
module can be compiled. Install them using your system's package manager.

For yum-based systems:

  1. python-dev
  2. librrd-dev
  3. libxml2-dev
  4. libglib2.0-dev
  5. libcairo2-dev
  6. libpango1.0-dev

For apt-get-based systems:

  1. python-dev
  2. librrd-dev
  3. libxml2-dev
  4. libglib2.0-dev
  5. libcairo2-dev
  6. libpango1.0-dev

Once you have the native dependencies installed, install the required Python
dependencies into a virtualenv using pip. If you find flask-rrd works with
newer versions of these pinned libraries, I would appreciate a PR to update the
libraries.

```
pip install -r requirements.txt
```

### docker

Alternatively, if local development isn't your think, you can build and deploy inside of a Docker container. Build a Docker image by running the following command.

```
docker build --tag flask-rrd:latest .
```

You can also then deploy the application in a Docker container like so.

```
docker run -p 5000:500 flask-rrd:latest
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

Update the RRD. Note, this also creates the RRD the first time you run it. This
loops indefinitely (until you press CTRL+C) and will update the RRD database
every second.

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
* * * * * $VENV/bin/python $FLASK_RRD_GIT/bin/stat-to-rrd
* * * * * $VENV/bin/python $FLASK_RRD_GIT/bin/netdev-to-rrd eth0
* * * * * $VENV/bin/python $FLASK_RRD_GIT/bin/df-to-rrd
```
