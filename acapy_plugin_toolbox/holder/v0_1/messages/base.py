from aries_cloudagent.messaging.agent_message import AgentMessage


class AdminHolderMessage(AgentMessage):
    """Admin Holder Protocol Message Base class."""

    protocol = "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-holder/0.1"
