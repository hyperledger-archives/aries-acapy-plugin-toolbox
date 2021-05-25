from typing import Sequence

from marshmallow import fields

from ....decorators.pagination import Page
from ....util import expand_message_class
from .base import AdminHolderMessage


@expand_message_class
class CredList(AdminHolderMessage):
    """Credential list message."""

    message_type = "credentials-list"

    class Fields:
        """Fields of credential list message."""

        results = fields.List(
            fields.Dict(),
            required=True,
            description="List of requested credentials",
            example=[],
        )
        page = fields.Nested(
            Page.Schema,
            required=False,
            data_key="~page",
            description="Pagination decorator.",
        )

    def __init__(self, results: Sequence[dict], page: Page = None, **kwargs):
        super().__init__(**kwargs)
        self.results = results
        self.page = page
