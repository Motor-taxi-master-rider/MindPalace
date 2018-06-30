import datetime
import enum

from .. import db


class Category(enum.Enum):
    SHORT_TERM = 'STERM'
    LONG_TERM = 'LTERM'
    HIGHLIGHT = 'INTEREST'
    REVIEWED = 'REVIEWED'
    FLIP = 'FLIP'


class DocumentCache(db.Document):
    cache_text = db.StringField()
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
    meta = {
        'collection': 'document_cache',
    }


class DocumentMeta(db.DynamicDocument):
    theme = db.StringField(max_length=128, unique=True)
    category = db.StringField(max_length=64, choice=(category.name for category in Category))
    url = db.StringField(max_length=128)
    priority = db.IntField()
    comment = db.ListField(db.StringField())
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
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
        if len(self.theme) > 20:
            title = f'{self.theme}...'
        else:
            title = self.theme
        return f'<Document \'{title}\'>'
