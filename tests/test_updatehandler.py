from unittest.mock import patch

import pytest
from _pytest.fixtures import yield_fixture
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.messaging.responder import MockResponder
from asynctest import mock

import acapy_plugin_toolbox.connections as con


@pytest.fixture
def message():
    """Message fixture"""
    yield con.Update(connection_id="test_conn_id")


@pytest.fixture
def context(context, message):
    """RequestContext fixture."""
    context.message = message
    yield context


@pytest.fixture
def responder():
    """Responder fixture."""
    return MockResponder()


@pytest.mark.asyncio
async def test_updatehandler(context, responder):
    """UpdateHandler test.

    A unit test for the UpdateHandler class."""
    handler = con.UpdateHandler()
    connection = mock.MagicMock(spec=ConnRecord)
    connection.save = mock.CoroutineMock()
    connection.their_label = "their_label"
    connection.my_did = "my_did"
    connection.their_did = "their_did"
    connection.state = "state"

    with patch.object(
        MockResponder, "send_reply", mock.CoroutineMock()
    ) as mocked_reply, patch.object(
        ConnRecord, "retrieve_by_id", mock.CoroutineMock(return_value=connection)
    ) as mocked_retrieve:

        await handler.handle(context, responder)
        mocked_reply.assert_called_once()


@pytest.mark.asyncio
async def test_storageerror(context, responder):
    """DeleteHandler StorageError test.

    A unit test for the StorageNotFound exception
    of the DeleteHandler class."""
    handler = con.DeleteHandler()
    responder.side_effect = StorageNotFoundError
    await handler.handle(context, responder)

    (message, _), *_ = responder.messages
    assert isinstance(message, ProblemReport)
    assert message.description["en"] == "Connection not found."
