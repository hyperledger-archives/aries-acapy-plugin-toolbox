"""Common testing fixtures."""
from contextlib import contextmanager
import pytest
from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.messaging.request_context import RequestContext
from aries_cloudagent.messaging.responder import BaseResponder, MockResponder
from aries_cloudagent.core.event_bus import EventBus
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from asynctest import mock


@pytest.fixture
def mock_admin_connection():
    """Mock connection fixture."""
    connection = mock.MagicMock(spec=ConnRecord)
    connection.metadata_get = mock.CoroutineMock(return_value="admin")
    yield connection


@pytest.fixture
def event_bus():
    """Event bus fixture."""
    yield EventBus()


@pytest.fixture
def mock_responder():
    """Mock responder fixture."""
    yield MockResponder()


@pytest.fixture
def profile(event_bus, mock_responder):
    """Profile fixture."""
    yield InMemoryProfile.test_profile(
        bind={
            EventBus: event_bus,
            BaseResponder: mock_responder,
            ProtocolRegistry: ProtocolRegistry(),
        }
    )


@pytest.fixture
def context(profile, mock_admin_connection):
    """RequestContext fixture."""
    context = RequestContext(profile)
    context.connection_record = mock_admin_connection
    context.connection_ready = True
    yield context


@pytest.fixture
def mock_get_connection():
    """Mock get_connection on a module"""

    @contextmanager
    def _mock_get_connection(module, conn: ConnRecord = None):
        with mock.patch.object(
            module,
            "get_connection",
            mock.CoroutineMock(return_value=conn or mock.MagicMock(spec=ConnRecord)),
        ) as get_connection:
            yield get_connection

    yield _mock_get_connection


class MockSendToAdmins:
    """Mock send_to_admins method."""

    def __init__(self):
        self.message = None

    async def __call__(
        self, profile, message, responder, to_session_only: bool = False
    ):
        self.message = message


@pytest.fixture
def mock_send_to_admins():
    """Mock send to admins factory fixture.

    Benefit of making this a fixture is primarily for ease of use.
    """

    @contextmanager
    def _mock_send_to_admins(module):
        temp = module.send_to_admins
        module.send_to_admins = MockSendToAdmins()
        yield module.send_to_admins
        module.send_to_admins = temp

    yield _mock_send_to_admins
