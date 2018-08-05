from flask_wtf import FlaskForm
from mongoengine import Q
from wtforms import (HiddenField, SelectField, SelectMultipleField,
                     StringField, SubmitField)
from wtforms.fields.html5 import URLField
from wtforms.validators import URL, InputRequired, Length, ValidationError

from app.globals import INVALID_OBJECT_ID
from app.models import Category, DocumentMeta, SystemTag, UserTag, itertools
from app.utils import beautify_static


class DocMetaForm(FlaskForm):
    id = HiddenField('Id')
    theme = StringField('Theme', validators=[InputRequired(), Length(1, 256)])
    category = SelectField(
        'Category',
        validators=[InputRequired()],
        choices=[(cat.value, cat.value.lower()) for cat in Category])
    url = URLField(
        'Link', validators=[InputRequired(),
                            Length(1, 1024),
                            URL()])
    tags = SelectMultipleField(
        'Tags',
        choices=[(tag.value, beautify_static(tag.value))
                 for tag in iter(itertools.chain(UserTag, SystemTag))])
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
