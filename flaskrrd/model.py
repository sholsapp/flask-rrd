from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String


db = SQLAlchemy()


class RRD(db.Model):
  """A database table for RRD databases.

  :param str name: The RRD database name.
  :param list[str] cols: The RRD database metric names.
  :param str path: The RRD database path.

  """

  __tablename__ = 'rrd'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(60))
  cols_n = db.Column(db.Integer)
  cols_desc = db.Column(db.String(1024))
  path = db.Column(db.String(1024))

  def __init__(self, name, cols, path):
    self.name = name
    self.cols_n = len(cols)
    self.cols_desc = ','.join(cols)
    self.path = path

  def __repr__(self):
    return 'RRD(%r, %r)' % (
      repr(self.name),
      repr(self.cols_desc.split(',')))


class Graph(db.Model):
  """A database table for graphs of RRD databases."""

  __tablename__ = 'graph'

  id = db.Column(db.Integer, primary_key=True)

  def __init__(self):
    pass


def make_conn_str():
  """Make an local database file on disk."""
  return 'sqlite:///flaskrrd.db'
