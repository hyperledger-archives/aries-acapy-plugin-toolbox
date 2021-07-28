from typing import Any, Dict, List, Type, TypeVar

import attr

from ..models.debug_info_connections import DebugInfoConnections
from ..models.debug_info_messages import DebugInfoMessages
from ..models.debug_info_recip_key_to_connection_id import DebugInfoRecipKeyToConnectionId

T = TypeVar("T", bound="DebugInfo")


@attr.s(auto_attribs=True)
class DebugInfo:
    """ """

    connections: DebugInfoConnections
    recip_key_to_connection_id: DebugInfoRecipKeyToConnectionId
    messages: DebugInfoMessages
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        connections = self.connections.to_dict()

        recip_key_to_connection_id = self.recip_key_to_connection_id.to_dict()

        messages = self.messages.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connections": connections,
                "recip_key_to_connection_id": recip_key_to_connection_id,
                "messages": messages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        connections = DebugInfoConnections.from_dict(d.pop("connections"))

        recip_key_to_connection_id = DebugInfoRecipKeyToConnectionId.from_dict(d.pop("recip_key_to_connection_id"))

        messages = DebugInfoMessages.from_dict(d.pop("messages"))

        debug_info = cls(
            connections=connections,
            recip_key_to_connection_id=recip_key_to_connection_id,
            messages=messages,
        )

        debug_info.additional_properties = d
        return debug_info

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
