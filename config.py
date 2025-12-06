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
    NFT_MARKETPLACE_CONTRACT_ADDRESS = os.environ.get('NFT_MARKETPLACE_CONTRACT_ADDRESS')
    # Prefer MONAD_RPC_URL, fallback to MONAD_RPC for compatibility
    MONAD_RPC_URL = os.environ.get('MONAD_RPC_URL') or os.environ.get('MONAD_RPC')
    MONAD_CHAIN_ID = os.environ.get('MONAD_CHAIN_ID', 10143)
    MONAD_CHAIN_NAME = os.environ.get('MONAD_CHAIN_NAME', 'Monad Testnet')
    MONAD_NATIVE_NAME = os.environ.get('MONAD_NATIVE_NAME', 'Monad')
    MONAD_NATIVE_SYMBOL = os.environ.get('MONAD_NATIVE_SYMBOL', 'MON')
    MONAD_NATIVE_DECIMALS = os.environ.get('MONAD_NATIVE_DECIMALS', 18)
    MONAD_EXPLORER_URL = os.environ.get('MONAD_EXPLORER_URL', 'https://testnet.monadexplorer.com/')
    MONAD_BLOCK_GAS_LIMIT = os.environ.get('MONAD_BLOCK_GAS_LIMIT', 150000000)

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
