from unittest.mock import patch

import pytest
from aries_cloudagent.protocols.connections.v1_0.messages.connection_invitation import (
    ConnectionInvitation,
)
from aries_cloudagent.connections.models.conn_record import ConnRecord as con
from aries_cloudagent.messaging.responder import MockResponder
from aries_cloudagent.messaging.agent_message import AgentMessage
from asynctest import mock

import acapy_plugin_toolbox.invitations as inv
from tests.conftest import RequestContext


@pytest.fixture
def message():
    """Message fixture"""
    yield inv.CreateInvitation(
        label="test_label",
        auto_accept=True,
        multi_use=True,
        alias="create_invitation",
        mediation_id="test_med_id",
        group="test_group",
    )


@pytest.fixture
def context(profile, mock_admin_connection, message):
    """RequestContext fixture."""
    context = RequestContext(profile)
    context.connection_record = mock_admin_connection
    context.connection_ready = True
    context.message = message
    yield context


@pytest.mark.asyncio
async def test_createinvitationhandler(context, mock_responder):
    """CreateInvitationHandler test.

    A unit test for the CreateInvitationHandler class."""
    createinvhandler = inv.CreateInvitationHandler()
    connection = mock.MagicMock(spec=con)
    connection.metadata_set = mock.CoroutineMock()
    connection.connection_id = patch.object(con, "metadata_set", mock.CoroutineMock())
    connection.alias = "test_alias"
    connection.accept = True
    connection.invitation_mode = "test_mode"
    connection.created_at = "test_created"

    invitation = mock.MagicMock(spec=ConnectionInvitation)
    invitation.label = "test_label"
    mock_conn_mgr = mock.MagicMock()
    mock_conn_mgr.create_invitation = mock.CoroutineMock(
        return_value=(connection, invitation)
    )

    with patch.object(
        inv, "ConnectionManager", mock.MagicMock(return_value=mock_conn_mgr)
    ), patch.object(
        AgentMessage, "assign_thread_from", mock.CoroutineMock()
    ) as mock_assign:

        await createinvhandler.handle(context, mock_responder)
        connection.metadata_set.assert_called_once()
        mock_assign.assert_called_once()
        assert isinstance(mock_responder.messages[0][0], inv.Invitation)
        assert (
            mock_responder.messages[0][0].mediation_id == context.message.mediation_id
        )
