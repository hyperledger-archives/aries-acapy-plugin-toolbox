"""Common fixtures for testing."""

import asyncio
import hashlib
import logging
import os
from typing import Iterator, Optional, Union

from acapy_backchannel import Client
from acapy_backchannel.api.connection import (
    create_static,
    delete_connection,
    set_metadata,
)
from acapy_backchannel.api.ledger import accept_taa, fetch_taa
from acapy_backchannel.api.wallet import create_did, set_public_did
from acapy_backchannel.models import (
    ConnectionMetadataSetRequest,
    ConnectionStaticRequest,
    ConnectionStaticResult,
    TAAAccept,
)
from acapy_backchannel.models.conn_record import ConnRecord
from acapy_backchannel.models.did import DID
from aries_staticagent import StaticConnection, Target
from aries_staticagent.message import Message
from aries_staticagent.utils import http_send
from echo_agent_client import Client as EchoClient
from echo_agent_client.api.default import (
    new_connection,
    retrieve_messages,
    send_message,
    wait_for_message as echo_wait_for_message,
)
from echo_agent_client.models import Connection as EchoConnection
from echo_agent_client.models.new_connection import NewConnection
from echo_agent_client.models.send_message_message import SendMessageMessage
from echo_agent_client.types import UNSET
import httpx
import pytest

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create a session scoped event loop.
    pytest.asyncio plugin provides a default function scoped event loop
    which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def host():
    """Hostname of agent under test."""
    return os.environ.get("AGENT_HOST", "localhost")


@pytest.fixture(scope="session")
def suite_host():
    """Hostname of agent under test."""
    return os.environ.get("SUITE_HOST", "localhost")


@pytest.fixture(scope="session")
def port():
    """Port of agent under test."""
    return os.environ.get("AGENT_PORT", 3000)


@pytest.fixture(scope="session")
def suite_port():
    """Port of agent under test."""
    return os.environ.get("SUITE_PORT", 3002)


@pytest.fixture(scope="session")
def backchannel_port():
    """Port of agent under test backchannel."""
    return os.environ.get("AGENT_BACKCHANNEL_PORT", 3001)


@pytest.fixture(scope="session")
def backchannel(host, backchannel_port):
    """Yield backchannel client."""
    yield Client(base_url="http://{}:{}".format(host, backchannel_port))


@pytest.fixture(scope="session")
def suite_seed():
    yield hashlib.sha256(b"acapy-plugin-toolbox-int-test-runner").hexdigest()[:32]


@pytest.fixture(scope="session")
def agent_seed():
    yield hashlib.sha256(b"acapy-plugin-toolbox-int-test-runner").hexdigest()[:32]


@pytest.fixture(scope="session")
def suite_endpoint():
    yield os.environ.get("SUITE_ENDPOINT", "http://localhost:3000")


@pytest.fixture(scope="session")
def agent_endpoint(host, port):
    yield "http://{}:{}".format(host, port)


@pytest.fixture(scope="session")
def agent_connection(
    suite_seed, agent_seed, suite_endpoint, backchannel
) -> Iterator[ConnectionStaticResult]:
    """Yield agent's representation of this connection."""

    # Create connection in agent under test
    create_result: Optional[ConnectionStaticResult] = create_static.sync(
        client=backchannel,
        json_body=ConnectionStaticRequest.from_dict(
            {
                "my_seed": agent_seed,
                "their_seed": suite_seed,
                "their_endpoint": suite_endpoint,
                "their_label": "test-runner",
            }
        ),
    )
    if not create_result:
        raise RuntimeError("Could not create static connection with agent under test")

    # Set admin metadata to enable access to admin protocols
    set_result = set_metadata.sync(
        client=backchannel,
        conn_id=create_result.record.connection_id,
        json_body=ConnectionMetadataSetRequest.from_dict(
            {"metadata": {"group": "admin"}}
        ),
    )
    if not set_result:
        raise RuntimeError("Could not set metadata on static connection")

    yield create_result

    delete_connection.sync(
        client=backchannel, conn_id=create_result.record.connection_id
    )


@pytest.fixture(scope="session")
def conn_record(agent_connection: ConnectionStaticResult):
    yield agent_connection.record


@pytest.fixture(scope="session")
def connection_id(conn_record: ConnRecord):
    yield conn_record.connection_id


