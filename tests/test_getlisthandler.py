from unittest.mock import patch

import pytest
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.messaging.responder import MockResponder
from asynctest import mock

import acapy_plugin_toolbox.connections as con


@pytest.fixture
def message():
    """Message fixture"""
    yield con.GetList()


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
async def test_getlisthandler(context, responder):
    """GetListHandler test.

    A unit test for the GetListHandler class.
    """
    handler = con.GetListHandler()

    with patch.object(ConnRecord, "query", mock.CoroutineMock()):

        await handler.handle(context, responder)
        conn_list, _ = responder.messages[0]
        assert isinstance(conn_list, con.List)
