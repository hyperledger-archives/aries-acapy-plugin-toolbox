"""Test PresGetMatchingCredentials message and handler."""

# pylint: disable=redefined-outer-name

import pytest
from aries_cloudagent.indy.holder import IndyHolder
from aries_cloudagent.indy.sdk.holder import IndySdkHolder
from asynctest import mock

from acapy_plugin_toolbox.decorators.pagination import Paginate
from acapy_plugin_toolbox.holder import PresExRecord
from acapy_plugin_toolbox.holder.v0_1 import (
    PresGetMatchingCredentials, PresMatchingCredentials, PresRequestApprove
)

TEST_PRES_EX_ID = "test-pres-ex-id"
TEST_CONN_ID = "test-connection-id"


@pytest.fixture
def message():
    """Message fixture."""
    yield PresGetMatchingCredentials(
        presentation_exchange_id=TEST_PRES_EX_ID,
        paginate=Paginate(10)
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
        presentation_exchange_id=TEST_PRES_EX_ID,
        connection_id=TEST_CONN_ID
    )


@pytest.mark.asyncio
async def test_handler(
    context, mock_responder, message, mock_get_pres_ex_record, record, holder
):

    holder.get_credentials_for_presentation_request_by_referent.return_value = ()
    with mock_get_pres_ex_record(
        PresRequestApprove, record
    ):
        await message.handle(context, mock_responder)

    assert len(mock_responder.messages) == 1
    reply, _reply_args = mock_responder.messages.pop()
    assert isinstance(reply, PresMatchingCredentials)
    assert reply.presentation_exchange_id == TEST_PRES_EX_ID
    assert reply.matching_credentials == ()
    assert reply.page.count == message.paginate.limit
