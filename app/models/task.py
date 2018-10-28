import datetime
import itertools
from enum import Enum

from mongoengine import signals

from .. import db
from .user import User
from .utils import handler


@handler(signals.pre_save)
def update_modified(sender, document):
    document.update_at = datetime.datetime.utcnow()


class Category(Enum):
    SHORT_TERM = 'short_term'
    LONG_TERM = 'long_term'
    FLIP = 'flip'


class UserTag(Enum):
    impressive = 'impressive'
    reviewed = 'reviewed'
    to_do = 'to do'
    cache = 'cache'


class SystemTag(Enum):
    cached = 'cached'
    unable_to_cache = 'unable to cache'


class DocumentCache(db.EmbeddedDocument):  # type: ignore
    content = db.StringField()
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)


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
    tags = db.ListField(
        db.StringField(choices=[
            tag.value for tag in iter(itertools.chain(UserTag, SystemTag))
        ]))
    update_at = db.DateTimeField(default=datetime.datetime.utcnow)
    create_by = db.ReferenceField(User)
    cache = db.EmbeddedDocumentField(DocumentCache)
    meta = {
        'collection': 'document_meta',
        'indexes': [{
            'fields': ['theme']
        }, {
            'fields': ['category']
        }, {
            'fields': ['$theme', "$comment", "$cache.content"],
            'default_language': 'english',
            'weights': {
                'theme': 8,
                'comment': 5,
                'cache.content': 3
            }
        }]
    }  # yapf: disable

    def __repr__(self):
        return f'<Document \'{str(self)}\'>'

    def __str__(self):
        if len(self.theme) > 30:
            title = f'{self.theme[:30]}...'
        else:
            title = self.theme
        return title
