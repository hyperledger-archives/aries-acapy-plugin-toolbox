"""Define messages for credential definitions admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import logging
from asyncio import shield

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.indy.issuer import IndyIssuer
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.util import canon
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from .schemas import SchemaRecord
from .util import admin_only, generate_model_schema

PROTOCOL = "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-credential-definitions/0.1"

SEND_CRED_DEF = "{}/send-credential-definition".format(PROTOCOL)
CRED_DEF_ID = "{}/credential-definition-id".format(PROTOCOL)
CRED_DEF_GET = "{}/credential-definition-get".format(PROTOCOL)
CRED_DEF = "{}/credential-definition".format(PROTOCOL)
CRED_DEF_GET_LIST = "{}/credential-definition-get-list".format(PROTOCOL)
CRED_DEF_LIST = "{}/credential-definition-list".format(PROTOCOL)

MESSAGE_TYPES = {
    SEND_CRED_DEF: "acapy_plugin_toolbox.credential_definitions.SendCredDef",
    CRED_DEF_ID: "acapy_plugin_toolbox.credential_definitions.CredDefID",
    CRED_DEF_GET: "acapy_plugin_toolbox.credential_definitions.CredDefGet",
    CRED_DEF: "acapy_plugin_toolbox.credential_definitions.CredDef",
    CRED_DEF_GET_LIST: "acapy_plugin_toolbox.credential_definitions.CredDefGetList",
    CRED_DEF_LIST: "acapy_plugin_toolbox.credential_definitions.CredDefList",
}

LOGGER = logging.getLogger(__name__)


async def setup(session: ProfileSession, protocol_registry: ProblemReport = None):
    """Setup the cred def plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


class CredDefRecord(BaseRecord):
    """Represents a Schema."""

    RECORD_ID_NAME = "record_id"
    RECORD_TYPE = "cred_def"

    AUTHOR_SELF = "self"
    AUTHOR_OTHER = "other"

    STATE_UNWRITTEN = "unwritten"
    STATE_WRITTEN = "written"

    class Meta:
        """CredDefRecord metadata."""

        schema_class = "CredDefRecordSchema"

    def __init__(
        self,
        *,
        record_id: str = None,
        cred_def_id: str = None,
        schema_id: str = None,
        attributes: [str] = None,
        author: str = None,
        state: str = None,
        **kwargs
    ):
        """Initialize a new SchemaRecord."""
        super().__init__(record_id, state or self.STATE_UNWRITTEN, **kwargs)
        self.cred_def_id = cred_def_id
        self.schema_id = schema_id
        self.attributes = attributes
        self.author = author

    @property
    def record_id(self) -> str:
        """Accessor for this schema's id."""
        return self._id

    @property
    def record_value(self) -> dict:
        """Get record value."""
        return {"attributes": self.attributes}

    @property
    def record_tags(self) -> dict:
        """Get tags for record."""
        return {
            prop: getattr(self, prop)
            for prop in ("cred_def_id", "schema_id", "state", "author")
        }

    @classmethod
    async def retrieve_by_cred_def_id(
        cls, session: ProfileSession, cred_def_id: str
    ) -> "CredDefRecord":
        """Retrieve a schema record by cred_def_id."""
        return await cls.retrieve_by_tag_filter(session, {"cred_def_id": cred_def_id})


class CredDefRecordSchema(BaseRecordSchema):
    """Schema to allow serialization/deserialization of Schema records."""

    class Meta:
        """PoolRecordSchema metadata."""

        model_class = CredDefRecord

    cred_def_id = fields.Str(required=False)
    schema_id = fields.Str(required=False)
    attributes = fields.List(fields.Str(), required=False)
    author = fields.Str(required=False)


SendCredDef, SendCredDefSchema = generate_model_schema(
    name="SendCredDef",
    handler="acapy_plugin_toolbox.credential_definitions" ".SendCredDefHandler",
    msg_type=SEND_CRED_DEF,
    schema={"schema_id": fields.Str(required=True)},
)

CredDefID, CredDefIDSchema = generate_model_schema(
    name="CredDefID",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=CRED_DEF_ID,
    schema={"cred_def_id": fields.Str(required=True)},
)


