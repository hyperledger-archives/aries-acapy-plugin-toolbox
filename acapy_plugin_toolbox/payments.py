"""Payment plugin."""
from ctypes import cdll
import json
import os
import platform
from functools import reduce
from typing import Dict

from marshmallow import Schema, fields
from indy import payment
from indy import ledger as indy_ledger

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
SOV_METHOD = 'sov'
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
GET_FEES = f'{PROTOCOL_URI}/get-fees'
FEES = f'{PROTOCOL_URI}/fees'
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

GetFees, GetFeesSchema = generate_model_schema(
    name='GetFees',
    handler='acapy_plugin_toolbox.payments.GetFeesHandler',
    msg_type=GET_FEES,
    schema={
        'method': fields.Str(required=True),
        'amount': fields.Float(required=False)
    }
)

Fees, FeesSchema = generate_model_schema(
    name='Fees',
    handler='acapy_plugin_toolbox.util.PassHandler',
    msg_type=FEES,
    schema={
        'total': fields.Float(required=True)
    }
)

Transfer, TransferSchema = generate_model_schema(
    name='Transfer',
    handler='acapy_plugin_toolbox.payments.TransferHandler',
    msg_type=TRANSFER,
    schema={
        'method': fields.Str(required=True),
        'from_address': fields.Str(required=True),
        'to_address': fields.Str(required=True),
        'amount': fields.Float(required=True)
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
        'from_address': fields.Str(required=True),
        'to_address': fields.Str(required=True),
        'amount': fields.Float(required=True),
        'raw_repr': fields.Dict(required=False)
    }
)


async def get_sources(ledger: BaseLedger, payment_address: str):
    """Retrieve sources for this payment address and asynchrounsly generate."""
    # We need to use ledger._submit
    # pylint: disable=protected-access
    next_seqno = -1
    while True:
        get_sources_json, method = \
            await payment.build_get_payment_sources_with_from_request(
                ledger.wallet.handle,
                None,
                payment_address,
                next_seqno
            )

        resp = await ledger._submit(get_sources_json, sign=False)
        source_list, next_seqno = \
            await payment.parse_get_payment_sources_with_from_response(
                method, resp
            )
        sources = json.loads(source_list)
        for source in sources:
            yield source
        if next_seqno == -1:
            break


async def get_balance(ledger: BaseLedger, payment_address: str):
    """Return the balance of a payment address."""
    sources = [source async for source in get_sources(ledger, payment_address)]

    return reduce(lambda acc, source: acc + source['amount'], sources, 0)


