from unittest.mock import patch

from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.event_bus import Event
from asynctest import mock
import pytest

import acapy_plugin_toolbox.connections as con


@pytest.mark.asyncio
async def test_chandler(profile):
    """Connections handler tester.

    Runs connections_event_handler() and returns
    the output."""
    with patch.object(
        con, "send_to_admins", mock.CoroutineMock()
    ) as mocked_send_to_admins:
        event_conn = Event(
            f"acapy::record::{ConnRecord.RECORD_TOPIC}::{ConnRecord.State.RESPONSE}::{ConnRecord.Protocol.RFC_0160}",
            ConnRecord(
                state=ConnRecord.State.RESPONSE,
                connection_protocol=ConnRecord.Protocol.RFC_0160,
            ).serialize(),
        )
        event_did = Event(
            f"acapy::record::{ConnRecord.RECORD_TOPIC}::{ConnRecord.State.COMPLETED}::{ConnRecord.Protocol.RFC_0023}",
            ConnRecord(
                state=ConnRecord.State.COMPLETED,
                connection_protocol=ConnRecord.Protocol.RFC_0023,
            ).serialize(),
        )

        await con.connections_event_handler(profile, event_conn)
        await con.connections_event_handler(profile, event_did)
        assert mocked_send_to_admins.call_count == 2


if __name__ == "__main__":
    pytest.run(test_chandler())
