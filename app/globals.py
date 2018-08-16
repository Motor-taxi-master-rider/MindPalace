import re
from enum import Enum

# String for all categories selection
ALL_CATEGORY = 'All categories'
# Regular expression to parse web page's 'Content-Type' in headers
CONTENT_TYPE_REG = re.compile(
    '(?P<type>\w+/\w+)(;\s*charset=(?P<encoding>[\w-]+))?')
# How many documents to cache for 1 time
DEFAULT_CACHE_BATCH_SIZE = 100
# Number of documents to show in my document page
DOCUMENT_PER_PAGE = 10
# Web page type which is enabled to store in the database, should be text like type
ENABLED_CACHE_TYPE = ('text/html', 'text/plain')
# This object id should never appears in database, used in test
INVALID_OBJECT_ID = '1' * 24


class MessageQueue(Enum):
    email = 'email'
    cache = 'cache'