class CreateAddressHandler(BaseHandler):
    """Handler for received create address requests."""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received create address requests."""
        wallet: BaseWallet = await context.inject(BaseWallet)
        ledger: BaseLedger = await context.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                explain_ltxt=(
                    'Method "{}" is not supported.'
                    .format(context.message.method)
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        address_str = await payment.create_payment_address(
            wallet.handle,
            SOV_METHOD,
            json.dumps({
                'seed': context.message.seed
            })
        )

        async with ledger:
            balance = await get_balance(ledger, address_str)

        address = Address(
            address=address_str,
            method=SOV_METHOD,
            balance=balance,
        )
        address.assign_thread_from(context.message)
        await responder.send_reply(address)
        return


async def prepare_extra(ledger: BaseLedger, extra: Dict):
    """Prepare extras field for submission of payment request."""
    extra_json = json.dumps(extra)
    print(extra_json)
    acceptance = await ledger.get_latest_txn_author_acceptance()
    if acceptance:
        extra_json = await (
            indy_ledger.append_txn_author_agreement_acceptance_to_request(
                extra_json,
                acceptance["text"],
                acceptance["version"],
                acceptance["digest"],
                acceptance["mechanism"],
                acceptance["time"],
            )
        )
    print(extra_json)
    return extra_json


async def fetch_transfer_auth(ledger: BaseLedger):
    """Retrieve token transfer fee."""
    # We need to use ledger._submit
    # pylint: disable=protected-access
    xfer_fee_resp = await ledger._submit(await payment.build_get_txn_fees_req(
        ledger.wallet.handle,
        None,
        SOV_METHOD
    ), sign=False)
    parse_xfer_fee = await payment.parse_get_txn_fees_response(
        SOV_METHOD, xfer_fee_resp
    )

    auth_rule_resp = await ledger._submit(
        await indy_ledger.build_get_auth_rule_request(
            None, "10001", "ADD", "*", None, "*"
        ),
        sign=False
    )
    xfer_auth_fee = json.loads(
        await payment.get_request_info(
            auth_rule_resp,
            json.dumps({'sig_count': 1}),
            parse_xfer_fee
        )
    )
    if ledger.cache:
        await ledger.cache.set(
            ['admin-payments::xfer_auth'],
            xfer_auth_fee,
            ledger.cache_duration,
        )
    return xfer_auth_fee


async def get_transfer_auth(ledger: BaseLedger):
    """Retrieve token transfer fee."""
    if ledger.cache:
        result = await ledger.cache.get(f"admin-payments::xfer_auth")
        if result:
            return result

    return await fetch_transfer_auth(ledger)


class GetFeesHandler(BaseHandler):
    """Handler for get fees."""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get fees."""
        ledger: BaseLedger = await context.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                explain_ltxt=(
                    'Method "{}" is not supported.'
                    .format(context.message.method)
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        async with ledger:
            xfer_auth = await get_transfer_auth(ledger)

        fees = Fees(total=xfer_auth['price'])
        fees.assign_thread_from(context.message)
        await responder.send_reply(fees)


class TransferHandler(BaseHandler):
    """Handler for payment"""

    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle payment"""
        # We need to use ledger._submit
        # pylint: disable=protected-access
        wallet: BaseWallet = await context.inject(BaseWallet)
        ledger: BaseLedger = await context.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                explain_ltxt=(
                    'Method "{}" is not supported.'
                    .format(context.message.method)
                ),
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        # get fees from ledger
        async with ledger:
            try:
                fee = (await get_transfer_auth(ledger))['price']
            except Exception as err:
                report = ProblemReport(
                    explain_ltxt=(
                        'Failed to retrieve fees from the ledger'
                        '; Error: {}'.format(err)
                    ),
                    who_retries='none'
                )
                await responder.send_reply(report)
                return

        # Sources look like:
        #     [{
        #       source: <str>, // source input
        #       paymentAddress: <str>, //payment address for this source
        #       amount: <int>, // amount
        #       extra: <str>, // optional data from payment transaction
        #     }]
        # inputs: ["source_str1", "source_str2", ...]
        # param outputs_json: The list of outputs as json array:
        #    [{
        #        recipient: <str>, // payment address of recipient
        #        amount: <int>, // amount
        #    }]

        accumulated = 0
        inputs = []
        async for source in get_sources(ledger, context.message.from_address):
            inputs.append(source['source'])
            accumulated += source['amount']
            if accumulated >= context.message.amount + fee:
                break

        outputs = [
            {
                'recipient': context.message.to_address,
                'amount': int(context.message.amount)
            },
            {
                'recipient': context.message.from_address,
                'amount': accumulated - fee - int(context.message.amount)
            }
        ]

        extras = await prepare_extra(ledger, {})

        payment_req, payment_method = await payment.build_payment_req(
            wallet.handle,
            None,
            json.dumps(inputs),
            json.dumps(outputs),
            extras
        )
        payment_resp = await ledger._submit(
            payment_req, sign=False
        )
        receipts = await payment.parse_payment_response(
            payment_method, payment_resp
        )

        completed = TransferComplete(
            from_address=context.message.from_address,
            to_address=context.message.to_address,
            amount=context.message.amount,
            raw_repr=json.loads(receipts)
        )
        completed.assign_thread_from(context.message)
        await responder.send_reply(completed)
