from pathlib import Path

from flask import Flask
from flask_assets import Environment
from flask_compress import Compress
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_mongoengine import MongoEngine
from flask_rq2 import RQ
from flask_wtf import CSRFProtect

from app.assets import app_css, app_js, vendor_css, vendor_js
from config import config

basedir = Path(__file__).parent

mail = Mail()
db = MongoEngine()
csrf = CSRFProtect()
compress = Compress()
moment = Moment()
rq = RQ()

# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'account.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    # Set up extensions
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    moment.init_app(app)
    rq.init_app(app)

    # Register Jinja template functions
    from .utils import register_template_utils
    register_template_utils(app)

    # Set up asset pipeline
    assets_env = Environment(app)
    dirs = ['assets/styles', 'assets/scripts']
    for path in dirs:
        assets_env.append_path(basedir / path)
    assets_env.url_expire = True

    assets_env.register('app_css', app_css)
    assets_env.register('app_js', app_js)
    assets_env.register('vendor_css', vendor_css)
    assets_env.register('vendor_js', vendor_js)

    # Configure SSL if platform supports it
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        SSLify(app)

    # Create app blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .task import task as task_blueprint
    app.register_blueprint(task_blueprint, url_prefix='/task')

    if config_name == 'production':
        from app.jobs.doc_cache import doc_cache
        # Create cron jobs
        doc_cache.cron('0 0 12 * * *', 'cache_job')

        @rq.exception_handler
        def send_alert_to_ops(job, *exc_info):
            print(job)
            print(exc_info)

    return app
