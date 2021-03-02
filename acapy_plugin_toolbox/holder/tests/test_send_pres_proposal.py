"""Test SendPresProposal message and handler."""

import pytest
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.messaging.request_context import RequestContext
from aries_cloudagent.messaging.responder import MockResponder
from asynctest import mock

from .. import v0_1 as test_module
from ..v0_1 import SendPresProposal

TEST_CONN_ID = "test-connection-id"
TEST_PROPOSAL = "test-proposal"
TEST_COMMENT = "test-comment"

@pytest.fixture
def mock_admin_connection():
    """Mock connection fixture."""
    connection = mock.MagicMock(spec=ConnRecord)
    connection.metadata_get = mock.CoroutineMock(return_value="admin")
    yield connection


@pytest.fixture
def message():
    """Message fixture."""
    yield SendPresProposal(
        connection_id=TEST_CONN_ID,
        presentation_proposal=TEST_PROPOSAL,
        comment=TEST_COMMENT
    )


@pytest.fixture
def profile():
    """Profile fixture."""
    yield InMemoryProfile.test_profile()


@pytest.fixture
def context(profile, message, mock_admin_connection):
    """RequestContext fixture."""
    context = RequestContext(profile)
    context.message = message
    context.connection_record = mock_admin_connection
    context.connection_ready = True
    yield context


@pytest.fixture
def mock_responder():
    """Mock responder fixture."""
    yield MockResponder()


@pytest.mark.asyncio
@mock.patch.object(
    test_module,
    "get_connection",
    mock.CoroutineMock(return_value=mock.MagicMock(spec=ConnRecord))
)
async def test_handler(context, mock_responder, message):
    """Test SendPresProposal handler."""
    await message.handle(context, mock_responder)
    assert len(mock_responder.messages) == 2
    (prop, prop_recipient), (response, _) = mock_responder.messages
    assert prop.presentation_proposal == TEST_PROPOSAL
    assert prop.comment == TEST_COMMENT
    assert prop_recipient["connection_id"] == TEST_CONN_ID
    assert isinstance(response, test_module.PresExchange)
    assert response.connection_id == TEST_CONN_ID
