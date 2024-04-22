# Own's Libraries
from order_modules.errors.base_error import BaseError


class SourceError(BaseError):
    pass


class DataBaseError(BaseError):
    """This error should be launched when record/item
    don't exist in BD."""

    pass


class NoRecordsFoundError(BaseError):
    """This error should be launched when record/item
    don't exist in BD."""

    pass


class NoRecordFoundError(BaseError):
    """This error should be launched when record/item
    don't exist in BD."""

    pass


class DuplicateRecordError(BaseError):
    """This error should be launched when record/item
    is duplicated in BD."""

    pass


class MultipleRecordsFoundError(BaseError):
    """This error should be launched when exist more than one
    record/item in BD."""

    pass
