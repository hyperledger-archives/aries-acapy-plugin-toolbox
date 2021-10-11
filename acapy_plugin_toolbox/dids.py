"""Define messages for did admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from typing import Dict
from marshmallow import fields

from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.models.base_record import BaseRecord, BaseRecordSchema
from aries_cloudagent.wallet.base import BaseWallet, DIDInfo
from aries_cloudagent.wallet.error import WalletNotFoundError
from aries_cloudagent.wallet.did_method import DIDMethod
from aries_cloudagent.wallet.key_type import KeyType

from .util import generate_model_schema, admin_only

PROTOCOL = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-dids/0.1"

GET_LIST_DIDS = "{}/get-list-dids".format(PROTOCOL)
LIST_DIDS = "{}/list-dids".format(PROTOCOL)
CREATE_DID = "{}/create-did".format(PROTOCOL)
SET_DID_METADATA = "{}/set-did-metadata".format(PROTOCOL)
DID = "{}/did".format(PROTOCOL)
PUBLIC_DID = "{}/public-did".format(PROTOCOL)
GET_PUBLIC_DID = "{}/get-public-did".format(PROTOCOL)
SET_PUBLIC_DID = "{}/set-public-did".format(PROTOCOL)
REGISTER_DID = "{}/register-did".format(PROTOCOL)
GET_DID_VERKEY = "{}/get-did-verky".format(PROTOCOL)
GET_DID_ENDPOINT = "{}/get-did-endpoint".format(PROTOCOL)

MESSAGE_TYPES = {
    GET_LIST_DIDS: "acapy_plugin_toolbox.dids" ".GetListDids",
    LIST_DIDS: "acapy_plugin_toolbox.dids" ".ListDids",
    CREATE_DID: "acapy_plugin_toolbox.dids" ".CreateDid",
    SET_DID_METADATA: "acapy_plugin_toolbox.dids" ".SetDidMetadata",
    DID: "acapy_plugin_toolbox.did" ".Did",
    PUBLIC_DID: "acapy_plugin_toolbox.did.PublicDid",
    GET_PUBLIC_DID: "acapy_plugin_toolbox.dids" ".GetPublicDid",
    SET_PUBLIC_DID: "acapy_plugin_toolbox.dids" ".SetPublicDid",
    REGISTER_DID: "acapy_plugin_toolbox.dids" ".RegisterDid",
    GET_DID_VERKEY: "acapy_plugin_toolbox.dids" ".GetDidVerkey",
    GET_DID_ENDPOINT: "acapy_plugin_toolbox.dids" ".GetDidEndpoint",
}


async def setup(session: ProfileSession, protocol_registry: ProtocolRegistry = None):
    """Setup the dids plugin."""
    if not protocol_registry:
        protocol_registry = session.inject(ProtocolRegistry)
    protocol_registry.register_message_types(MESSAGE_TYPES)


class DidRecord(BaseRecord):
    """Represents a DID."""

    RECORD_ID_NAME = "did"
    RECORD_TYPE = "did"

    class Meta:
        """DidRecord metadata."""

        schema_class = "DidRecordSchema"

    def __init__(
        self,
        *,
        did: str = None,
        verkey: str = None,
        metadata: Dict[str, object] = None,
        **kwargs,
    ):
        """Initialize a new DidRecord."""
        super().__init__(None, None, **kwargs)
        self.did = did
        self.verkey = verkey
        self.metadata = metadata


class DidRecordSchema(BaseRecordSchema):
    """Schema to allow serialization/deserialization of DID records."""

    class Meta:
        """DidRecordSchema metadata."""

        model_class = DidRecord

    did = fields.Str(required=True)
    verkey = fields.Str(required=True)
    metadata = fields.Dict(keys=fields.Str(), required=False)


GetListDids, GetListDidsSchema = generate_model_schema(
    name="GetListDids",
    handler="acapy_plugin_toolbox.dids.ListDidHandler",
    msg_type=GET_LIST_DIDS,
    schema={"did": fields.Str(required=False), "verkey": fields.Str(required=False)},
)


ListDids, ListDidsSchema = generate_model_schema(
    name="ListDids",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=LIST_DIDS,
    schema={"result": fields.List(fields.Nested(DidRecordSchema), required=True)},
)

CreateDid, CreateDidSchema = generate_model_schema(
    name="CreateDid",
    handler="acapy_plugin_toolbox.dids.CreateDidHandler",
    msg_type=CREATE_DID,
    schema={
        "seed": fields.Str(required=False),
        "did": fields.Str(required=False),
        "metadata": fields.Dict(keys=fields.Str(), required=False),
    },
)

SetDidMetadata, SetDidMetadataSchema = generate_model_schema(
    name="SetDidMetadata",
    handler="acapy_plugin_toolbox.dids.SetDidMetadataHandler",
    msg_type=SET_DID_METADATA,
    schema={
        "did": fields.Str(required=True),
        "metadata": fields.Dict(keys=fields.Str(), required=False),
    },
)

Did, DidSchema = generate_model_schema(
    name="Did",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=DID,
    schema={"result": fields.Nested(DidRecordSchema, required=False)},
)

PublicDid, PublicDidSchema = generate_model_schema(
    name="PublicDid",
    handler="acapy_plugin_toolbox.util.PassHandler",
    msg_type=PUBLIC_DID,
    schema={"result": fields.Nested(DidRecordSchema, required=False)},
)

GetPublicDid, GetPublicDidSchema = generate_model_schema(
    name="GetPublicDid",
    handler="acapy_plugin_toolbox.dids.GetPublicDidHandler",
    msg_type=GET_PUBLIC_DID,
    schema={},
)

SetPublicDid, SetPublicDidSchema = generate_model_schema(
    name="SetPublicDid",
    handler="acapy_plugin_toolbox.dids.SetPublicDidHandler",
    msg_type=SET_PUBLIC_DID,
    schema={"did": fields.Str(required=True)},
)

RegisterDid, RegisterDidSchema = generate_model_schema(
    name="RegisterDid",
    handler="acapy_plugin_toolbox.dids.RegisterDidHandler",
    msg_type=SET_PUBLIC_DID,
    schema={
        "did": fields.Str(required=True),
        "verkey": fields.Str(required=True),
        "alias": fields.Str(required=False),
        "role": fields.Str(required=False),
    },
)

GetDidVerkey, GetDidVerkeySchema = generate_model_schema(
    name="GetDidVerkey",
    handler="acapy_plugin_toolbox.dids.GetDidVerkeyHandler",
    msg_type=GET_DID_VERKEY,
    schema={"did": fields.Str(required=True)},
)

GetDidEndpoint, GetDidEndpointSchema = generate_model_schema(
    name="GetDidEndpoint",
    handler="acapy_plugin_toolbox.dids.GetDidEndpointHandler",
    msg_type=GET_DID_VERKEY,
    schema={"did": fields.Str(required=True)},
)


def get_reply_did(info: DIDInfo) -> Did:
    if info:
        return Did(
            result=DidRecord(
                did=info.did if info.did else None,
                verkey=info.verkey if info.verkey else None,
                metadata=info.metadata if info.metadata else None,
            )
        )
    else:
        return Did(result=None)


def public_did(info: DIDInfo) -> Did:
    if info:
        return PublicDid(
            result=DidRecord(
                did=info.did if info.did else None,
                verkey=info.verkey if info.verkey else None,
                metadata=info.metadata if info.metadata else None,
            )
        )
    else:
        return PublicDid(result=None)


class CreateDidHandler(BaseHandler):
    """Handler for creating local DIDs"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)

        did = context.message.did if context.message.did else None
        seed = context.message.seed if context.message.seed else None
        metadata = context.message.metadata if context.message.metadata else None

        did_info = await wallet.create_local_did(
            method=DIDMethod.SOV,
            key_type=KeyType.ED25519,
            seed=seed,
            did=did,
            metadata=metadata,
        )

        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class ListDidHandler(BaseHandler):
    """Handler for list DIDs."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)

        # Get list of all DIDs in the wallet
        results = []
        try:
            if context.message.did:
                dids = [await wallet.get_local_did(context.message.did)]
            elif context.message.verkey:
                dids = [await wallet.get_local_did_for_verkey(context.message.verkey)]
            else:
                dids = await wallet.get_local_dids()

            results = [
                DidRecord(
                    did=x.did,
                    verkey=x.verkey,
                    metadata=x.metadata if x.metadata else None,
                )
                for x in dids
            ]
        except WalletNotFoundError:
            pass

        did_list = ListDids(result=results)
        did_list.assign_thread_from(context.message)
        await responder.send_reply(did_list)


class GetPublicDidHandler(BaseHandler):
    """Handler that retrieves the currently set Public DID"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Look for the public DID"""
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)

        did_info = await wallet.get_public_did()
        result = public_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class SetPublicDidHandler(BaseHandler):
    """Handler that sets the current Public DID to the input"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """ "Set the public DID"""
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)

        await wallet.set_public_did(context.message.did)
        did_info = await wallet.get_public_did()
        result = public_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class SetDidMetadataHandler(BaseHandler):
    """ "Handler that sets the DID metadata"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """ "Set the metadata"""
        session = await context.session()
        wallet: BaseWallet = session.inject(BaseWallet)

        await wallet.replace_local_did_metadata(
            context.message.did,
            context.message.metadata if context.message.metadata else None,
        )
        did_info = await wallet.get_local_did(context.message.did)
        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)
