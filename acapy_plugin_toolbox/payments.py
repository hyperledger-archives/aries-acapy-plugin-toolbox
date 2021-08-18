"""Payment plugin."""
# pylint: disable=invalid-name

from ctypes import cdll
import json
import os
import platform
from functools import reduce
from typing import Dict, Sequence, Tuple

from marshmallow import Schema, fields
from indy import payment
from indy import ledger as indy_ledger
from indy.error import IndyError

from aries_cloudagent.ledger.base import BaseLedger
from aries_cloudagent.ledger.error import LedgerError
from aries_cloudagent.ledger.indy import IndyErrorHandler
from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.wallet.base import BaseWallet
from .util import generate_model_schema, admin_only

# TODO: Find a better way to find the library
LIBRARY = os.environ.get("LIBSOVTOKEN", "libsovtoken.so")
SOV_METHOD = "sov"
# LIBRARY = 'libsovtoken'
EXTENSION = {"darwin": ".dylib", "linux": ".so", "win32": ".dll", "windows": ".dll"}


PROTOCOL_URI = (
    "https://github.com/hyperledger/aries-toolbox/"
    "tree/master/docs/admin-payments/0.1"
)

GET_ADDRESS_LIST = f"{PROTOCOL_URI}/get-address-list"
ADDRESS_LIST = f"{PROTOCOL_URI}/address-list"
CREATE_ADDRESS = f"{PROTOCOL_URI}/create-address"
ADDRESS = f"{PROTOCOL_URI}/address"
GET_FEES = f"{PROTOCOL_URI}/get-fees"
FEES = f"{PROTOCOL_URI}/fees"
TRANSFER = f"{PROTOCOL_URI}/transfer"
TRANSFER_COMPLETE = f"{PROTOCOL_URI}/transfer-complete"

MESSAGE_TYPES = {
    GET_ADDRESS_LIST: "acapy_plugin_toolbox.payments.GetAddressList",
    ADDRESS_LIST: "acapy_plugin_toolbox.payments.AddressList",
    CREATE_ADDRESS: "acapy_plugin_toolbox.payments.CreateAddress",
    GET_FEES: "acapy_plugin_toolbox.payments.GetFees",
    ADDRESS: "acapy_plugin_toolbox.payments.Address",
    TRANSFER: "acapy_plugin_toolbox.payments.Transfer",
    TRANSFER_COMPLETE: "acapy_plugin_toolbox.payments.TransferComplete",
}


def file_ext():
    """Determine extension for system."""
    your_platform = platform.system().lower()
    return EXTENSION[your_platform] if (your_platform in EXTENSION) else ".so"


async def setup(session: ProfileSession, protocol_registry: ProblemReport = None):
    """Load plugin."""

    # Load in libsovtoken
    cdll.LoadLibrary(LIBRARY).sovtoken_init()

    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


class PaymentError(Exception):
    """When an error occurs during payment"""


def sovatoms_to_tokens(sovatoms: int) -> float:
    """Convert sovatoms to tokens."""
    return sovatoms / 100000000


def tokens_to_sovatoms(tokens: float) -> int:
    """Convert tokens to sovatoms."""
    return int(tokens * 100000000)


async def get_sources(ledger: BaseLedger, payment_address: str):
    """Retrieve sources for this payment address and asynchrounsly generate."""
    # We need to use ledger._submit
    # pylint: disable=protected-access
    with IndyErrorHandler("Failed to retrieve payment address sources"):
        next_seqno = -1
        while True:
            (
                get_sources_json,
                method,
            ) = await payment.build_get_payment_sources_with_from_request(
                ledger.wallet.handle, None, payment_address, next_seqno
            )

            resp = await ledger._submit(get_sources_json, sign=False)
            (
                source_list,
                next_seqno,
            ) = await payment.parse_get_payment_sources_with_from_response(method, resp)
            sources = json.loads(source_list)
            for source in sources:
                yield source
            if next_seqno == -1:
                break


async def get_balance(ledger: BaseLedger, payment_address: str):
    """Return the balance of a payment address."""
    sources = [source async for source in get_sources(ledger, payment_address)]

    return reduce(lambda acc, source: acc + source["amount"], sources, 0)


