from acapy_client.models.indy_proof_request import IndyProofRequest
from acapy_client.models.indy_proof_request_requested_attributes import (
    IndyProofRequestRequestedAttributes,
)
from acapy_client.models.indy_proof_request_requested_predicates import (
    IndyProofRequestRequestedPredicates,
)
from acapy_client.models.v10_presentation_send_request_request import (
    V10PresentationSendRequestRequest,
)
from acapy_client.types import Unset
import pytest
from typing import cast
from acapy_client import Client
from acapy_client.models.conn_record import ConnRecord
from acapy_client.api.present_proof_v10 import send_proof_request

from tests.test_holder import issue_credential, issuer_holder_connection
from tests.conftest import connection


@pytest.mark.asyncio
async def test_presentation(
    backchannel: Client,
    issue_credential,
    issuer_holder_connection,
    wait_for_message,
    connection,
):
    """Test the presentation message and notification flows."""
    verifier, prover = issuer_holder_connection
    verifier = cast(ConnRecord, verifier)
    prover = cast(ConnRecord, prover)
    assert not isinstance(verifier.connection_id, Unset)
    assert not isinstance(prover.connection_id, Unset)
    proof_req = await send_proof_request.asyncio(
        client=backchannel,
        json_body=V10PresentationSendRequestRequest(
            connection_id=prover.connection_id,
            proof_request=IndyProofRequest(
                name="test-proof",
                requested_attributes=IndyProofRequestRequestedAttributes.from_dict(
                    {"attr_1_0": {"name": "attr_1_0"}}
                ),
                requested_predicates=IndyProofRequestRequestedPredicates(),
                version="0.1",
            ),
        ),
    )
    presentation_request_received = await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/presentation-request-received"
    )
    assert presentation_request_received["matching_credentials"]
    await connection.send_async(
        {
            "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/presentation-request-approve",
            "@id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "presentation_exchange_id": presentation_request_received[
                "presentation_exchange_id"
            ],
            "self_attested_attributes": {},
            "requested_attributes": {
                "attr_1_0": {
                    "cred_id": presentation_request_received["matching_credentials"][0][
                        "cred_info"
                    ]["referent"],
                    "revealed": True,
                }
            },
            "requested_predicates": {},
            "comment": "It's dangerous to go alone. Take this!",
        }
    )
    pres_sent = await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1/presentation-sent"
    )
    assert pres_sent["presentation_exchange_id"]
    await wait_for_message(
        msg_type="did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-issuer/0.1/presentation-received"
    )
