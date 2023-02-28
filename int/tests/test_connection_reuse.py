"""Connections Tests"""
import pytest

from acapy_client import Client
from acapy_client.api.connection import (
    get_connections,
    delete_connection,
)
from acapy_client.api.out_of_band import post_out_of_band_create_invitation
from acapy_client.models.invitation_create_request import InvitationCreateRequest
from echo_agent.client import EchoClient
from echo_agent.models import ConnectionInfo


@pytest.fixture(autouse=True)
async def clear_connection_state(backchannel: Client, connection_id: str):
    """Clear connections after each test."""
    yield
    connections = await get_connections.asyncio(client=backchannel)
    for connection in connections.results:
        if connection.connection_id != connection_id:
            await delete_connection.asyncio(
                client=backchannel, conn_id=connection.connection_id
            )


@pytest.mark.asyncio
async def test_connection_reuse_single_invitation(
    backchannel: Client,
    echo: EchoClient,
    echo_connection: ConnectionInfo,
    endorser_did,
):
    invitation = await post_out_of_band_create_invitation.asyncio(
        client=backchannel,
        json_body=InvitationCreateRequest(
            handshake_protocols=["did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"],
            use_public_did="true",
        ),
        auto_accept="true",
    )
    await echo.send_message(
        echo_connection,
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-oob-invitation",
            "invitation": invitation.invitation_url,
            "auto_accept": True,
        },
    )
    await echo.get_message(
        echo_connection,
        msg_type=(
            "https://github.com/hyperledger/aries-toolbox/tree/master/docs/"
            "admin-connections/0.1/connected"
        ),
    )
    connections_initial = await get_connections.asyncio(client=backchannel)
    len_conn_initial = len(connections_initial.results)

    # Accept the same invitation again
    await echo.send_message(
        echo_connection,
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-oob-invitation",
            "invitation": invitation.invitation_url,
            "auto_accept": True,
            "use_existing_connection": True,
        },
    )
    await echo.get_message(
        echo_connection,
        msg_type=(
            "https://github.com/hyperledger/aries-toolbox/tree/master/docs/"
            "admin-connections/0.1/connected"
        ),
    )
    connections_final = await get_connections.asyncio(client=backchannel)
    len_conn_final = len(connections_final.results)
    assert len_conn_initial == len_conn_final


@pytest.mark.asyncio
async def test_connection_reuse_multiple_invitations(
    backchannel: Client,
    echo: EchoClient,
    echo_connection: ConnectionInfo,
    endorser_did,
):
    invitation = await post_out_of_band_create_invitation.asyncio(
        client=backchannel,
        json_body=InvitationCreateRequest(
            handshake_protocols=["did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"],
            use_public_did="true",
        ),
        auto_accept="true",
    )
    await echo.send_message(
        echo_connection,
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-oob-invitation",
            "invitation": invitation.invitation_url,
            "auto_accept": True,
        },
    )
    await echo.get_message(
        echo_connection,
        msg_type=(
            "https://github.com/hyperledger/aries-toolbox/tree/master/docs/"
            "admin-connections/0.1/connected"
        ),
    )
    connections_initial = await get_connections.asyncio(client=backchannel)
    num_active_connections_initial = len(
        [conn.state for conn in connections_initial.results if conn.state == "active"]
    )

    # Send and receive another invitation
    invitation = await post_out_of_band_create_invitation.asyncio(
        client=backchannel,
        json_body=InvitationCreateRequest(
            handshake_protocols=["did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"],
            use_public_did="true",
        ),
        auto_accept="true",
    )
    await echo.send_message(
        echo_connection,
        {
            "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-connections/0.1/receive-oob-invitation",
            "invitation": invitation.invitation_url,
            "auto_accept": True,
            "use_existing_connection": True,
        },
    )
    connections_final = await get_connections.asyncio(client=backchannel)
    num_active_connections_final = len(
        [conn.state for conn in connections_final.results if conn.state == "active"]
    )
    assert num_active_connections_initial == num_active_connections_final
