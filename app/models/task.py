import datetime
import enum

from mongoengine import signals

from .. import db
from .user import User
from .utils import handler


@handler(signals.pre_save)
def update_modified(sender, document):
    document.update_at = datetime.datetime.utcnow()


class Category(enum.Enum):
    FLIP = 'FLIP'
    SHORT_TERM = 'STERM'
    LONG_TERM = 'LTERM'
    HIGHLIGHT = 'INTEREST'
    REVIEWED = 'REVIEWED'


@update_modified.apply
class DocumentCache(db.Document):  # type: ignore
    content = db.StringField()
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
    meta = {
        'collection': 'document_cache',
    }


@update_modified.apply
class DocumentMeta(db.DynamicDocument):  # type: ignore
    theme = db.StringField(max_length=256, required=True, unique=True)
    category = db.StringField(
        max_length=64,
        required=True,
        choices=[category.value for category in Category])
    url = db.StringField(max_length=1024)
    priority = db.IntField()
    comment = db.ListField(db.StringField())
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
    create_by = db.ReferenceField(User)
    cache = db.ReferenceField(DocumentCache)
    meta = {
        'collection':
        'document_meta',
        'indexes': [{
            'fields': ['theme']
        }, {
            'fields': ['category']
        }, {
            'fields': ['$theme', "$comment"],
            'default_language': 'english',
            'weights': {
                'theme': 8,
                'comment': 5
            }
        }]
    }

    def __repr__(self):
        return f'<Document \'{str(self)}\'>'

    def __str__(self):
        if len(self.theme) > 30:
            title = f'{self.theme[:30]}...'
        else:
            title = self.theme
        return title