class IntegrationTestConnection(StaticConnection):
    async def send_and_await_reply_async(
        self,
        msg: Union[dict, Message],
        *,
        return_route: str = "all",
        plaintext: bool = False,
        anoncrypt: bool = False,
        timeout: int = 1,
    ) -> Message:
        return await super().send_and_await_reply_async(
            msg,
            return_route=return_route,
            plaintext=plaintext,
            anoncrypt=anoncrypt,
            timeout=timeout,
        )


@pytest.fixture(scope="session")
def connection(agent_connection: ConnectionStaticResult, suite_seed: str):
    """Yield static connection to agent under test."""

    # Create and yield static connection
    yield IntegrationTestConnection.from_seed(
        seed=suite_seed.encode("ascii"),
        target=Target(
            endpoint=agent_connection.my_endpoint, their_vk=agent_connection.my_verkey
        ),
    )


@pytest.fixture(scope="session")
def echo_client(suite_host, suite_port):
    yield EchoClient(base_url=f"http://{suite_host}:{suite_port}")


@pytest.fixture(scope="session")
async def echo_connection(echo_client, suite_seed, agent_connection):
    yield await new_connection.asyncio(
        client=echo_client,
        json_body=NewConnection(
            seed=suite_seed,
            endpoint=agent_connection.my_endpoint,
            their_vk=agent_connection.my_verkey,
        ),
    )


@pytest.fixture(scope="session")
def asynchronously_received_messages(
    echo_client: EchoClient, echo_connection: EchoConnection
):
    """Get asynchronously recevied messages from the echo agent."""
    # Could wipe left over messages here
    async def _asynchronously_received_messages(timeout: int = 5):
        timed_client = echo_client.with_timeout(timeout)
        try:
            messages = await retrieve_messages.asyncio(
                client=timed_client, connection_id=echo_connection.connection_id
            )
        except httpx.ReadTimeout:
            raise Exception(
                "Retrieving asynchronously recevied messages timed out"
            ) from None

        return messages

    yield _asynchronously_received_messages
    # Could wipe remaining messages here


@pytest.fixture(scope="session")
def wait_for_message(echo_client: EchoClient, echo_connection: EchoConnection):
    """Get asynchronously recevied messages from the echo agent."""
    # Could wipe left over messages here
    async def _asynchronously_received_messages(
        *, thid: Optional[str] = None, msg_type: Optional[str] = None, timeout: int = 5
    ):
        timed_client = echo_client.with_timeout(timeout)
        try:
            return await echo_wait_for_message.asyncio(
                client=timed_client,
                connection_id=echo_connection.connection_id,
                thid=thid or UNSET,
                msg_type=msg_type or UNSET,
            )
        except httpx.ReadTimeout:
            raise Exception("Waiting for message timed out") from None

    yield _asynchronously_received_messages
    # Could wipe remaining messages here


@pytest.fixture(scope="session")
def send_via_echo(echo_client, echo_connection: EchoConnection):
    async def _send_via_echo(message: dict):
        await send_message.asyncio(
            client=echo_client,
            connection_id=echo_connection.connection_id,
            json_body=SendMessageMessage.from_dict(message),
        )

    yield _send_via_echo


@pytest.fixture(scope="session")
async def make_did(backchannel):
    """DID factory fixture"""

    async def _make_did():
        return (await create_did.asyncio(client=backchannel.with_timeout(15))).result

    yield _make_did
    # TODO create DID deletion method


@pytest.fixture(scope="session")
async def accepted_taa(backchannel):
    result = (await fetch_taa.asyncio(client=backchannel.with_timeout(15))).result
    result = await accept_taa.asyncio(
        client=backchannel,
        json_body=TAAAccept(
            mechanism="on_file",
            text=result.taa_record.text,
            version=result.taa_record.version,
        ),
    )


@pytest.fixture(scope="session")
async def endorser_did(make_did, backchannel, accepted_taa):
    """Endorser DID factory fixture"""
    did: DID = await make_did()
    LOGGER.info("Publishing DID through https://selfserve.indiciotech.io")
    response = httpx.post(
        url="https://selfserve.indiciotech.io/nym",
        json={"network": "testnet", "did": did.did, "verkey": did.verkey},
        timeout=15,
    )
    if response.is_error:
        raise Exception("Failed to publish DID:", response.text)

    LOGGER.info("DID Published")
    result = await set_public_did.asyncio_detailed(
        client=backchannel.with_timeout(15), did=did.did
    )
    assert result.status_code == 200
    yield did
