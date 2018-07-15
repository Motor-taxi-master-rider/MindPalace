from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, SubmitField
from wtforms.fields.html5 import URLField
from wtforms.validators import URL, InputRequired, Length, NumberRange, ValidationError

from app.models import Category, DocumentMeta


class DocMetaForm(FlaskForm):
    theme = StringField('Theme', validators=[InputRequired(), Length(1, 256)])
    category = SelectField(
        'Category',
        validators=[InputRequired()],
        choices=[(cat.value, cat.name.lower()) for cat in Category])
    url = URLField(
        'Link', validators=[InputRequired(),
                            Length(1, 1024),
                            URL()])
    priority = IntegerField(
        'Priority', validators=[NumberRange(0, 3)], default=0)
    submit = SubmitField('Submit Document')

    def validate_theme(self, theme):
        if DocumentMeta.objects(theme=theme.data).first():
            raise ValidationError('Theme already exists.')
