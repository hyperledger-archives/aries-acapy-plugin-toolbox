"""Define messages for static connections management admin protocol."""

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods

from marshmallow import fields, validate

from ...wallet.base import BaseWallet

from . import generate_model_schema, admin_only
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..connections.manager import ConnectionManager
from ..connections.models.connection_record import ConnectionRecord
from ..connections.models.diddoc import (
    DIDDoc, PublicKey, PublicKeyType, Service
)
from ..problem_report.message import ProblemReport
from ...storage.error import StorageNotFoundError


PROTOCOL = 'did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-static-connections/1.0'

# Message Types
CREATE_STATIC_CONNECTION = '{}/create-static-connection'.format(PROTOCOL)
STATIC_CONNECTION_INFO = '{}/static-connection-info'.format(PROTOCOL)
STATIC_CONNECTION_GET_LIST = '{}/static-connection-get-list'.format(PROTOCOL)
STATIC_CONNECTION_LIST = '{}/static-connection-list'.format(PROTOCOL)

# Message Type to Message Class Map
MESSAGE_TYPES = {
    CREATE_STATIC_CONNECTION:
        'aries_cloudagent.messaging.admin.static_connections'
        '.CreateStaticConnection',
    STATIC_CONNECTION_INFO:
        'aries_cloudagent.messaging.admin.static_connections'
        '.StaticConnectionInfo',
    STATIC_CONNECTION_GET_LIST:
        'aries_cloudagent.messaging.admin.static_connections'
        '.StaticConnectionGetList',
    STATIC_CONNECTION_LIST:
        'aries_cloudagent.messaging.admin.static_connections'
        '.StaticConnectionList',
}

# Models and Schemas
CreateStaticConnection, CreateStaticConnectionSchema = generate_model_schema(
    name='CreateStaticConnection',
    handler='aries_cloudagent.messaging.admin.static_connections'
            '.CreateStaticConnectionHandler',
    msg_type=CREATE_STATIC_CONNECTION,
    schema={
        'label': fields.Str(required=True),
        'role': fields.Str(required=False),
        'static_did': fields.Str(required=True),
        'static_key': fields.Str(required=True),
        'static_endpoint': fields.Str(missing='')
    }
)
StaticConnectionInfo, StaticConnectionInfoSchema = generate_model_schema(
    name='StaticConnectionInfo',
    handler='aries_cloudagent.messaging.admin.static_connections'
            '.StaticConnectionInfoHandler',
    msg_type=STATIC_CONNECTION_INFO,
    schema={
        'did': fields.Str(required=True),
        'key': fields.Str(required=True),
        'endpoint': fields.Str(required=True)
    }
)


class CreateStaticConnectionHandler(BaseHandler):
    """Handler for static connection creation requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle static connection creation request."""

        connection_mgr = ConnectionManager(context)
        wallet: BaseWallet = await context.inject(BaseWallet)

        # Make our info for the connection
        my_info = await wallet.create_local_did()

        # Create connection record
        connection = ConnectionRecord(
            initiator=ConnectionRecord.INITIATOR_SELF,
            my_did=my_info.did,
            their_did=context.message.static_did,
            their_label=context.message.label,
            their_role=context.message.role if context.message.role else None,
            state=ConnectionRecord.STATE_ACTIVE,
            invitation_mode=ConnectionRecord.INVITATION_MODE_STATIC
        )

        # Construct their did doc from the basic components in message
        diddoc = DIDDoc(context.message.static_did)
        public_key = PublicKey(
            did=context.message.static_did,
            ident="1",
            value=context.message.static_key,
            pk_type=PublicKeyType.ED25519_SIG_2018,
            controller=context.message.static_did
        )
        service = Service(
            did=context.message.static_did,
            ident="indy",
            typ="IndyAgent",
            recip_keys=[public_key],
            routing_keys=[],
            endpoint=context.message.static_endpoint
        )
        diddoc.set(public_key)
        diddoc.set(service)

        # Save
        await connection_mgr.store_did_document(diddoc)
        await connection.save(
            context,
            reason='Created new static connection'
        )

        # Prepare response
        info = StaticConnectionInfo(
            did=my_info.did,
            key=my_info.verkey,
            endpoint=context.settings.get("default_endpoint")
        )
        info.assign_thread_from(context.message)
        await responder.send_reply(info)
        return


StaticConnectionGetList, StaticConnectionGetListSchema = generate_model_schema(
    name='StaticConnectionGetList',
    handler='aries_cloudagent.messaging.admin.static_connections'
            '.StaticConnectionGetListHandler',
    msg_type=STATIC_CONNECTION_GET_LIST,
    schema={
        'initiator': fields.Str(
            validate=validate.OneOf(['self', 'external']),
            required=False,
        ),
        'invitation_key': fields.Str(required=False),
        'my_did': fields.Str(required=False),
        'their_did': fields.Str(required=False),
        'their_role': fields.Str(required=False)
    }
)

StaticConnectionList, StaticConnectionListSchema = generate_model_schema(
    name='StaticConnectionList',
    handler='aries_cloudagent.messaging.admin.PassHandler',
    msg_type=STATIC_CONNECTION_LIST,
    schema={
        'results': fields.List(fields.Dict(
            connection_id=fields.Str(),
            their_info=fields.Dict(
                label=fields.Str(),
                did=fields.Str(),
                vk=fields.Str(),
                endpoint=fields.Str()
            ),
            my_info=fields.Dict(
                label=fields.Str(),
                did=fields.Str(),
                vk=fields.Str(),
                endpoint=fields.Str()
            )
        ))
    }
)


class StaticConnectionGetListHandler(BaseHandler):
    """Handler for static connection get list requests."""

    @admin_only
    async def handle(self, context: RequestContext, responder: BaseResponder):
        """Handle static connection get list request."""
        connection_mgr = ConnectionManager(context)
        wallet: BaseWallet = await context.inject(BaseWallet)
        try:
            tag_filter = dict(
                filter(lambda item: item[1] is not None, {
                    'initiator': context.message.initiator,
                    'invitation_key': context.message.invitation_key,
                    'my_did': context.message.my_did,
                    'invitation_mode': ConnectionRecord.INVITATION_MODE_STATIC,
                    'their_did': context.message.their_did,
                    'their_role': context.message.their_role
                }.items())
            )
            records = await ConnectionRecord.query(context, tag_filter)
        except StorageNotFoundError:
            report = ProblemReport(
                explain_ltxt='Connection not found.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)
            return

        def flatten_target(connection, target, my_info):
            """Map for flattening results."""
            return {
                'connection_id': connection.connection_id,
                'their_info': {
                    'label': target.label,
                    'did': target.did,
                    'vk': target.recipient_keys[0],
                    'endpoint': target.endpoint
                },
                'my_info': {
                    'did': my_info.did,
                    'vk': my_info.verkey,
                    'endpoint': context.settings.get("default_endpoint")
                }
            }

        targets = []
        my_info = []
        for record in records:
            targets.append(
                await connection_mgr.get_connection_target(record)
            )
            my_info.append(await wallet.get_local_did(record.my_did))

        results = list(map(
            flatten_target,
            records,
            targets,
            my_info
        ))

        static_connections = StaticConnectionList(results=results)
        static_connections.assign_thread_from(context.message)
        await responder.send_reply(static_connections)
