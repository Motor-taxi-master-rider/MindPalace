from flask_wtf import FlaskForm
from mongoengine import Q
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.fields.html5 import URLField
from wtforms.validators import URL, InputRequired, Length, ValidationError

from app.models import Category, DocumentMeta
from app.utils import INVALID_OBJECT_ID


class DocMetaForm(FlaskForm):
    id = HiddenField('Id')
    theme = StringField('Theme', validators=[InputRequired(), Length(1, 256)])
    category = SelectField(
        'Category',
        validators=[InputRequired()],
        choices=[(cat.value, cat.name.lower()) for cat in Category])
    url = URLField(
        'Link', validators=[InputRequired(),
                            Length(1, 1024),
                            URL()])
    priority = SelectField(
        'Priority',
        choices=[(i, i) for i in range(0, 4)],
        coerce=int,
        default=0)
    submit = SubmitField('Submit Document')

    def validate_theme(self, theme):
        if DocumentMeta.objects(
                Q(theme=theme.data) & Q(
                    id__ne=self.id.data or INVALID_OBJECT_ID)).first():
            raise ValidationError('Theme already exists.')
