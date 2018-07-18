import datetime

from flask import render_template
from flask_login import current_user

from app.main.views import main


@main.app_errorhandler(401)
def unauthorized(_):
    return render_template('errors/401.html'), 401


@main.app_errorhandler(403)
def forbidden(_):
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def page_not_found(_):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(_):
    return render_template('errors/500.html'), 500


@main.before_request
def modify_last_seen():
    if current_user.is_authenticated:
        if (datetime.datetime.utcnow() - current_user.last_seen).seconds > 100:
            current_user.last_seen = datetime.datetime.utcnow()
            current_user.save()
