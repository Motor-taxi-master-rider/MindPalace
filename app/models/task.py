import datetime
import enum

from .. import db
from .user import User


class Category(enum.Enum):
    SHORT_TERM = 'STERM'
    LONG_TERM = 'LTERM'
    HIGHLIGHT = 'INTEREST'
    REVIEWED = 'REVIEWED'
    FLIP = 'FLIP'


class DocumentCache(db.Document):
    content = db.StringField()
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
    meta = {
        'collection': 'document_cache',
    }


class DocumentMeta(db.DynamicDocument):
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
        'collection': 'document_meta',
        'indexes': [{
            'fields': ['theme']
        }, {
            'fields': ['category']
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
