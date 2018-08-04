class MindPalaceException(Exception):
    pass


class AsyncJobException(MindPalaceException):
    pass


class DocCacheException(AsyncJobException):
    def __init__(self, msg, document):
        super().__init__(msg)
        self.document = document


class InvalidContentType(MindPalaceException):
    pass
