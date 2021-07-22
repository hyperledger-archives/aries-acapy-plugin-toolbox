"""Holder Tests"""
import asyncio
import pytest

from acapy_backchannel import Client
from acapy_backchannel.models.create_invitation_request import CreateInvitationRequest
from acapy_backchannel.models.conn_record import ConnRecord
from acapy_backchannel.models.receive_invitation_request import ReceiveInvitationRequest
from acapy_backchannel.models.schema_send_request import SchemaSendRequest
from acapy_backchannel.models.credential_definition_send_request import (
    CredentialDefinitionSendRequest,
)
from acapy_backchannel.api.connection import (
    create_invitation,
    receive_invitation,
    get_connection,
)
from acapy_backchannel.api.schema import publish_schema
from acapy_backchannel.api.credential_definition import publish_cred_def


@pytest.fixture(scope="module")
async def issuer_holder_connection(backchannel: Client):
    """Invitation creation fixture"""
    invitation_created = await create_invitation.asyncio(
        client=backchannel, json_body=CreateInvitationRequest()
    )
    connection_created = await receive_invitation.asyncio(
        client=backchannel,
        json_body=ReceiveInvitationRequest(
            id=invitation_created.invitation.id,
            type=invitation_created.invitation.type,
            did=invitation_created.invitation.did,
            image_url=invitation_created.invitation.image_url,
            label=invitation_created.invitation.label,
            recipient_keys=invitation_created.invitation.recipient_keys,
            routing_keys=invitation_created.invitation.routing_keys,
            service_endpoint=invitation_created.invitation.service_endpoint,
        ),
    )
    return await get_connection.asyncio(
        client=backchannel, conn_id=connection_created.connection_id
    )


@pytest.fixture(scope="module")
async def create_schema(backchannel: Client, endorser_did):
    """Schema factory fixture"""

    async def _create_schema(version):
        return await publish_schema.asyncio(
            client=backchannel,
            json_body=SchemaSendRequest(
                attributes=["attr_1_0", "attr_1_1", "attr_1_2"],
                schema_name="Test Schema",
                schema_version=version,
            ),
        )

    yield _create_schema


@pytest.fixture(scope="module")
async def create_cred_def(backchannel: Client, endorser_did, create_schema):
    """Credential definition fixture"""

    async def _create_cred_def(version):
        schema = await create_schema(version="1.0")
        backchannel.timeout = 20
        return await publish_cred_def.asyncio(
            client=backchannel,
            json_body=CredentialDefinitionSendRequest(
                schema_id=schema.sent.schema_id,
            ),
        )

    yield _create_cred_def
