from flask import Flask, session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy # type: ignore

from config import config

db = SQLAlchemy()
bootstrap = Bootstrap5()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)

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
            user = User.query.get(user_id)
        else:
            user = None
        return dict(current_user=user)

    return app
