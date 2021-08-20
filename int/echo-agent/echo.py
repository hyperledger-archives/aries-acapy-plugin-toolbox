"""
Echo Agent.

The goal of this agent is to implement an agent that can create new static
connections, receive messages, and send messages while minimizing logic and,
therefore (hopefully) how much code needs to be maintained.

Required operations include:
- create static connection
- receive message
- retrieve messages
- send message
"""

from asyncio import Queue
import json
import logging
from typing import Dict, Iterable, List, Optional
from uuid import uuid4
from aries_staticagent.static_connection import StaticConnection, Target
from aries_staticagent.message import Message
from pydantic import BaseModel, Field
from fastapi import FastAPI, Body, HTTPException, Request
from aries_staticagent import crypto

# Logging
LOGGER = logging.getLogger("uvicorn.error." + __name__)

# Global state
connections: Dict[str, StaticConnection] = {}
recip_key_to_connection_id: Dict[str, str] = {}
messages: Dict[str, "Queue[Message]"] = {}


app = FastAPI(title="Echo Agent", version="0.1.0")


class NewConnection(BaseModel):
    seed: str = Field(..., example="00000000000000000000000000000000")
    endpoint: str
    their_vk: str


class Connection(BaseModel):
    connection_id: str
    did: str
    verkey: str
    their_vk: str


@app.post("/connection", response_model=Connection, operation_id="new_connection")
async def new_connection(new_connection: NewConnection):
    """Create a new static connection."""
    LOGGER.debug("Creating new connection from request: %s", new_connection)
    conn = StaticConnection.from_seed(
        seed=new_connection.seed.encode("ascii"),
        target=Target(
            endpoint=new_connection.endpoint, their_vk=new_connection.their_vk
        ),
    )
    connection_id = str(uuid4())
    connections[connection_id] = conn
    recip_key_to_connection_id[conn.verkey_b58] = connection_id
    result = Connection(
        connection_id=connection_id,
        did=conn.did,
        verkey=conn.verkey_b58,
        their_vk=new_connection.their_vk,
    )
    LOGGER.debug("Returning new connection: %s", result)
    return result


def _recipients_from_packed_message(message_bytes: bytes) -> Iterable[str]:
    """
    Inspect the header of the packed message and extract the recipient key.
    """
    try:
        wrapper = json.loads(message_bytes)
    except Exception as error:
        raise ValueError("Invalid packed message") from error

    recips_json = crypto.b64_to_bytes(wrapper["protected"], urlsafe=True).decode(
        "ascii"
    )

    try:
        recips_outer = json.loads(recips_json)
    except Exception as error:
        raise ValueError("Invalid packed message recipients") from error

    return [recip["header"]["kid"] for recip in recips_outer["recipients"]]


@app.post("/receive")
async def receive_message(request: Request):
    """Receive a new agent message and push onto the message queue."""
    message = await request.body()
    LOGGER.debug("Message received: %s", message)
    handled = False
    for recipient in _recipients_from_packed_message(message):
        if recipient in recip_key_to_connection_id:
            connection_id = recip_key_to_connection_id[recipient]
            LOGGER.debug(
                "Found connection %s for message recipient %s", connection_id, recipient
            )
            conn = connections[connection_id]
            unpacked = conn.unpack(message)
            LOGGER.debug("Unpacked message: %s", unpacked)
            if connection_id not in messages:
                messages[connection_id] = Queue()
            await messages[connection_id].put(unpacked)
            handled = True
    if not handled:
        LOGGER.warning("Received message that could not be handled: %s", message)


@app.get(
    "/retrieve/{connection_id}",
    response_model=List[Message],
    operation_id="retrieve_messages",
)
async def retreive_messages(connection_id: str):
    """Retrieve all received messages for recipient key."""
    if connection_id not in messages:
        raise HTTPException(
            status_code=404,
            detail=f"No messages found for connection id {connection_id}",
        )

    LOGGER.debug(
        "Retrieving messages for connection_id %s",
        connection_id,
    )
    queue = messages[connection_id]
    if not queue.empty():
        to_return = []
        while not queue.empty():
            to_return.append(queue.get_nowait())
            queue.task_done()
        LOGGER.debug("Returning messages: %s", to_return)
        return to_return
    else:
        return []


@app.get(
    "/wait-for/{connection_id}", response_model=Message, operation_id="wait_for_message"
)
async def wait_for_message(
    connection_id: str, thid: Optional[str] = None, msg_type: Optional[str] = None
):
    """Wait for a message matching criteria."""

    def _matcher(message: Message):
        """Matcher for messages."""
        thid_match = True if thid is None else message.thread["thid"] == thid
        msg_type_match = True if msg_type is None else message.type == msg_type
        return thid_match and msg_type_match

    if connection_id not in messages:
        if connection_id in connections:
            messages[connection_id] = Queue()
        else:
            raise HTTPException(
                status_code=404, detail=f"No connection id matching {connection_id}"
            )

    queue = messages[connection_id]
    while not queue.empty():
        message = queue.get_nowait()
        queue.task_done()
        if _matcher(message):
            LOGGER.debug("Found message: %s", message)
            return message
        else:
            LOGGER.info("Dropping message: %s", message)

    while True:
        message = await queue.get()
        queue.task_done()
        if _matcher(message):
            LOGGER.debug("Found message: %s", message)
            return message
        else:
            LOGGER.info("Dropping message: %s", message)


@app.post("/send/{connection_id}", operation_id="send_message")
async def send_message(connection_id: str, message: dict = Body(...)):
    """Send a message to connection identified by did."""
    LOGGER.debug("Sending message to %s: %s", connection_id, message)
    if connection_id not in connections:
        raise HTTPException(
            status_code=404, detail=f"No connection matching {connection_id} found"
        )
    conn = connections[connection_id]
    await conn.send_async(message)


class DebugInfo(BaseModel):
    connections: Dict[str, str]
    recip_key_to_connection_id: Dict[str, str]
    messages: Dict[str, str]


@app.get("/debug", response_model=DebugInfo)
async def debug_info():
    """Return agent state for debugging."""
    return DebugInfo(
        connections={k: str(v) for k, v in connections.items()},
        recip_key_to_connection_id=recip_key_to_connection_id,
        messages={k: repr(v) for k, v in messages.items()},
    )
