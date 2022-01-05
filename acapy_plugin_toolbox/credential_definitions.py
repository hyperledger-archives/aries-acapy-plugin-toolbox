"""Define messages for credential definitions admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

import logging
from asyncio import ensure_future, shield

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.indy.issuer import IndyIssuer
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.credential_definitions.routes import (
    add_cred_def_non_secrets_record,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.messaging.util import canon
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

from aries_cloudagent.revocation.error import (
    RevocationError,
    RevocationNotSupportedError,
)
from aries_cloudagent.revocation.indy import IndyRevocation
from aries_cloudagent.tails.base import BaseTailsServer

from aries_cloudagent.messaging.valid import INDY_REV_REG_SIZE

from .schemas import SchemaRecord
from .util import admin_only, generate_model_schema

PROTOCOL = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-credential-definitions/0.1"

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

    REVOCATION_SUPPORTED = True
    REVOCATION_UNSUPPORTED = False

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
        support_revocation: bool = False,
        revocation_registry_size: int = None,
        **kwargs,
    ):
        """Initialize a new SchemaRecord."""
        super().__init__(record_id, state or self.STATE_UNWRITTEN, **kwargs)
        self.cred_def_id = cred_def_id
        self.schema_id = schema_id
        self.attributes = attributes
        self.author = author
        self.support_revocation = support_revocation
        self.revocation_registry_size = revocation_registry_size

    @property
    def record_id(self) -> str:
        """Accessor for this schema's id."""
        return self._id

    @property
    def record_value(self) -> dict:
        """Get record value."""
        return {
            "attributes": self.attributes,
            "support_revocation": self.support_revocation,
            "revocation_registry_size": self.revocation_registry_size,
        }

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
    support_revocation = fields.Bool(required=False, missing=False)
    revocation_registry_size = fields.Int(required=False)


SendCredDef, SendCredDefSchema = generate_model_schema(
    name="SendCredDef",
    handler="acapy_plugin_toolbox.credential_definitions" ".SendCredDefHandler",
    msg_type=SEND_CRED_DEF,
    schema={
        "schema_id": fields.Str(required=True),
        "support_revocation": fields.Bool(required=False, missing=False),
        "revocation_registry_size": fields.Int(
            required=False, strict=True, **INDY_REV_REG_SIZE
        ),
    },
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
        support_revocation: bool = context.message.support_revocation
        revocation_registry_size: int = None

        if support_revocation:
            revocation_registry_size = context.message.revocation_registry_size
            if revocation_registry_size is None:
                report = ProblemReport(
                    description={
                        "en": "Failed to create revokable credential definition; Error: revocation_registry_size not specified"
                    },
                    who_retries="none",
                )
                LOGGER.warning(
                    "revocation_registry_size not specified while creating revokable credential definition"
                )
                await responder.send_reply(report)
                return
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
                credential_definition_id, _, novel = await shield(
                    ledger.create_and_send_credential_definition(
                        issuer,
                        context.message.schema_id,
                        tag="{}_{}".format(
                            schema_record.schema_name, schema_record.schema_version
                        ),
                        support_revocation=support_revocation,
                    )
                )
                issuer_did = credential_definition_id.split(":")[0]
                await add_cred_def_non_secrets_record(
                    context.profile,
                    context.message.schema_id,
                    issuer_did,
                    credential_definition_id,
                )

        except Exception as err:
            report = ProblemReport(
                description={"en": "Failed to send to ledger; Error: {}".format(err)},
                who_retries="none",
            )
            LOGGER.exception("Failed to send cred def to ledger: %s", err)
            await responder.send_reply(report)
            return

        # If revocation is requested and cred def is novel, create revocation registry
        if support_revocation and novel:
            profile = context.profile
            tails_base_url = profile.settings.get("tails_server_base_url")
            if not tails_base_url:
                report = ProblemReport(
                    description={
                        "en": "Failed to contact Revocation Registry (Not Configured)"
                    },
                    who_retries="none",
                )
                LOGGER.exception("tails_server_base_url not configured")
                await responder.send_reply(report)
                return
            try:
                # Create registry
                revoc = IndyRevocation(profile)
                registry_record = await revoc.init_issuer_registry(
                    credential_definition_id,
                    max_cred_num=revocation_registry_size,
                )

            except RevocationNotSupportedError as e:
                report = ProblemReport(
                    description={"en": "Failed to initialize Revocation Registry"},
                    who_retries="none",
                )
                LOGGER.exception("init_issuer_registry failed: %s", e)
                await responder.send_reply(report)
                return
            await shield(registry_record.generate_registry(profile))
            try:
                await registry_record.set_tails_file_public_uri(
                    profile, f"{tails_base_url}/{registry_record.revoc_reg_id}"
                )
                await registry_record.send_def(profile)
                await registry_record.send_entry(profile)

                # stage pending registry independent of whether tails server is OK
                pending_registry_record = await revoc.init_issuer_registry(
                    registry_record.cred_def_id,
                    max_cred_num=registry_record.max_cred_num,
                )
                ensure_future(
                    pending_registry_record.stage_pending_registry(
                        profile, max_attempts=16
                    )
                )

                tails_server = profile.inject(BaseTailsServer)
                (upload_success, reason) = await tails_server.upload_tails_file(
                    profile,
                    registry_record.revoc_reg_id,
                    registry_record.tails_local_path,
                    interval=0.8,
                    backoff=-0.5,
                    max_attempts=5,  # heuristic: respect HTTP timeout
                )
                if not upload_success:
                    report = ProblemReport(
                        description={
                            "en": f"Tails file for rev reg {registry_record.revoc_reg_id} failed to upload: {reason}"
                        },
                        who_retries="none",
                    )
                    LOGGER.exception(
                        f"Tails file for rev reg {registry_record.revoc_reg_id} failed to upload: {reason}"
                    )
                    await responder.send_reply(report)
                    return

            except RevocationError as e:
                report = ProblemReport(
                    description={
                        "en": "Error occurred while setting up revocation registry"
                    },
                    who_retries="none",
                )
                LOGGER.exception(
                    "Error occurred while setting up revocation registry: %s", e
                )
                await responder.send_reply(report)
                return

        # we may not need to save the record as below
        cred_def_record = CredDefRecord(
            cred_def_id=credential_definition_id,
            schema_id=context.message.schema_id,
            attributes=list(map(canon, schema_record.attributes)),
            state=CredDefRecord.STATE_WRITTEN,
            author=CredDefRecord.AUTHOR_SELF,
            support_revocation=support_revocation,
            revocation_registry_size=revocation_registry_size,
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
