"""Decorators for Pagination."""

from typing import Any, Sequence, Tuple

from aries_cloudagent.messaging.models.base import BaseModel
from marshmallow import fields

from ..util import expand_model_class


@expand_model_class
class Page(BaseModel):
    """Page decorator for messages containing a paginated object."""

    class Fields:
        """Fields of page decorator."""

        count_ = fields.Int(required=True, data_key="count", example=10)
        offset = fields.Int(required=True, example=20)
        remaining = fields.Int(required=False, example=15)

    def __init__(
        self, count_: int = 0, offset: int = 0, remaining: int = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.count = count_
        self.offset = offset
        self.remaining = remaining


@expand_model_class
class Paginate(BaseModel):
    """Paginate decorator for messages querying for a paginated object."""

    class Fields:
        """Pagination decorator."""

        limit = fields.Int(
            required=True,
            description="return at most n items in paginated results",
            example=10,
        )
        offset = fields.Int(
            required=False,
            missing=0,
            description="Offset returned results by n items",
            example=20,
        )

    def __init__(self, limit: int = 0, offset: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.limit = limit
        self.offset = offset

    def apply(self, items: list) -> Tuple[Sequence[Any], Page]:
        """Apply pagination to list."""
        limit = self.limit if self.limit >= 1 else len(items[self.offset :])
        end = self.offset + limit
        result = items[self.offset : end]
        remaining = len(items[end:])
        page = Page(len(result), self.offset, remaining)
        return result, page
