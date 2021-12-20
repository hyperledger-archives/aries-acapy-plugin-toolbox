"""Test RequestPres message and handler."""
# pylint: disable=redefined-outer-name

import uuid
from aries_cloudagent.indy.models.proof_request import IndyProofRequest

from aries_cloudagent.messaging.request_context import RequestContext
from aries_cloudagent.messaging.responder import MockResponder
from aries_cloudagent.protocols.present_proof.v1_0.messages.presentation_request import (
    PresentationRequest,
)
import pytest

from acapy_plugin_toolbox.issuer import IssuerPresExchange, RequestPres
from acapy_plugin_toolbox import issuer as test_module

TEST_CONN_ID = uuid.uuid4()


@pytest.fixture
def message():
    """Message fixture."""
    yield RequestPres(
        connection_id=TEST_CONN_ID,
        proof_request=IndyProofRequest(
            requested_attributes={}, requested_predicates={}
        ),
        comment="comment",
    )


@pytest.fixture
def context(context, message):
    """Context fixture."""
    context.message = message
    yield context


@pytest.mark.asyncio
async def test_handler(
    context: RequestContext,
    mock_responder: MockResponder,
    message: RequestPres,
    mock_get_connection,
):
    """Test RequestPres handler."""
    with mock_get_connection(test_module):
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 2
    (req, req_recipient), (response, _) = mock_responder.messages
    assert isinstance(req, PresentationRequest)
    assert req.request_presentations_attach
    assert req_recipient == {"connection_id": str(TEST_CONN_ID)}
    assert isinstance(response, IssuerPresExchange)
    assert response.record.connection_id == str(TEST_CONN_ID)
