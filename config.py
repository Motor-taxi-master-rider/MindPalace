import os
from abc import ABC, abstractmethod
from pathlib import Path

from dotenv import load_dotenv
from raygun4py.middleware import flask as flask_raygun

if Path('.env').exists():
    load_dotenv()


class Config(ABC):
    APP_NAME = os.environ.get('APP_NAME') or 'MindPalace'

    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ.get('SECRET_KEY')
    else:
        SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
        print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.sendgrid.net'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 587
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') or False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Analytics
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID') or ''
    SEGMENT_API_KEY = os.environ.get('SEGMENT_API_KEY') or ''

    # Admin account
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'test'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@admin.com'
    EMAIL_SUBJECT_PREFIX = f'[{APP_NAME}]'
    EMAIL_SENDER = f'{APP_NAME} Admin <{MAIL_USERNAME}>'

    RQ_HOST = os.getenv('RQ_HOST') or '127.0.0.1'
    RQ_PORT = os.getenv('RQ_PORT') or '6379'
    RQ_DB = os.getenv('RQ_DB') or '0'
    RQ_PASSWORD = os.getenv('RQ_PASSWORD')
    RQ_REDIS_URL = f'redis://{RQ_HOST}:{RQ_PORT}/{RQ_DB}'

    RAYGUN_APIKEY = os.environ.get('RAYGUN_APIKEY')

    @classmethod
    @abstractmethod
    def init_app(cls, app):
        """init app with config"""


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'doc_search'
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or '127.0.0.1'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT', 0)) or 27017
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')

    @classmethod
    def init_app(cls, app):
        print('THIS APP IS IN DEBUG MODE. \
                YOU SHOULD NOT SEE THIS IN PRODUCTION.')


class TestingConfig(Config):
    TESTING = True
    MOCK_MONGO = 'mongomock'
    MONGODB_DB = 'doc_search'
    MONGODB_SETTINGS = {'host': f'mongomock://localhost/{MOCK_MONGO}'}
    WTF_CSRF_ENABLED = False

    @classmethod
    def init_app(cls, app):
        print('THIS APP IS IN TESTING MODE.  \
                YOU SHOULD NOT SEE THIS IN PRODUCTION.')


class ProductionConfig(Config):
    MONGODB_DB = os.environ.get('MONGODB_DB')
    MONGODB_HOST = os.environ.get('MONGODB_HOST')
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT', 0)) or 27017
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
    SSL_DISABLE = (os.environ.get('SSL_DISABLE') or 'True') == 'True'

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.environ.get('SECRET_KEY'), 'SECRET_KEY IS NOT SET!'

        flask_raygun.Provider(app, app.config['RAYGUN_APIKEY']).attach()


class HerokuConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # Handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig,
    'unix': UnixConfig
}
