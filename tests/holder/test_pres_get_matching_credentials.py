"""Test PresGetMatchingCredentials message and handler."""

# pylint: disable=redefined-outer-name

import pytest
from acapy_plugin_toolbox.decorators.pagination import Paginate
from acapy_plugin_toolbox.holder import v0_1 as test_module
from acapy_plugin_toolbox.holder.v0_1 import (
    PresGetMatchingCredentials,
    PresMatchingCredentials,
    PresRequestApprove,
)
from acapy_plugin_toolbox.holder.v0_1.error import InvalidPresentationExchange
from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.indy.sdk.holder import IndySdkHolder
from aries_cloudagent.protocols.present_proof.v1_0.models.presentation_exchange import (
    V10PresentationExchange as PresExRecord,
)
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.storage.error import StorageNotFoundError
from asynctest import mock

TEST_PRES_EX_ID = "test-pres-ex-id"
TEST_CONN_ID = "test-connection-id"


@pytest.fixture
def message():
    """Message fixture."""
    yield PresGetMatchingCredentials(
        presentation_exchange_id=TEST_PRES_EX_ID, paginate=Paginate(10)
    )


@pytest.fixture
def holder():
    yield mock.MagicMock(IndySdkHolder)


@pytest.fixture
def context(context, message, holder):
    """Context fixture"""
    context.message = message
    context.injector.bind_instance(IndyHolder, holder)
    yield context


@pytest.fixture
def record():
    yield PresExRecord(
        presentation_exchange_id=TEST_PRES_EX_ID, connection_id=TEST_CONN_ID
    )


@pytest.mark.asyncio
async def test_handler(
    context, mock_responder, message, mock_get_pres_ex_record, record, holder
):

    holder.get_credentials_for_presentation_request_by_referent.return_value = ()
    with mock_get_pres_ex_record(PresRequestApprove, record):
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 1
    reply, _reply_args = mock_responder.messages.pop()
    assert isinstance(reply, PresMatchingCredentials)
    assert reply.presentation_exchange_id == TEST_PRES_EX_ID
    assert reply.matching_credentials == ()
    assert reply.page.count == message.paginate.limit


@pytest.mark.asyncio
async def test_handler_x_no_such_pres(
    context, mock_responder, message, mock_get_pres_ex_record, record, holder
):

    holder.get_credentials_for_presentation_request_by_referent.return_value = ()
    with mock.patch.object(
        test_module, "PresExRecord", mock.MagicMock()
    ) as mock_pres_ex_record, pytest.raises(InvalidPresentationExchange):
        mock_pres_ex_record.retrieve_by_id = mock.CoroutineMock(
            side_effect=StorageNotFoundError
        )
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 1
    reply, _reply_args = mock_responder.messages.pop()
    assert isinstance(reply, ProblemReport)


@pytest.mark.asyncio
async def test_handler_x_pres_invalid_state(
    context, mock_responder, message, mock_get_pres_ex_record, record, holder
):

    holder.get_credentials_for_presentation_request_by_referent.return_value = ()
    with mock.patch.object(
        test_module, "PresExRecord", mock.MagicMock()
    ) as mock_pres_ex_record, pytest.raises(InvalidPresentationExchange):
        mock_pres_ex_record.retrieve_by_id = mock.CoroutineMock(
            return_value=mock.MagicMock(state="not request_received")
        )
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 1
    reply, _reply_args = mock_responder.messages.pop()
    assert isinstance(reply, ProblemReport)
