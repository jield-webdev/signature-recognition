class EmptyFileError(ValueError):
    pass


class UnsupportedContentTypeError(ValueError):
    pass


class InvalidImageError(ValueError):
    pass

class InvalidPdfError(ValueError):
    pass

class EmptyPdfError(ValueError):
    pass


class EncryptedPdfError(ValueError):
    pass
