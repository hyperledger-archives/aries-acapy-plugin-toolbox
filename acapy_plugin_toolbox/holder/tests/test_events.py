"""Test holder event handlers."""

# pylint: disable=redefined-outer-name

import pytest
from aries_cloudagent.core.event_bus import EventBus, Event
from aries_cloudagent.core.in_memory import InMemoryProfile
from aries_cloudagent.core.profile import Profile
from aries_cloudagent.core.protocol_registry import ProtocolRegistry
from aries_cloudagent.messaging.responder import BaseResponder, MockResponder
from aries_cloudagent.protocols.issue_credential.v1_0.models.credential_exchange import V10CredentialExchange
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import V10PresentationExchange
from asynctest import mock

from .. import v0_1 as test_module


@pytest.fixture
def event_bus():
    """Event bus fixture."""
    yield EventBus()


@pytest.fixture
def profile(event_bus):
    """Profile fixture."""
    holder = mock.MagicMock()
    holder.get_credentials_for_presentation_request_by_referent = mock.CoroutineMock()
    yield InMemoryProfile.test_profile(bind={
        EventBus: event_bus,
        BaseResponder: MockResponder(),
        ProtocolRegistry: ProtocolRegistry(),
        test_module.IndyHolder: holder
    })


@pytest.fixture
def context(profile):
    """Context fixture."""
    yield profile.context


class MockSendToAdmins:
    """Mock send_to_admins method."""
    def __init__(self):
        self.message = None

    async def __call__(self, session, message, responder):
        self.message = message


@pytest.fixture
def mock_send_to_admins():
    temp = test_module.send_to_admins
    test_module.send_to_admins = MockSendToAdmins()
    yield test_module.send_to_admins
    test_module.send_to_admins = temp


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "handler, topic",
    [
        ("issue_credential_event_handler", V10CredentialExchange.WEBHOOK_TOPIC),
        ("present_proof_event_handler", V10PresentationExchange.WEBHOOK_TOPIC)
    ]
)
async def test_events_subscribed_and_triggered(
    profile, context, event_bus, handler, topic
):
    """Test events are correctly registered and triggered."""
    with mock.patch.object(
        test_module,
        handler,
        mock.CoroutineMock()
    ) as mock_event_handler:
        await test_module.setup(context)
        await event_bus.notify(profile, Event(topic, {"test": "payload"}))
        mock_event_handler.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "handler, state, message",
    [
        (
            test_module.issue_credential_event_handler,
            V10CredentialExchange.STATE_OFFER_RECEIVED,
            test_module.CredOfferRecv
        ),
        (
            test_module.issue_credential_event_handler,
            V10CredentialExchange.STATE_CREDENTIAL_RECEIVED,
            test_module.CredReceived
        ),
        (
            test_module.present_proof_event_handler,
            V10PresentationExchange.STATE_REQUEST_RECEIVED,
            test_module.PresRequestReceived
        )
    ]
)
async def test_message_sent_on_correct_state(
    profile, mock_send_to_admins, handler, state, message
):
    """Test message sent on handle given correct state."""
    event = Event("anything", {"state": state})
    await handler(profile, event)
    assert isinstance(mock_send_to_admins.message, message)
