"""Test BasicMessage"""

import pytest
from aries_cloudagent.core.event_bus import Event

from acapy_plugin_toolbox import basicmessage as basicmessage_module


@pytest.fixture
def injection_context(profile):
    """Injection context fixture."""
    yield profile.context


@pytest.mark.asyncio
async def test_basic_message_event_handler_notify_admins(
    event_bus, profile, injection_context, mock_send_to_admins
):
    with mock_send_to_admins(basicmessage_module) as send_to_admins:
        await basicmessage_module.setup(injection_context)

        assert send_to_admins.message is None

        await event_bus.notify(
            profile,
            Event(
                "acapy::basicmessage::received",
                {
                    "connection_id": "connection-1",
                    "message_id": "test id",
                    "content": "Hello world",
                    "state": "received",
                },
            ),
        )

        assert send_to_admins.message
        assert send_to_admins.message.message.content == "Hello world"
