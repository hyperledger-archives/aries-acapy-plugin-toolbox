"""Transaction Author Agreement acceptance plugin."""
# pylint: disable=invalid-name, too-few-public-methods

from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from marshmallow import fields
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.protocols.problem_report.message import ProblemReport

from .util import (
    generate_model_schema, admin_only
)

PROTOCOL_URI = "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin_taa/0.1"
GET = f"{PROTOCOL_URI}/get"
TAA = f"{PROTOCOL_URI}/taa"
ACCEPT = f"{PROTOCOL_URI}/accept"
ACCEPTED = f"{PROTOCOL_URI}/accepted"

MESSAGE_TYPES = {
    GET: 'acapy_plugin_toolbox.taa.Get',
    TAA: 'acapy_plugin_toolbox.taa.Taa',
    ACCEPT: 'acapy_plugin_toolbox.taa.Accept',
    ACCEPTED: 'acapy_plugin_toolbox.taa.Accepted'
}


async def setup(context: InjectionContext):
    """Setup the basicmessage plugin."""
    protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


Get, GetSchema = generate_model_schema(
    name='Get',
    handler='acapy_plugin_toolbox.taa.GetHandler',
    msg_type=GET,
    schema={}
)


Taa, TaaSchema = generate_model_schema(
    name='Taa',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=TAA,
    schema={
        'version': fields.Str(
            required=True,
            description="Version of Transaction Author Agreement",
        ),
        'text': fields.Str(
            required=True,
            description="Transaction Author Agreement text"
        ),
        'accepted': fields.Bool(
            required=True,
            description="A record of acceptance of this version of the TAA exists."
        )
    }
)


class GetHandler(BaseHandler):
    """Handler for received get request."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received get request."""
        ledger: BaseLedger = await context.inject(BaseLedger, required=False)
        if not ledger or ledger.LEDGER_TYPE != 'indy':
            report = ProblemReport(
                explain_ltxt='Invalid ledger.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        taa_info = await ledger.get_txn_author_agreement()
        result = Taa(
            version=taa_info['taa_record']['version'],
            text=taa_info['taa_record']['text'],
            accepted=(not taa_info['taa_required'])
        )
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


Accept, AcceptSchema = generate_model_schema(
    name='Accept',
    handler='acapy_plugin_toolbox.taa.AcceptHandler',
    msg_type=ACCEPT,
    schema={
        'version': fields.Str(
            required=True,
            description='Version of accepted TAA.'
        ),
        'text': fields.Str(
            required=True,
            description='Text of accepted TAA.'
        ),
        'acceptance_mechanism': fields.Str(
            required=False,
            description='The mechanism used to accept the TAA.',
            missing='wallet_agreement',
        )
    }
)

Accepted, AcceptedSchema = generate_model_schema(
    name='Accepted',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=ACCEPTED,
    schema={}
)


class AcceptHandler(BaseHandler):
    """Handler for taa acceptance messages."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle taa acceptance messages."""
        ledger: BaseLedger = await context.inject(BaseLedger, required=False)
        if not ledger or ledger.LEDGER_TYPE != 'indy':
            report = ProblemReport(
                explain_ltxt='Invalid ledger.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        taa_record = {
            'version': context.message.version,
            'text': context.message.text,
            'digest': ledger.taa_digest(
                context.message.version, context.message.text
            )
        }
        try:
            await ledger.accept_txn_author_agreement(
                taa_record,
                context.message.acceptance_mechanism
            )
        except Exception as err:
            report = ProblemReport(
                explain_ltxt='An error occured while attempting to accept'
                ' the Transaction Author Agreement: {}'.format(
                    err
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        result = Accepted()
        result.assign_thread_from(context.message)
        await responder.send_reply(result)
