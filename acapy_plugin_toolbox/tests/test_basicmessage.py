"""Test BasicMessage"""
from typing import Mapping

import pytest
from aries_cloudagent.admin.request_context import AdminRequestContext
from aries_cloudagent.core.event_bus import Event, EventBus
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.responder import BaseResponder, MockResponder
from aries_cloudagent.protocols.basicmessage.v1_0.messages.basicmessage import (
    BasicMessage
)
from asynctest import mock

from .. import basicmessage as basicmessage_module


@pytest.fixture
def event_bus():
    """Event bus fixture."""
    yield EventBus()


@pytest.fixture
def profile(event_bus):
    """Context fixture."""
    yield InMemoryProfile.test_profile(bind={
        EventBus: event_bus,
        BaseResponder: MockResponder(),
        ProtocolRegistry: ProtocolRegistry(),
    })


@pytest.fixture
def context(profile):
    yield profile.context


class MockSendToAdmins:
    """Mock send_to_admins method."""

    def __init__(self):
        self.message = None

    async def __call__(
        self, session, message, responder, to_session_only: bool = False
    ):
        self.message = message


@pytest.fixture
def mock_send_to_admins():
    temp = basicmessage_module.send_to_admins
    basicmessage_module.send_to_admins = MockSendToAdmins()
    yield basicmessage_module.send_to_admins
    basicmessage_module.send_to_admins = temp


@pytest.mark.asyncio
async def test_basic_message_event_handler_notify_admins(
    mock_send_to_admins, event_bus, profile, context
):
    await basicmessage_module.setup(context)

    assert mock_send_to_admins.message == None

    await event_bus.notify(
        profile,
        Event(
            "basicmessages",
            {
                "connection_id": "connection-1",
                "message_id": "test id",
                "content": "Hello world",
                "state": "received",
            },
        ),
    )

    assert mock_send_to_admins.message.message.content == "Hello world"
