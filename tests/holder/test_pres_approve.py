"""Test PresRequestApprove message and handler."""

import pytest
from acapy_plugin_toolbox.holder.v0_1.messages import (
    pres_request_approve as test_module,
)
from acapy_plugin_toolbox.holder.v0_1.messages.pres_request_approve import (
    PresRequestApprove,
)
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.protocols.present_proof.v1_0.manager import PresentationManager
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from asynctest import mock

TEST_PRES_EX_ID = "test-presentation_exchange_id"
TEST_CONN_ID = "test-connection-id"
TEST_SELF_ATTESTED_ATTRS = {}
TEST_REQUESTED_ATTRS = {}
TEST_REQUESTED_PREDS = {}
TEST_COMMENT = "test-comment"


@pytest.fixture
def message():
    """Message fixture."""
    yield PresRequestApprove(
        presentation_exchange_id=TEST_PRES_EX_ID,
        self_attested_attributes=TEST_SELF_ATTESTED_ATTRS,
        requested_attributes=TEST_REQUESTED_ATTRS,
        requested_predicates=TEST_REQUESTED_PREDS,
        comment=TEST_COMMENT,
    )


@pytest.fixture
def context(context, message):
    context.message = message
    yield context


@pytest.fixture
def record():
    yield PresExRecord(
        presentation_exchange_id=TEST_PRES_EX_ID, connection_id=TEST_CONN_ID
    )


@pytest.fixture
def conn_record():
    yield ConnRecord(connection_id=TEST_CONN_ID)


@pytest.mark.asyncio
async def test_handler(
    context,
    mock_responder,
    message,
    mock_get_connection,
    mock_get_pres_ex_record,
    record,
    conn_record,
):
    """Test PresRequestApprove handler."""
    mock_presentation_manager = mock.MagicMock(spec=PresentationManager)
    mock_presentation_manager.create_presentation = mock.CoroutineMock(
        return_value=(record, mock.MagicMock())
    )
    with mock_get_connection(test_module, conn_record), mock_get_pres_ex_record(
        PresRequestApprove, record
    ), mock.patch.object(
        test_module,
        "PresentationManager",
        mock.MagicMock(return_value=mock_presentation_manager),
    ):
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 2

    reply, _reply_args = mock_responder.messages.pop()
    assert reply.record.presentation_exchange_id == TEST_PRES_EX_ID

    _pres, pres_args = mock_responder.messages.pop()
    assert "connection_id" in pres_args
    assert pres_args["connection_id"] == TEST_CONN_ID
