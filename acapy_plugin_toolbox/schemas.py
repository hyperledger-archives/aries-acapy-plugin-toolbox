"""Define messages for schemas admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from asyncio import shield

from marshmallow import fields

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.indy.issuer import IndyIssuer
from aries_cloudagent.storage.error import StorageNotFoundError

from .util import generate_model_schema, admin_only

PROTOCOL = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-schemas/0.1"

SEND_SCHEMA = "{}/send-schema".format(PROTOCOL)
SCHEMA_ID = "{}/schema-id".format(PROTOCOL)
SCHEMA_GET = "{}/schema-get".format(PROTOCOL)
SCHEMA = "{}/schema".format(PROTOCOL)
SCHEMA_GET_LIST = "{}/schema-get-list".format(PROTOCOL)
SCHEMA_LIST = "{}/schema-list".format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_SCHEMA: "acapy_plugin_toolbox.schemas" ".SendSchema",
    SCHEMA_ID: "acapy_plugin_toolbox.schemas" ".SchemaID",
    SCHEMA_GET: "acapy_plugin_toolbox.schemas" ".SchemaGet",
    SCHEMA: "acapy_plugin_toolbox.schemas" ".Schema",
    SCHEMA_GET_LIST: "acapy_plugin_toolbox.schemas" ".SchemaGetList",
    SCHEMA_LIST: "acapy_plugin_toolbox.schemas" ".SchemaList",
}


async def setup(session: ProfileSession, protocol_registry: ProtocolRegistry = None):
    """Setup the schemas plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


class SchemaRecord(BaseRecord):
    """Represents a Schema."""

    RECORD_ID_NAME = "record_id"
    RECORD_TYPE = "schema"

    AUTHOR_SELF = "self"
    AUTHOR_OTHER = "other"

    STATE_UNWRITTEN = "unwritten"
    STATE_WRITTEN = "written"

    class Meta:
        """SchemaRecord metadata."""

        schema_class = "SchemaRecordSchema"

    def __init__(
        self,
        *,
        record_id: str = None,
        schema_id: str = None,
        schema_name: str = None,
        schema_version: str = None,
        author: str = None,
        attributes: [str] = None,
        state: str = None,
        **kwargs
    ):
        """Initialize a new SchemaRecord."""
        super().__init__(record_id, state or self.STATE_UNWRITTEN, **kwargs)
        self.schema_id = schema_id
        self.schema_name = schema_name
        self.schema_version = schema_version
        self.author = author
        self.attributes = attributes

    @property
    def record_id(self) -> str:
        """Get the id."""
        return self._id

    @property
    def record_value(self) -> dict:
        """Get record value."""
        return {
            prop: getattr(self, prop)
            for prop in (
                "attributes",
                "schema_name",
                "schema_version",
                "state",
                "author",
            )
        }

    @property
    def record_tags(self) -> dict:
        """Get tags for record."""
        return {prop: getattr(self, prop) for prop in ("schema_id",)}

    @classmethod
    async def retrieve_by_schema_id(
        cls, session: ProfileSession, schema_id: str
    ) -> "SchemaRecord":
        """Retrieve a schema record by schema_id."""
        return await cls.retrieve_by_tag_filter(session, {"schema_id": schema_id})


class SchemaRecordSchema(BaseRecordSchema):
    """Schema to allow serialization/deserialization of Schema records."""

    class Meta:
        """PoolRecordSchema metadata."""

        model_class = SchemaRecord

    schema_id = fields.Str(required=False)
    schema_name = fields.Str(required=False)
    schema_version = fields.Str(required=False)
    author = fields.Str(required=False)
    attributes = fields.List(fields.Str(), required=False)


SendSchema, SendSchemaSchema = generate_model_schema(
    name="SendSchema",
    handler="acapy_plugin_toolbox.schemas.SendSchemaHandler",
    msg_type=SEND_SCHEMA,
    schema={
        "schema_name": fields.Str(required=True),
        "schema_version": fields.Str(required=True),
        "attributes": fields.List(fields.Str(), required=True),
    },
)
SchemaID, SchemaIDSchema = generate_model_schema(
    name="SchemaID",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=SCHEMA_ID,
    schema={"schema_id": fields.Str()},
)


class SendSchemaHandler(BaseHandler):
    """Handler for received send schema request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send schema request."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        issuer: IndyIssuer = session.inject(IndyIssuer)
        async with ledger:
            schema_id, schema_def = await shield(
                ledger.create_and_send_schema(
                    issuer,
                    context.message.schema_name,
                    context.message.schema_version,
                    context.message.attributes,
                )
            )
        # Note: We may not need to save the schema as done below.
        schema = SchemaRecord(
            schema_id=schema_id,
            schema_name=context.message.schema_name,
            schema_version=context.message.schema_version,
            attributes=context.message.attributes,
            state=SchemaRecord.STATE_WRITTEN,
            author=SchemaRecord.AUTHOR_SELF,
        )
        await schema.save(session, reason="Committed to ledger")

        result = SchemaID(schema_id=schema_id)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


SchemaGet, SchemaGetSchema = generate_model_schema(
    name="SchemaGet",
    handler="acapy_plugin_toolbox.schemas.SchemaGetHandler",
    msg_type=SCHEMA_GET,
    schema={"schema_id": fields.Str(required=True)},
)
Schema, SchemaSchema = generate_model_schema(
    name="Schema",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=SCHEMA,
    schema=SchemaRecordSchema,
)


class SchemaGetHandler(BaseHandler):
    """Handler for received schema get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received schema get request."""
        try:
            session = await context.session()
            schema_record = await SchemaRecord.retrieve_by_schema_id(
                session, context.message.schema_id
            )
            schema_msg = Schema(**schema_record.serialize())
            schema_msg.assign_thread_from(context.message)
            await responder.send_reply(schema_msg)
            return
        except StorageNotFoundError:
            pass

        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        async with ledger:
            schema = await ledger.get_schema(context.message.schema_id)

        schema_record = SchemaRecord(
            schema_id=schema["id"],
            schema_name=schema["name"],
            schema_version=schema["version"],
            attributes=schema["attrNames"],
            state=SchemaRecord.STATE_WRITTEN,
            author=SchemaRecord.AUTHOR_OTHER,
        )
        await schema_record.save(session, reason="Retrieved from ledger")

        schema_msg = Schema(**schema_record.serialize())
        schema_msg.assign_thread_from(context.message)
        await responder.send_reply(schema_msg)


SchemaGetList, SchemaGetListSchema = generate_model_schema(
    name="SchemaGetList",
    handler="acapy_plugin_toolbox.schemas.SchemaGetListHandler",
    msg_type=SCHEMA_GET_LIST,
    schema={},
)

SchemaList, SchemaListSchema = generate_model_schema(
    name="SchemaList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=SCHEMA_LIST,
    schema={"results": fields.List(fields.Nested(SchemaRecordSchema), required=True)},
)


class SchemaGetListHandler(BaseHandler):
    """Handler for get schema list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get schema list request."""
        session = await context.session()
        records = await SchemaRecord.query(session, {})
        schema_list = SchemaList(results=records)
        schema_list.assign_thread_from(context.message)
        await responder.send_reply(schema_list)
