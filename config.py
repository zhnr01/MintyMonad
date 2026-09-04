import os
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'development-only-change-me'
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    BOOTSTRAP_BOOTSWATCH_THEME  = 'pulse'
    ALCHEMY_API_KEY = os.environ.get('ALCHEMY_API_KEY')
    ALCHEMY_URL = f"https://monad-testnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY}/getNFTsForOwner"
    NFT_MARKETPLACE_CONTRACT_ADDRESS = os.environ.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
    MONAD_RPC_URL = os.environ.get('MONAD_RPC_URL') or os.environ.get('MONAD_RPC')
    MONAD_CHAIN_ID = int(os.environ.get('MONAD_CHAIN_ID', 10143))
    MONAD_CHAIN_NAME = os.environ.get('MONAD_CHAIN_NAME', 'Monad Testnet')
    MONAD_NATIVE_NAME = os.environ.get('MONAD_NATIVE_NAME', 'Monad')
    MONAD_NATIVE_SYMBOL = os.environ.get('MONAD_NATIVE_SYMBOL', 'MON')
    MONAD_NATIVE_DECIMALS = int(os.environ.get('MONAD_NATIVE_DECIMALS', 18))
    MONAD_EXPLORER_URL = os.environ.get('MONAD_EXPLORER_URL', 'https://testnet.monadexplorer.com/')
    MONAD_BLOCK_GAS_LIMIT = int(os.environ.get('MONAD_BLOCK_GAS_LIMIT', 150000000))

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
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @staticmethod
    def init_app(app):
        if not app.config.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY is required in production')
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            raise RuntimeError('DATABASE_URL is required in production')
        if not app.config.get('MONAD_RPC_URL'):
            raise RuntimeError('MONAD_RPC_URL is required in production')
        if not app.config.get('ALCHEMY_API_KEY'):
            raise RuntimeError('ALCHEMY_API_KEY is required in production')
        if not app.config.get('NFT_MARKETPLACE_CONTRACT_ADDRESS'):
            raise RuntimeError('NFT_MARKETPLACE_CONTRACT_ADDRESS is required in production')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
