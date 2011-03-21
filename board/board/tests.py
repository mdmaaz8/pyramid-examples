"""Tests"""
import unittest
from pyramid.config import Configurator
from pyramid import testing
from sqlalchemy import create_engine

from board.models import initialize_sql, Post


def _initTestingDB():
    return initialize_sql(create_engine('sqlite://'))


class TestMyView(unittest.TestCase):

    db = _initTestingDB()

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_index(self):
        from board.views import index
        # Make sure that index() returns as many posts as exist in the database
        request = testing.DummyRequest()
        info = index(request)
        self.assertEqual(len(info['posts']), self.db.query(Post).count())

    def test_add(self):
        from board.views import add
        # Make sure that add() does not add empty posts
        postCount = self.db.query(Post).count()
        request = testing.DummyRequest(params={'text': u''}, post=True)
        info = add(request)
        self.assertEqual(len(info['posts']), postCount)
        # Make sure that add() increments the number of posts
        postCount = self.db.query(Post).count()
        request = testing.DummyRequest(params={'text': u'four'}, post=True)
        info = add(request)
        self.assertEqual(len(info['posts']), postCount + 1)
