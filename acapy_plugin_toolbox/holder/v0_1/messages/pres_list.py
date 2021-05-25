from marshmallow import fields

from ....decorators.pagination import Page
from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class PresList(AdminHolderMessage):
    """Presentation get list response message."""

    message_type = "presentations-list"

    class Fields:
        """Fields for presentation list message."""

        results = fields.List(fields.Dict(), description="Retrieved presentations.")
        page = fields.Nested(
            Page.Schema,
            required=False,
            data_key="~page",
            description="Pagination decorator.",
        )

    def __init__(self, results, page: Page = None, **kwargs):
        super().__init__(**kwargs)
        self.results = results
        self.page = page
