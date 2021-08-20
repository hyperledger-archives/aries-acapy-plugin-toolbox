"""Transaction Author Agreement acceptance plugin."""
# pylint: disable=invalid-name, too-few-public-methods

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from marshmallow import fields
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport

from .util import generate_model_schema, admin_only

PROTOCOL_URI = (
    "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-taa/0.1"
)
GET = f"{PROTOCOL_URI}/get"
TAA = f"{PROTOCOL_URI}/taa"
ACCEPT = f"{PROTOCOL_URI}/accept"
ACCEPTED = f"{PROTOCOL_URI}/accepted"
GET_ACCEPTANCE = f"{PROTOCOL_URI}/get-acceptance"
ACCEPTANCE = f"{PROTOCOL_URI}/acceptance"

MESSAGE_TYPES = {
    GET: "acapy_plugin_toolbox.taa.Get",
    TAA: "acapy_plugin_toolbox.taa.Taa",
    ACCEPT: "acapy_plugin_toolbox.taa.Accept",
    ACCEPTED: "acapy_plugin_toolbox.taa.Accepted",
    GET_ACCEPTANCE: "acapy_plugin_toolbox.taa.GetAcceptance",
    ACCEPTANCE: "acapy_plugin_toolbox.taa.Acceptance",
}


async def setup(session: ProfileSession, protocol_registry: ProblemReport = None):
    """Setup the basicmessage plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


Get, GetSchema = generate_model_schema(
    name="Get", handler="acapy_plugin_toolbox.taa.GetHandler", msg_type=GET, schema={}
)


Taa, TaaSchema = generate_model_schema(
    name="Taa",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=TAA,
    schema={
        "version": fields.Str(
            required=True, description="Version of Transaction Author Agreement"
        ),
        "text": fields.Str(
            required=True, description="Transaction Author Agreement text"
        ),
        "needed": fields.Bool(
            required=True,
            description="Acceptance is needed before making ledger writes.",
        ),
    },
)


class GetHandler(BaseHandler):
    """Handler for received get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get request."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        if not ledger or ledger.BACKEND_NAME != "indy":
            report = ProblemReport(
                description={"en": "Invalid ledger."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        async with ledger:
            taa_info = await ledger.get_txn_author_agreement()
            acceptance = await ledger.get_latest_txn_author_acceptance()

        if taa_info["taa_required"] and not acceptance:
            needed = True
        elif acceptance and acceptance["digest"] != taa_info["taa_record"]["digest"]:
            needed = True
        else:
            needed = False

        result = Taa(
            version=taa_info["taa_record"]["version"],
            text=taa_info["taa_record"]["text"],
            needed=needed,
        )
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


Accept, AcceptSchema = generate_model_schema(
    name="Accept",
    handler="acapy_plugin_toolbox.taa.AcceptHandler",
    msg_type=ACCEPT,
    schema={
        "version": fields.Str(required=True, description="Version of accepted TAA."),
        "text": fields.Str(required=True, description="Text of accepted TAA."),
        "mechanism": fields.Str(
            required=False,
            description="The mechanism used to accept the TAA.",
            missing="wallet_agreement",
        ),
    },
)

Accepted, AcceptedSchema = generate_model_schema(
    name="Accepted",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ACCEPTED,
    schema={},
)


class AcceptHandler(BaseHandler):
    """Handler for taa acceptance messages."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle taa acceptance messages."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        if not ledger or ledger.BACKEND_NAME != "indy":
            report = ProblemReport(
                description={"en": "Invalid ledger."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        taa_record = {
            "version": context.message.version,
            "text": context.message.text,
            "digest": ledger.taa_digest(context.message.version, context.message.text),
        }
        try:
            async with ledger:
                await ledger.accept_txn_author_agreement(
                    taa_record, context.message.mechanism
                )
        except Exception as err:
            report = ProblemReport(
                description={
                    "en": "An error occured while attempting to accept"
                    " the Transaction Author Agreement: {}".format(err)
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        result = Accepted()
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


GetAcceptance, GetAcceptanceSchema = generate_model_schema(
    name="GetAcceptance",
    handler="acapy_plugin_toolbox.taa.GetAcceptanceHandler",
    msg_type=GET_ACCEPTANCE,
    schema={},
)


Acceptance, AcceptanceSchema = generate_model_schema(
    name="Acceptance",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ACCEPTANCE,
    schema={
        "needed": fields.Bool(required=True, description="Acceptance needed."),
        "version": fields.Str(required=False, description="Version of accepted TAA."),
        "time": fields.Str(required=False, description="Time of acceptance."),
        "mechanism": fields.Str(
            required=False, description="The mechanism used to accept the TAA."
        ),
    },
)


class GetAcceptanceHandler(BaseHandler):
    """Handler for received get acceptance request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get acceptance request."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        if not ledger or ledger.BACKEND_NAME != "indy":
            report = ProblemReport(
                description={"en": "Invalid ledger."}, who_retries="none"
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        async with ledger:
            taa_info = await ledger.get_txn_author_agreement()
            acceptance = await ledger.get_latest_txn_author_acceptance()

        if taa_info["taa_required"] and not acceptance:
            needed = True
        elif acceptance and acceptance["digest"] != taa_info["taa_record"]["digest"]:
            needed = True
        else:
            needed = False

        result = Acceptance(
            needed=needed,
            version=acceptance.get("version"),
            time=acceptance.get("time"),
            mechanism=acceptance.get("mechanism"),
        )
        result.assign_thread_from(context.message)
        await responder.send_reply(result)