BasePaymentAddressSchema = Schema.from_dict(
    {
        "address": fields.Str(required=True),
        "method": fields.Str(required=True),
        "balance": fields.Float(required=True),
        "raw_repr": fields.Dict(required=False),
    }
)

GetAddressList, GetAddressListSchema = generate_model_schema(
    name="GetAddressList",
    handler="acapy_plugin_toolbox.payments.GetAddressListHandler",
    msg_type=GET_ADDRESS_LIST,
    schema={"method": fields.Str(required=False)},
)

AddressList, AddressListSchema = generate_model_schema(
    name="AddressList",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ADDRESS_LIST,
    schema={
        "addresses": fields.List(fields.Nested(BasePaymentAddressSchema), required=True)
    },
)


class GetAddressListHandler(BaseHandler):
    """Handler for received address list requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received address list requests."""
        if context.message.method and context.message.method != SOV_METHOD:
            report = ProblemReport(
                description={
                    "en": (
                        'Method "{}" is not supported.'.format(context.message.method)
                    )
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        try:
            addresses = json.loads(
                await payment.list_payment_addresses(ledger.wallet.handle)
            )

            async with ledger:
                address_results = []
                for address in addresses:
                    balance = 0
                    sources = []
                    async for source in get_sources(ledger, address):
                        balance += source["amount"]
                        sources.append(source)
                    address_results.append(
                        {
                            "address": address,
                            "method": SOV_METHOD,
                            "balance": sovatoms_to_tokens(balance),
                            "raw_repr": {"sources": sources},
                        }
                    )
        except (LedgerError, PaymentError) as err:
            report = ProblemReport(description={"en": str(err)}, who_retries="none")
            await responder.send_reply(report)
            return
        except IndyError as err:
            # TODO: Remove when IndyErrorHandler bug is fixed.
            # Likely to be next ACA-Py release.
            message = "Unexpected IndyError while retrieving addresses"
            if hasattr(err, "message"):
                message += ": {}".format(err.message)
            report = ProblemReport(description={"en": message}, who_retries="none")
            await responder.send_reply(report)
            return

        result = AddressList(addresses=address_results)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


CreateAddress, CreateAddressSchema = generate_model_schema(
    name="CreateAddress",
    handler="acapy_plugin_toolbox.payments.CreateAddressHandler",
    msg_type=CREATE_ADDRESS,
    schema={"seed": fields.Str(required=False), "method": fields.Str(required=True)},
)

Address, AddressSchema = generate_model_schema(
    name="Address",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=ADDRESS,
    schema=BasePaymentAddressSchema,
)


class CreateAddressHandler(BaseHandler):
    """Handler for received create address requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle received create address requests."""
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)
        ledger: BaseLedger = session.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                description={
                    "en": (
                        'Method "{}" is not supported.'.format(context.message.method)
                    )
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        if context.message.seed and len(context.message.seed) < 32:
            report = ProblemReport(
                description={"en": ("Seed must be 32 characters in length")},
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        try:
            address_str = await payment.create_payment_address(
                wallet.handle, SOV_METHOD, json.dumps({"seed": context.message.seed})
            )
        except IndyError as err:
            message = "Failed to create payment address"
            if hasattr(err, "message"):
                message += ": {}".format(err.message)
            report = ProblemReport(description={"en": message}, who_retries="none")
            await responder.send_reply(report)
            return

        try:
            async with ledger:
                balance = 0
                sources = []
                async for source in get_sources(ledger, address_str):
                    balance += source["amount"]
                    sources.append(source)
        except (LedgerError, PaymentError) as err:
            report = ProblemReport(description={"en": str(err)}, who_retries="none")
            await responder.send_reply(report)
            return
        except IndyError as err:
            # TODO: Remove when IndyErrorHandler bug is fixed.
            # Likely to be next ACA-Py release.
            message = "Unexpected IndyError while retrieving address balances"
            if hasattr(err, "message"):
                message += ": {}".format(err.message)
            report = ProblemReport(description={"en": message}, who_retries="none")
            await responder.send_reply(report)
            return

        address = Address(
            address=address_str, method=SOV_METHOD, balance=sovatoms_to_tokens(balance)
        )
        address.assign_thread_from(context.message)
        await responder.send_reply(address)
        return


GetFees, GetFeesSchema = generate_model_schema(
    name="GetFees",
    handler="acapy_plugin_toolbox.payments.GetFeesHandler",
    msg_type=GET_FEES,
    schema={
        "method": fields.Str(required=True),
        "amount": fields.Float(required=False),
    },
)

Fees, FeesSchema = generate_model_schema(
    name="Fees",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=FEES,
    schema={"total": fields.Float(required=True)},
)


async def fetch_transfer_auth(ledger: BaseLedger):
    """Retrieve token transfer fee."""
    # We need to use ledger._submit
    # pylint: disable=protected-access
    with IndyErrorHandler("Failed to retrieve transfer auth"):
        req = await payment.build_get_txn_fees_req(
            ledger.wallet.handle, None, SOV_METHOD
        )
        xfer_fee_resp = await ledger._submit(req, sign=False)
        parse_xfer_fee = await payment.parse_get_txn_fees_response(
            SOV_METHOD, xfer_fee_resp
        )
        req = await indy_ledger.build_get_auth_rule_request(
            None, "10001", "ADD", "*", None, "*"
        )
        auth_rule_resp = await ledger._submit(req, sign=False)

        xfer_auth_fee = json.loads(
            await payment.get_request_info(
                auth_rule_resp, json.dumps({"sig_count": 1}), parse_xfer_fee
            )
        )
    if ledger.cache:
        await ledger.cache.set(
            ["admin-payments::xfer_auth"], xfer_auth_fee, ledger.cache_duration
        )
    return xfer_auth_fee


async def get_transfer_auth(ledger: BaseLedger):
    """Retrieve token transfer fee."""
    if ledger.cache:
        result = await ledger.cache.get("admin-payments::xfer_auth")
        if result:
            return result

    return await fetch_transfer_auth(ledger)


class GetFeesHandler(BaseHandler):
    """Handler for get fees."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle get fees."""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                description={
                    "en": (
                        'Method "{}" is not supported.'.format(context.message.method)
                    )
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        try:
            async with ledger:
                xfer_auth = await get_transfer_auth(ledger)
        except (LedgerError, PaymentError) as err:
            report = ProblemReport(description={"en": str(err)}, who_retries="none")
            await responder.send_reply(report)
            return
        except IndyError as err:
            # TODO: Remove when IndyErrorHandler bug is fixed.
            # Likely to be next ACA-Py release.
            message = "Unexpected IndyError while retrieving transfer fee"
            if hasattr(err, "message"):
                message += ": {}".format(err.message)
            report = ProblemReport(description={"en": message}, who_retries="none")
            await responder.send_reply(report)
            return

        fees = Fees(total=sovatoms_to_tokens(xfer_auth["price"]))
        fees.assign_thread_from(context.message)
        await responder.send_reply(fees)


Transfer, TransferSchema = generate_model_schema(
    name="Transfer",
    handler="acapy_plugin_toolbox.payments.TransferHandler",
    msg_type=TRANSFER,
    schema={
        "method": fields.Str(required=True),
        "from_address": fields.Str(required=True),
        "to_address": fields.Str(required=True),
        "amount": fields.Float(required=True),
    },
)

BaseReceiptSchema = Schema.from_dict(
    {
        "receipt": fields.Str(required=True),
        "recipient": fields.Str(required=True),
        "amount": fields.Float(required=True),
        "extra": fields.Str(required=False),
    }
)

TransferComplete, TransferCompleteSchema = generate_model_schema(
    name="TransferComplete",
    handler="acapy_plugin_toolbox.payments.TransferCompleteHandler",
    msg_type=TRANSFER_COMPLETE,
    schema={
        "from_address": fields.Str(required=True),
        "to_address": fields.Str(required=True),
        "amount": fields.Float(required=True),
        "method": fields.Str(required=False),
        "fees": fields.Float(required=False),
        "raw_repr": fields.Dict(required=False),
    },
)


async def prepare_extra(ledger: BaseLedger, extra: Dict = None):
    """Prepare extras field for submission of payment request."""
    extra_json = json.dumps(extra or {})
    acceptance = await ledger.get_latest_txn_author_acceptance()
    if acceptance:
        with IndyErrorHandler("Failed to append txn author acceptance to extras"):
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
    return extra_json


async def prepare_payment(
    ledger: BaseLedger, from_address: str, to_address: str, amount: int, fee: int
) -> Tuple[Sequence[str], Sequence[Dict]]:
    """Prepare inputs and outputs for a payment."""
    if from_address == to_address:
        raise PaymentError("Source and destination addresses are the same")

    if amount <= 0:
        raise PaymentError("Payment amount must be greater than 0")

    accumulated = 0
    inputs = []
    async for source in get_sources(ledger, from_address):
        inputs.append(source["source"])
        accumulated += source["amount"]
        if accumulated >= amount + fee:
            break

    if accumulated < (amount + fee):
        raise PaymentError(
            "Insufficient funds; {} available, {} required".format(
                accumulated, amount + fee
            )
        )

    outputs = list(
        filter(
            lambda output: output["amount"] > 0,
            [
                {"recipient": to_address, "amount": amount},
                {"recipient": from_address, "amount": (accumulated - fee - amount)},
            ],
        )
    )
    return inputs, outputs


async def make_payment(
    ledger: BaseLedger,
    inputs: Sequence[str],
    outputs: Sequence[Dict],
    extra: Dict = None,
) -> Dict:
    """Make a payment.

    Arguments:

        inputs (Sequence[str]): Input sources for the payment i.e.
            ["txo:sov:12345...", "txo:sov:abcde..."]
            Use prepare_payment to construct this based off a desired amount to
            transfer, source, and destintation address.

        outputs (Sequence[Dict]): Output objects for the payment i.e.
            [
                {
                    "recipient": "pay:sov:1234abcd...",
                    "amount": 100000
                },
                {
                    "recipient": "pay:sov:abcd1234...",
                    "amount": 200000
                },
            ]
            Use prepare_payment to construct this based off a desired amount to
            transfer, source, and destintation address.

        extra (Dict): Optional extra information for the payment transaction.
    """
    # We need to use ledger._submit
    # pylint: disable=protected-access
    with IndyErrorHandler("Payment failed"):
        extras = await prepare_extra(ledger, extra)

        payment_req, payment_method = await payment.build_payment_req(
            ledger.wallet.handle, None, json.dumps(inputs), json.dumps(outputs), extras
        )
        payment_resp = await ledger._submit(payment_req, sign=False)
        receipts = await payment.parse_payment_response(payment_method, payment_resp)
    return json.loads(receipts)


class TransferHandler(BaseHandler):
    """Handler for payment"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle payment"""
        session = await context.session()
        ledger: BaseLedger = session.inject(BaseLedger)
        if context.message.method != SOV_METHOD:
            report = ProblemReport(
                description={
                    "en": (
                        'Method "{}" is not supported.'.format(context.message.method)
                    )
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        async with ledger:
            try:
                fee = (await get_transfer_auth(ledger))["price"]
                inputs, outputs = await prepare_payment(
                    ledger,
                    context.message.from_address,
                    context.message.to_address,
                    tokens_to_sovatoms(context.message.amount),
                    fee,
                )
                receipts = await make_payment(ledger, inputs, outputs)
            except (LedgerError, PaymentError) as err:
                report = ProblemReport(description={"en": str(err)}, who_retries="none")
                await responder.send_reply(report)
                return
            except IndyError as err:
                # TODO: Remove when IndyErrorHandler bug is fixed.
                # Likely to be next ACA-Py release.
                message = "Unexpected IndyError while making payment"
                if hasattr(err, "message"):
                    message += ": {}".format(err.message)
                report = ProblemReport(description={"en": message}, who_retries="none")
                await responder.send_reply(report)
                return

        completed = TransferComplete(
            from_address=context.message.from_address,
            to_address=context.message.to_address,
            amount=context.message.amount,
            fees=sovatoms_to_tokens(fee),
            method=SOV_METHOD,
            raw_repr=receipts,
        )
        completed.assign_thread_from(context.message)
        await responder.send_reply(completed)
