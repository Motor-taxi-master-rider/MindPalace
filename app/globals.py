import re
# String for all categories selection
from enum import Enum

ALL_CATEGORY = 'All categories'
# Regular expression to parse web page's 'Content-Type' in headers
CONTENT_TYPE_REG = re.compile(
    '(?P<type>\w+/\w+)(;\s*charset=(?P<encoding>[\w-]+))?')
# Number of documents to show in my document page
DOCUMENT_PER_PAGE = 10
# Web page type which is enabled to store in the database, should be text like type
ENABLED_CACHE_TYPE = ('text/html', )
# This object id should never appears in database, used in test
INVALID_OBJECT_ID = '1' * 24


class MessageQueue(Enum):
    email = 'email'
    cache = 'cache'
