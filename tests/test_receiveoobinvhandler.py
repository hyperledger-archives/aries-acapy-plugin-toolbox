from unittest.mock import patch
from aries_cloudagent.connections.models.conn_record import ConnRecord

import pytest
from aries_cloudagent.messaging.agent_message import AgentMessage
from asynctest import mock

import acapy_plugin_toolbox.connections as con
from aries_cloudagent.protocols.out_of_band.v1_0.messages.invitation import (
    InvitationMessage,
)
from tests.conftest import RequestContext


@pytest.fixture
def connection():
    yield ConnRecord()


@pytest.fixture
def message():
    """Message fixture"""
    yield con.ReceiveInvitation(
        auto_accept=True,
        mediation_id="test_id",
        invitation="http://example.org?c_i=eyPartyTime",
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
async def test_oobreceiveinvitationhandler(context, connection, mock_responder):
    """ReceiveOOBInvitationHandler test.

    A unit test for the ReceiveOOBInvitationHandler class."""
    receiveinv = con.ReceiveOOBInvitationHandler()
    mock_oob_mgr = mock.MagicMock()
    mock_oob_mgr.receive_invitation = mock.CoroutineMock(return_value=connection)

    with patch.object(
        AgentMessage, "assign_thread_from", mock.CoroutineMock()
    ) as mock_assign, patch.object(
        InvitationMessage, "from_url", mock.MagicMock()
    ) as mock_reply, patch.object(
        con, "OutOfBandManager", mock.MagicMock(return_value=mock_oob_mgr)
    ):
        await receiveinv.handle(context, mock_responder)
        mock_assign.assert_called_once()
        assert connection.accept
