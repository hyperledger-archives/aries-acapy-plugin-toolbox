"""Common fixtures for testing."""

import asyncio
from contextlib import suppress
import os
import base64
from typing import Optional
import pytest
import hashlib

from acapy_backchannel import Client
from acapy_backchannel.api.connection import (
    create_static,
    set_metadata,
)
from acapy_backchannel.models import (
    ConnectionStaticRequest,
    ConnectionStaticResult,
    ConnectionMetadataSetRequest,
)

from aries_staticagent import StaticConnection, Target

from . import BaseAgent


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


# 3. Make the connection fixture take in agent as a parameter
# and yield agent.connection, since the connection creation was moved to the agent fixture
@pytest.fixture(scope="session")
def connection(
    host: str, port: int, suite_host: str, suite_port: int, backchannel: Client
):
    """Yield static connection to agent under test."""
    # Create static connection in agent under test
    test_runner_seed = hashlib.sha256(
        b"acapy-plugin-toolbox-int-test-runner"
    ).hexdigest()[:32]
    agent_seed = hashlib.sha256(b"acapy-plugin-toolbox-int-test").hexdigest()[:32]
    create_result: Optional[ConnectionStaticResult] = create_static.sync(
        client=backchannel,
        json_body=ConnectionStaticRequest(
            my_seed=agent_seed,
            their_seed=test_runner_seed,
            their_endpoint="http://{}:{}".format(suite_host, suite_port),
            their_label="test-runner",
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

    # Create and yield static connection
    yield StaticConnection.from_seed(
        seed=test_runner_seed.encode("ascii"),
        target=Target(
            endpoint=create_result.my_endpoint, their_vk=create_result.my_verkey
        ),
    )

    yield agent.connection  # added


# 2. Create a new fixture in conftest.py for agent or similar
# and do this chunk in it, moving logic from the connection fixture
@pytest.fixture(scope="session")
def agent(
    suite_host, suite_port, connection: StaticConnection
):  # name of function? take backchannel: Client as a parameter?
    yield BaseAgent(suite_host, suite_port, connection)


# 4. Yank this fixture from agent-testing and put into our conftest.py
@pytest.fixture(scope="session", autouse=True)
async def http_endpoint(agent: BaseAgent):
    """Start up agent and yield a connection to it."""
    server_task = asyncio.ensure_future(agent.start_async())

    yield

    server_task.cancel()
    with suppress(asyncio.CancelledError):
        await server_task
    await agent.cleanup()
