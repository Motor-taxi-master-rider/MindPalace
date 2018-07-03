from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import URL, Email, InputRequired, Length, NumberRange

from app.models import Category


class DocMetaForm(FlaskForm):
    theme = StringField(
        'Theme', validators=[InputRequired(),
                             Length(1, 256)])
    category = SelectField(
        'Category',
        validators=[InputRequired()],
        choices=[(cat.value, cat.name.lower()) for cat in Category])
    link = StringField(
        'Link', validators=[InputRequired(),
                            Length(1, 1024),
                            URL()])
    priority = IntegerField(
        'Priority', validators=[NumberRange(0, 3)], default=0)
    submit = SubmitField('Add Document')
