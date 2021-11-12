from unittest.mock import patch
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError

import pytest
from _pytest.fixtures import yield_fixture
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.messaging.responder import MockResponder
from asynctest import mock

import acapy_plugin_toolbox.connections as con


@pytest.fixture
def message():
    """Message fixture"""
    yield con.Delete(connection_id="test_conn_id")


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
async def test_deletehandler(context, responder):
    """DeleteHandler test.

    A unit test for the DeleteHandler class."""
    handler = con.DeleteHandler()
    connection = mock.MagicMock(spec=ConnRecord)
    connection.connection_id = "conn_id"

    with patch.object(
        ConnRecord, "retrieve_by_id", mock.CoroutineMock(return_value=connection)
    ) as mocked_retrieve:

        await handler.handle(context, responder)
        assert responder.messages


@pytest.mark.asyncio
async def test_delhandler_badconnid(context, responder):
    """DeleteHandler bad connection test.

    A unit test for the message.connection_id
    == connection_record.connection_id error
    of the DeleteHandler class."""
    handler = con.DeleteHandler()

    context.message.connection_id = "test_id"
    context.connection_record.connection_id = "test_id"

    await handler.handle(context, responder)
    (message, _), *_ = responder.messages
    assert isinstance(message, ProblemReport)
    assert message.description == {"en": "Current connection cannot be deleted."}


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
