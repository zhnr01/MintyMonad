from flask import Flask
from flask_bootstrap import Bootstrap5
from config import config


bootstrap = Bootstrap5()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)

    from .main import main as main_blueprint
    from .nfts import nfts as nfts_blueprint
    from .auth import auth as auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(nfts_blueprint, url_prefix='/nfts')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
