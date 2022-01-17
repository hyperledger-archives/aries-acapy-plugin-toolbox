"""Holder Tests"""
import asyncio
from acapy_client.models.credential_definition_send_result import (
    CredentialDefinitionSendResult,
)
import pytest
from typing import cast

from acapy_client import Client
from acapy_client.models.create_invitation_request import CreateInvitationRequest
from acapy_client.models.conn_record import ConnRecord
from acapy_client.models.receive_invitation_request import ReceiveInvitationRequest
from acapy_client.models.schema_send_request import SchemaSendRequest
from acapy_client.models.v10_credential_proposal_request_mand import (
    V10CredentialProposalRequestMand,
)
from acapy_client.models.credential_preview import CredentialPreview
from acapy_client.models.credential_definition_send_request import (
    CredentialDefinitionSendRequest,
)
from acapy_client.models.cred_attr_spec import CredAttrSpec
from acapy_client.models.v10_credential_exchange import V10CredentialExchange
from acapy_client.api.connection import (
    create_invitation,
    receive_invitation,
    get_connection,
)
from acapy_client.api.schema import publish_schema
from acapy_client.api.credential_definition import publish_cred_def
from acapy_client.api.issue_credential_v10 import issue_credential_automated
from acapy_client.api.issue_credential_v10 import get_issue_credential_records


@pytest.fixture(scope="module")
async def issuer_holder_connection(backchannel: Client, connection):
    """Invitation creation fixture"""
    invitation_created = await create_invitation.asyncio(
        client=backchannel, json_body=CreateInvitationRequest(), auto_accept="true"
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
        auto_accept="true",
    )
    return invitation_created, connection_created


@pytest.fixture
async def issue_credential(
    backchannel: Client,
    connection,
    issuer_holder_connection,
    endorser_did,
    create_schema,
    create_cred_def,
    wait_for_message,
):
    connected = issuer_holder_connection
    cred_def = await create_cred_def(version="1.0")
    assert isinstance(cred_def, CredentialDefinitionSendResult)
    issue_result = await asyncio.wait_for(
        issue_credential_automated.asyncio(
            client=backchannel,
            json_body=V10CredentialProposalRequestMand(
                connection_id=connected[1].connection_id,
                credential_proposal=CredentialPreview(
                    [
                        CredAttrSpec(name="attr_1_0", value="Test 1"),
                        CredAttrSpec(name="attr_1_1", value="Test 2"),
                        CredAttrSpec(name="attr_1_2", value="Test 3"),
                    ]
                ),
                cred_def_id=cred_def.credential_definition_id,
            ),
        ),
        timeout=60,
    )
    credential_offer_received = await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-offer-received"
    )
    issue_result = cast(V10CredentialExchange, issue_result)
    await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-offer-accept",
            "credential_exchange_id": credential_offer_received[
                "credential_exchange_id"
            ],
        }
    )
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-received"
    )
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1/credential-issued"
    )
    credentials_list = await asyncio.wait_for(
        get_issue_credential_records.asyncio(client=backchannel), timeout=40
    )
    return credentials_list


@pytest.mark.asyncio
async def test_holder_credential_exchange(
    backchannel: Client,
    connection,
    issuer_holder_connection,
    endorser_did,
    create_schema,
    create_cred_def,
    wait_for_message,
):
    connected = issuer_holder_connection
    cred_def = await create_cred_def(version="1.0")
    assert isinstance(cred_def, CredentialDefinitionSendResult)
    issue_result = await asyncio.wait_for(
        issue_credential_automated.asyncio(
            client=backchannel,
            json_body=V10CredentialProposalRequestMand(
                connection_id=connected[1].connection_id,
                credential_proposal=CredentialPreview(
                    [
                        CredAttrSpec(name="attr_1_0", value="Test 1"),
                        CredAttrSpec(name="attr_1_1", value="Test 2"),
                        CredAttrSpec(name="attr_1_2", value="Test 3"),
                    ]
                ),
                cred_def_id=cred_def.credential_definition_id,
            ),
        ),
        timeout=60,
    )
    credential_offer_received = await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-offer-received"
    )
    issue_result = cast(V10CredentialExchange, issue_result)
    credential_offer_accept = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-offer-accept",
            "credential_exchange_id": credential_offer_received[
                "credential_exchange_id"
            ],
        }
    )
    assert (
        credential_offer_accept["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-request-sent"
    )
    credential_received = await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credential-received"
    )
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1/credential-issued"
    )
    records = await asyncio.wait_for(
        get_issue_credential_records.asyncio(client=backchannel), timeout=20
    )
    assert credential_received["credential_exchange_id"] in [
        record.credential_exchange_id for record in records.results
    ]


@pytest.mark.asyncio
async def test_credentials_get_list(
    backchannel: Client,
    connection,
    issue_credential,
    wait_for_message,
):
    cred = issue_credential
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1/credential-issued"
    )
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1/credential-issued"
    )
    credentials_get_list = await connection.send_and_await_reply_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credentials-get-list"
        }
    )
    cred_set = {result.credential_exchange_id for result in cred.results}
    cred_get_list_set = {
        cred["credential_exchange_id"] for cred in credentials_get_list["results"]
    }
    assert (
        credentials_get_list["@type"]
        == "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/credentials-list"
    )
    assert cred_get_list_set <= cred_set
