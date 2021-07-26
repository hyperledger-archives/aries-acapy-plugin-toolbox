"""
Echo Agent.

The goal of this agent is to implement an agent that can create new static
connections, receive messages, and send messages while minimizing logic and,
therefore (hopefully) how much code needs to be maintained.
"""

from pydantic import BaseModel
from fastapi import FastAPI
from aries_staticagent import crypto

app = FastAPI()


class Keypair(BaseModel):
    public: str
    private: str


@app.get("/")
def read_root() -> Keypair:
    """Return root."""
    keypair_bytes = crypto.create_keypair()
    return Keypair(
        public=crypto.bytes_to_b58(keypair_bytes[0]),
        private=crypto.bytes_to_b58(keypair_bytes[1]),
    )
