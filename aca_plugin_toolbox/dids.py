"""Define messages for did admin protocols."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from typing import Dict
from marshmallow import fields
from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ...wallet.base import BaseWallet, DIDInfo
from ..models.base_record import BaseRecord, BaseRecordSchema
from ...wallet.error import WalletNotFoundError

PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-dids/1.0'

GET_LIST_DIDS = '{}/get-list-dids'.format(PROTOCOL)
LIST_DIDS = '{}/list-dids'.format(PROTOCOL)
CREATE_DID = '{}/create-did'.format(PROTOCOL)
SET_DID_METADATA = '{}/set-did-metadata'.format(PROTOCOL)
DID = '{}/did'.format(PROTOCOL)
GET_PUBLIC_DID = '{}/get-public-did'.format(PROTOCOL)
SET_PUBLIC_DID = '{}/set-public-did'.format(PROTOCOL)
REGISTER_DID = '{}/register-did'.format(PROTOCOL)
GET_DID_VERKEY = '{}/get-did-verky'.format(PROTOCOL)
GET_DID_ENDPOINT = '{}/get-did-endpoint'.format(PROTOCOL)

MESSAGE_TYPES = {
    GET_LIST_DIDS:
        'aries_cloudagent.messaging.admin.dids'
        '.GetListDids',
    LIST_DIDS:
        'aries_cloudagent.messaging.admin.dids'
        '.ListDids',
    CREATE_DID:
        'aries_cloudagent.messaging.admin.dids'
        '.CreateDid',
    SET_DID_METADATA:
        'aries_cloudagent.messaging.admin.dids'
        '.SetDidMetadata',
    DID:
        'aries_cloudagent.messaging.admin.did'
        '.Did',
    GET_PUBLIC_DID:
        'aries_cloudagent.messaging.admin.dids'
        '.GetPublicDid',
    SET_PUBLIC_DID:
        'aries_cloudagent.messaging.admin.dids'
        '.SetPublicDid',
    REGISTER_DID:
        'aries_cloudagent.messaging.admin.dids'
        '.RegisterDid',
    GET_DID_VERKEY:
        'aries_cloudagent.messaging.admin.dids'
        '.GetDidVerkey',
    GET_DID_ENDPOINT:
    'aries_cloudagent.messaging.admin.dids'
        '.GetDidEndpoint'
}


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
    name='GetListDids',
    handler='aries_cloudagent.messaging.admin.dids.ListDidHandler',
    msg_type=GET_LIST_DIDS,
    schema={
        'did': fields.Str(required=False),
        'verkey': fields.Str(required=False)
    }
)


ListDids, ListDidsSchema = generate_model_schema(
    name='ListDids',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=LIST_DIDS,
    schema={
        'result': fields.List(
            fields.Nested(DidRecordSchema),
            required=True
        )
    }
)

CreateDid, CreateDidSchema = generate_model_schema(
    name='CreateDid',
    handler='aries_cloudagent.messaging.admin.dids.CreateDidHandler',
    msg_type=CREATE_DID,
    schema={
        'seed': fields.Str(required=False),
        'did': fields.Str(required=False),
        'metadata': fields.Dict(keys=fields.Str(), required=False)
    }
)

SetDidMetadata, SetDidMetadataSchema = generate_model_schema(
    name='SetDidMetadata',
    handler='aries_cloudagent.messaging.admin.dids.SetDidMetadataHandler',
    msg_type=SET_DID_METADATA,
    schema={
        'did': fields.Str(required=True),
        'metadata': fields.Dict(keys=fields.Str(), required=False)
    }
)

Did, DidSchema = generate_model_schema(
    name='Did',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=DID,
    schema={
        'result': fields.Nested(DidRecordSchema, required=False)
    }
)

GetPublicDid, GetPublicDidSchema = generate_model_schema(
    name='GetPublicDid',
    handler='aries_cloudagent.messaging.admin.dids.GetPublicDidHandler',
    msg_type=GET_PUBLIC_DID,
    schema={}
)

SetPublicDid, SetPublicDidSchema = generate_model_schema(
    name='SetPublicDid',
    handler='aries_cloudagent.messaging.admin.dids.SetPublicDidHandler',
    msg_type=SET_PUBLIC_DID,
    schema={
        'did': fields.Str(required=True)
    }
)

RegisterDid, RegisterDidSchema = generate_model_schema(
    name='RegisterDid',
    handler='aries_cloudagent.messaging.admin.dids.RegisterDidHandler',
    msg_type=SET_PUBLIC_DID,
    schema={
        'did': fields.Str(required=True),
        'verkey': fields.Str(required=True),
        'alias': fields.Str(required=False),
        'role': fields.Str(required=False)
    }
)

GetDidVerkey, GetDidVerkeySchema = generate_model_schema(
    name='GetDidVerkey',
    handler='aries_cloudagent.messaging.admin.dids.GetDidVerkeyHandler',
    msg_type=GET_DID_VERKEY,
    schema={
        'did': fields.Str(required=True)
    }
)

GetDidEndpoint, GetDidEndpointSchema = generate_model_schema(
    name='GetDidEndpoint',
    handler='aries_cloudagent.messaging.admin.dids.GetDidEndpointHandler',
    msg_type=GET_DID_VERKEY,
    schema={
        'did': fields.Str(required=True)
    }
)


def get_reply_did(info: DIDInfo) -> Did:
    if info:
        return Did(result=DidRecord(did=info.did if info.did else None,
                                 verkey=info.verkey if info.verkey else None,
                                 metadata=info.metadata if info.metadata else None))
    else:
        return Did(result=None)


class CreateDidHandler(BaseHandler):
    """Handler for creating local DIDs"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        wallet: BaseWallet = await context.inject(BaseWallet)

        did = context.message.did if context.message.did else None
        seed = context.message.seed if context.message.seed else None
        metadata = context.message.metadata if context.message.metadata else None

        did_info = await wallet.create_local_did(seed, did, metadata)

        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class ListDidHandler(BaseHandler):
    """Handler for list DIDs."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        wallet: BaseWallet = await context.inject(BaseWallet)

        # Get list of all DIDs in the wallet
        results = []
        try:
            if context.message.did:
                dids = [await wallet.get_local_did(context.message.did)]
            elif context.message.verkey:
                dids = [await wallet.get_local_did_for_verkey(context.message.verkey)]
            else:
                dids = await wallet.get_local_dids()

            results = [DidRecord(did=x.did,
                                 verkey=x.verkey,
                                 metadata=x.metadata if x.metadata else None) for x in dids]
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
        wallet: BaseWallet = await context.inject(BaseWallet)

        did_info = await wallet.get_public_did()
        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class SetPublicDidHandler(BaseHandler):
    """Handler that sets the current Public DID to the input"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """"Set the public DID"""
        wallet: BaseWallet = await context.inject(BaseWallet)

        await wallet.set_public_did(context.message.did)
        did_info = await wallet.get_public_did()
        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)


class SetDidMetadataHandler(BaseHandler):
    """"Handler that sets the DID metadata"""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """"Set the metadata"""
        wallet: BaseWallet = await context.inject(BaseWallet)

        await wallet.replace_local_did_metadata(context.message.did,
                                                context.message.metadata if context.message.metadata else None)
        did_info = await wallet.get_local_did(context.message.did)
        result = get_reply_did(did_info)
        result.assign_thread_from(context.message)
        await responder.send_reply(result)
