"""Pyramid WSGI configuration"""
from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from board.models import initialize_sql


def main(global_config, **settings):
    """Return a Pyramid WSGI application"""
    # Connect to database
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    # Configure routes
    config = Configurator(settings=settings)
    config.add_static_view('static', 'board:static')
    config.add_route('index', '/', view='board.views.index',
        view_renderer='index.mak', request_method='GET')
    config.add_route('add', '/', view='board.views.add',
        view_renderer='index_.mak', request_method='POST')
    # Return WSGI app
    return config.make_wsgi_app()
