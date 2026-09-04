import json
import logging
import re
from uuid import uuid4

from flask import Flask, g, request, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            return json.dumps({
                'level': record.levelname,
                'event': record.getMessage(),
                'request_id': getattr(g, 'request_id', None),
            })

    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.before_request
    def assign_request_id():
        supplied_id = request.headers.get('X-Request-ID', '')
        if re.fullmatch(r'[A-Za-z0-9_-]{1,64}', supplied_id):
            g.request_id = supplied_id
        else:
            g.request_id = uuid4().hex

    @app.after_request
    def add_request_id(response):
        response.headers['X-Request-ID'] = g.request_id
        return response

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Content-Security-Policy', "default-src 'self'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; script-src 'self' https://cdn.jsdelivr.net; img-src 'self' https: data:; connect-src 'self' https:; frame-ancestors 'self'")
        return response

    from .main import main as main_blueprint
    from .nfts import nfts as nfts_blueprint
    from .auth import auth as auth_blueprint
    from .api import api as api_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(nfts_blueprint, url_prefix='/nfts')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from app.model import User
    @app.context_processor
    def inject_user():
        user_id = session.get('user_id')
        if user_id:
            user = db.session.get(User, user_id)
        else:
            user = None
        return dict(current_user=user)

    return app
