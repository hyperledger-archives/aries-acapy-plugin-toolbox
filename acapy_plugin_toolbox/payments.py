"""Payment plugin."""
from ctypes import cdll
import json
import os
import platform

from marshmallow import Schema, fields
from indy import ledger, payment

from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.config.injection_context import InjectionContext
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.protocols.problem_report.message import ProblemReport
from aries_cloudagent.wallet.base import BaseWallet
from .util import generate_model_schema

# TODO: Find a better way to find the library
LIBRARY = os.environ.get('LIBSOVTOKEN', 'libsovtoken.so')
# LIBRARY = 'libsovtoken'
EXTENSION = {
    "darwin": ".dylib",
    "linux": ".so",
    "win32": ".dll",
    'windows': '.dll'
}


PROTOCOL_URI = (
    'https://github.com/hyperledger/aries-toolbox/'
    'tree/master/docs/admin-payments/0.1'
)

GET_ADDRESS_LIST = f'{PROTOCOL_URI}/get-address-list'
ADDRESS_LIST = f'{PROTOCOL_URI}/address-list'
CREATE_ADDRESS = f'{PROTOCOL_URI}/create-address'
ADDRESS = f'{PROTOCOL_URI}/address'
TRANSFER = f'{PROTOCOL_URI}/transfer'
TRANSFER_COMPLETE = f'{PROTOCOL_URI}/transfer-complete'

MESSAGE_TYPES = {
    GET_ADDRESS_LIST: 'acapy_plugin_toolbox.payments.GetAddressList',
    ADDRESS_LIST: 'acapy_plugin_toolbox.payments.AddressList',
    CREATE_ADDRESS: 'acapy_plugin_toolbox.payments.CreateAddress',
    ADDRESS: 'acapy_plugin_toolbox.payments.Address',
    TRANSFER: 'acapy_plugin_toolbox.payments.Transfer',
    TRANSFER_COMPLETE: 'acapy_plugin_toolbox.payments.TransferComplete',
}


def file_ext():
    """Determine extension for system."""
    your_platform = platform.system().lower()
    return EXTENSION[your_platform] if (your_platform in EXTENSION) else '.so'


async def setup(
        context: InjectionContext,
        protocol_registry: ProblemReport = None
):
    """Load plugin."""

    # Load in libsovtoken
    cdll.LoadLibrary(LIBRARY).sovtoken_init()

    if not protocol_registry:
        protocol_registry = await context.inject(ProtocolRegistry)
    protocol_registry.register_message_types(
        MESSAGE_TYPES
    )


GetAddressList, GetAddressListSchema = generate_model_schema(
    name='GetAddressList',
    handler='acapy_plugin_toolbox.payments.GetAddressListHandler',
    msg_type=GET_ADDRESS_LIST,
    schema={}
)

BasePaymentAddressSchema = Schema.from_dict({
    'address': fields.Str(required=True),
    'method': fields.Str(required=True),
    'balance': fields.Float(required=True),
    'raw_repr': fields.Dict(required=False)
})

AddressList, AddressListSchema = generate_model_schema(
    name='AddressList',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=ADDRESS_LIST,
    schema={
        'address': fields.List(
            fields.Nested(BasePaymentAddressSchema),
            required=True
        )
    }
)

CreateAddress, CreateAddressSchema = generate_model_schema(
    name='CreateAddress',
    handler='acapy_plugin_toolbox.payments.CreateAddressHandler',
    msg_type=CREATE_ADDRESS,
    schema={
        'seed': fields.Str(required=False),
        'method': fields.Str(required=True)
    }
)

Address, AddressSchema = generate_model_schema(
    name='Address',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=ADDRESS,
    schema=BasePaymentAddressSchema
)

Transfer, TransferSchema = generate_model_schema(
    name='Transfer',
    handler='acapy_plugin_toolbox.payments.TransferHandler'
    msg_type=TRANSFER,
    schema={
        'from_address': fields.List(fields.Nested(BasePaymentAddressSchema)),
        'to_address': fields.List(fields.Nested(BasePaymentAddressSchema)),
        'amount': fields.Float(required=True)
        'raw_repr': fields.Str(required=False)
    }
)

BaseReceiptSchema = Schema.from_dict({
    'receipt': fields.Str(required=True), # receipt that can be used for payment referencing and verification
    'recipient': fields.Str(required=True), # payment address of recipient
    'amount': fields.Float(required=True),
    'extra': fields.Str(required=False) # optional data from payment transaction
})

