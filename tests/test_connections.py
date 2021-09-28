import asyncio
from unittest.mock import patch

import pytest
from _pytest.fixtures import yield_fixture
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.event_bus import Event
from aries_cloudagent.core.profile import Profile
from asynctest import mock

import acapy_plugin_toolbox.connections as con
import acapy_plugin_toolbox.util as util


@pytest.mark.asyncio
async def test_chandler(profile):
    """Connections handler tester.
    
    Runs connections_event_handler() and returns 
    the output."""
    with patch.object(con, 'send_to_admins', 
    mock.CoroutineMock()) as mocked_send_to_admins:
        event = Event(
            f"acapy::record::{ConnRecord.RECORD_TOPIC}::{ConnRecord.State.RESPONSE}",
            ConnRecord(state=ConnRecord.State.RESPONSE).serialize()
        )
        
        await con.connections_event_handler(profile, event)
        mocked_send_to_admins.assert_called_once()

    
if __name__ == "__main__":
    pytest.run(test_chandler())