class SendCredDefHandler(BaseHandler):
    """Handler for received send cred def request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received send cred def request."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        issuer: IndyIssuer = session.inject(IndyIssuer)
        # If no schema record, make one
        try:
            schema_record = await SchemaRecord.retrieve_by_schema_id(
                session, schema_id=context.message.schema_id
            )
        except StorageNotFoundError:
            # Schema will be cached so retrieving here is not
            # any less efficient (schema is retrieved in
            # send_credential_definition).
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

        try:
            async with ledger:
                credential_definition_id, *_ = await shield(
                    ledger.create_and_send_credential_definition(
                        issuer,
                        context.message.schema_id,
                        tag="{}_{}".format(
                            schema_record.schema_name, schema_record.schema_version
                        ),
                    )
                )
        except Exception as err:
            report = ProblemReport(
                description={"en": "Failed to send to ledger; Error: {}".format(err)},
                who_retries="none",
            )
            LOGGER.exception("Failed to send cred def to ledger: %s", err)
            await responder.send_reply(report)
            return

        # we may not need to save the record as below
        cred_def_record = CredDefRecord(
            cred_def_id=credential_definition_id,
            schema_id=context.message.schema_id,
            attributes=list(map(canon, schema_record.attributes)),
            state=CredDefRecord.STATE_WRITTEN,
            author=CredDefRecord.AUTHOR_SELF,
        )
        await cred_def_record.save(
            session, reason="Committed credential definition to ledger"
        )

        result = CredDefID(cred_def_id=credential_definition_id)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


CredDefGet, CredDefGetSchema = generate_model_schema(
    name="CredDefGet",
    handler="acapy_plugin_toolbox.credential_definitions" ".CredDefGetHandler",
    msg_type=CRED_DEF_GET,
    schema={"cred_def_id": fields.Str(required=True)},
)

CredDef, CredDefSchema = generate_model_schema(
    name="CredDef",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=CRED_DEF,
    schema=CredDefRecordSchema,
)


class CredDefGetHandler(BaseHandler):
    """Handler for cred def get requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received cred def get requests."""
        session = await context.session()
        try:
            cred_def_record = await CredDefRecord.retrieve_by_cred_def_id(
                session, context.message.cred_def_id
            )
            cred_def = CredDef(**cred_def_record.serialize())
            cred_def.assign_thread_from(context.message)
            await responder.send_reply(cred_def)
            return
        except StorageNotFoundError:
            pass

        ledger: BaseLedger = session.inject(BaseLedger)
        async with ledger:
            credential_definition = await ledger.get_credential_definition(
                context.message.cred_def_id
            )
            schema_id = await ledger.credential_definition_id2schema_id(
                credential_definition["id"]
            )

        try:
            schema_record = await SchemaRecord.retrieve_by_schema_id(session, schema_id)
        except StorageNotFoundError:
            # This may be less efficient
            async with ledger:
                schema = await ledger.get_schema(schema_id)

            schema_record = SchemaRecord(
                schema_id=schema["id"],
                schema_name=schema["name"],
                schema_version=schema["version"],
                attributes=schema["attrNames"],
                state=SchemaRecord.STATE_WRITTEN,
                author=SchemaRecord.AUTHOR_OTHER,
            )
            await schema_record.save(session, reason="Retrieved from ledger")

        cred_def_record = CredDefRecord(
            cred_def_id=credential_definition["id"],
            schema_id=schema_record.schema_id,
            attributes=list(map(canon, schema_record.attributes)),
            state=CredDefRecord.STATE_WRITTEN,
            author=CredDefRecord.AUTHOR_OTHER,
        )
        await cred_def_record.save(session, reason="Retrieved from ledger")

        cred_def = CredDef(**cred_def_record.serialize())
        cred_def.assign_thread_from(context.message)
        await responder.send_reply(cred_def)


CredDefGetList, CredDefGetListSchema = generate_model_schema(
    name="CredDefGetList",
    handler="acapy_plugin_toolbox.credential_definitions" ".CredDefGetListHandler",
    msg_type=CRED_DEF_GET_LIST,
    schema={},
)

CredDefList, CredDefListSchema = generate_model_schema(
    name="CredDefList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=CRED_DEF_LIST,
    schema={"results": fields.List(fields.Nested(CredDefRecordSchema), required=True)},
)


class CredDefGetListHandler(BaseHandler):
    """Handler for get schema list request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get schema list request."""
        session = await context.session()
        records = await CredDefRecord.query(session, {})
        cred_def_list = CredDefList(results=records)
        cred_def_list.assign_thread_from(context.message)
        await responder.send_reply(cred_def_list)