TransferComplete, TransferCompleteSchema = generate_model_schema(
    name='TransferComplete',
    handler='acapy_plugin_toolbox.payments.TransferCompleteHandler',
    msg_type=TRANSFER_COMPLETE,
    schema={
        'receipt': fields.List(
            fields.Nested(BaseReceiptSchema),
            required=True
        )
    }

class CreateAddressHandler(BaseHandler):
    """Handler for received create address requests."""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received create address requests."""
        wallet: BaseWallet = await context.inject(BaseWallet)
        if context.message.method != 'sov':
            report = ProblemReport(
                explain_ltxt=(
                    'Method {} is not supported.'
                    .format(context.message.method),
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        address_str = await payment.create_payment_address(
            wallet.handle,
            'sov',
            json.dumps({
                'seed': context.message.seed
            })
        )

        address = Address(
            address=address_str,
            method='sov',
            balance=0,
        )
        address.assign_thread_from(context.message)
        await responder.send_reply(address)
        return

class TransferHandler(BaseHandler):
    """Handler for payment"""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle payment"""
        wallet BaseWallet = await context.inject(BaseWallet)
        ledger: BaseLedger = await context.inject(BaseLedger)
        if context.message.method != 'sov':
            report = ProblemReport(
                explain_ltxt=(
                    'Method {} is not supported.'
                    .format(context.message.method),
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return
        # get fees from ledger
        xfer_fee = 0
        xfer_fee_req = await payment.build_get_txn_fees_req(wallet.handle, None, 'sov')
        xfer_fee_resp = await ledger.sign_and_submit_request(pool_handle, steward_wallet_handle, steward_did, xfer_fee_req)
        parse_xfer_fee = await payment.parse_get_txn_fees_response(PAYMENT_METHOD, xfer_fee_resp)
        #parse_xfer_fee_json = json.loads(parse_xfer_fee)
        auth_rule_req = await ledger.build_get_auth_rule_request(steward_did, "10001", "ADD", "*", None, "*")
        auth_rule_resp = await ledger.sign_and_submit_request(pool_handle, steward_wallet_handle, steward_did, auth_rule_req)
        #auth_rule_resp_json = json.loads(auth_rule_resp)
        xfer_auth_fee_resp = await payment.get_request_info(auth_rule_resp, '{ "sig_count" : 1 }', parse_xfer_fee) # { "sig_count" : 1 }
        xfer_auth_fee_resp_json = json.loads(xfer_auth_fee_resp)
        xfer_fee = xfer_auth_fee_resp_json["price"]
        try:
            async with ledger:
                credential_definition_id = await shield(
                    ledger.(
                        context.message.schema_id,
                        tag='{}_{}'.format(
                            schema_record.schema_name,
                            schema_record.schema_version
                        )
                    )
                )
        except Exception as err:
            report = ProblemReport(
                explain_ltxt='Failed to send to ledger; Error: {}'.format(err),
                who_retries='none'
            )
            await responder.send_reply(report)
            return

    # get payment address's sources
    # build outputs
    # Build TAA for extras
        ''' 
        param outputs_json: The list of outputs as json array:
        [{
            recipient: <str>, // payment address of recipient
            amount: <int>, // amount
        }]
        '''
     xfer_fee):
    utctimestamp = int(datetime.datetime.utcnow().timestamp())
    logger.debug("Before getting all token sources")
    token_sources = await getTokenSources(pool_handle, wallet_handle, steward_did, source_payment_address)
    logging.debug(token_sources)
    if len(token_sources) == 0:
        logging.debug("Gothere4")
        err = Exception("No token sources found for source payment address %s" % source_payment_address)
        err.status_code = 400
        logging.error(err)
        raise err
    target_tokens_amount = target_tokens_amount or DEFAULT_TOKENS_AMOUNT
    token_sources, remaining_tokens_amount = getSufficientTokenSources(token_sources, target_tokens_amount, xfer_fee)
    inputs = token_sources
    outputs = [
        {"recipient": target_payment_address, "amount": target_tokens_amount},
        {"recipient": source_payment_address, "amount": remaining_tokens_amount}
    ]

    taa_req = await ledger.build_get_txn_author_agreement_request(steward_did, None)
    taa_resp_json = await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, taa_req)
    taa_resp=json.loads(taa_resp_json)

    if taa_resp["result"]["data"]:
        extras = await payment.prepare_payment_extra_with_acceptance_data(None, taa_resp["result"]["data"]["text"], taa_resp["result"]["data"]["version"], None, 'service_agreement', utctimestamp)
    else:
        extras = None

    inputs = 
    payment_req, payment_method = await payment.build_payment_req(
        wallet.handle, 
        None,
        json.dumps(inputs),
        json.dumps(outputs),
        extras)
    #payment_resp = await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, payment_req)
    receipts = await payment.parse_payment_response(payment_method, payment_resp)did