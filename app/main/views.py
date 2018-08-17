import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from app.models import EditableHTML

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)


@main.before_request
def modify_last_seen():
    if current_user.is_authenticated:
        if (datetime.datetime.utcnow() - current_user.last_seen).seconds > 100:
            current_user.last_seen = datetime.datetime.utcnow()
            current_user.save()
