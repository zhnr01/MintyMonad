import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    BOOTSTRAP_BOOTSWATCH_THEME  = 'pulse'
    ALCHEMY_API_KEY = os.environ.get('ALCHEMY_API_KEY')
    ALCHEMY_URL = f"https://monad-testnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY}/getNFTsForOwner"
    NFT_MARKETPLACE_CONTRACT_ADDRESS = '0xd4011963C4e1Ca6e1279b6398C4Cc352d0069d86'
    MONAD_RPC_URL = os.environ.get('MONAD_RPC')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(base_dir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
