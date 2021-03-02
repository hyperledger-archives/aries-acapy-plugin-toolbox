"""Test SendPresProposal message and handler."""

import pytest

from acapy_plugin_toolbox.holder import v0_1 as test_module
from acapy_plugin_toolbox.holder.v0_1 import SendPresProposal
from ..conftest import mock_get_connection

TEST_CONN_ID = "test-connection-id"
TEST_PROPOSAL = "test-proposal"
TEST_COMMENT = "test-comment"


@pytest.fixture
def message():
    """Message fixture."""
    yield SendPresProposal(
        connection_id=TEST_CONN_ID,
        presentation_proposal=TEST_PROPOSAL,
        comment=TEST_COMMENT
    )


@pytest.fixture
def context(context, message):
    """Context fixture"""
    context.message = message
    yield context


@pytest.mark.asyncio
async def test_handler(context, mock_responder, message):
    """Test SendPresProposal handler."""
    with mock_get_connection(test_module):
        await message.handle(context, mock_responder)
    assert len(mock_responder.messages) == 2
    (prop, prop_recipient), (response, _) = mock_responder.messages
    assert prop.presentation_proposal == TEST_PROPOSAL
    assert prop.comment == TEST_COMMENT
    assert prop_recipient["connection_id"] == TEST_CONN_ID
    assert isinstance(response, test_module.PresExchange)
    assert response.connection_id == TEST_CONN_ID
