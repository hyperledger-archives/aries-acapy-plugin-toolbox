"""Payment plugin."""
from ctypes import cdll
import json
import os
import platform

from marshmallow import Schema, fields
from indy import payment

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


async def setup(context: InjectionContext):
    """Load plugin."""

    # Load in libsovtoken
    cdll.LoadLibrary(LIBRARY).sovtoken_init()

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
