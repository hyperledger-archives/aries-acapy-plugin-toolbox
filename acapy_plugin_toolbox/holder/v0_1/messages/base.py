from aries_cloudagent.messaging.agent_message import AgentMessage


class AdminHolderMessage(AgentMessage):
    """Admin Holder Protocol Message Base class."""

    protocol = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin-holder/0.1"
