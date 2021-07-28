from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="Connection")


@attr.s(auto_attribs=True)
class Connection:
    """ """

    connection_id: str
    did: str
    verkey: str
    their_vk: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        connection_id = self.connection_id
        did = self.did
        verkey = self.verkey
        their_vk = self.their_vk

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connection_id": connection_id,
                "did": did,
                "verkey": verkey,
                "their_vk": their_vk,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        connection_id = d.pop("connection_id")

        did = d.pop("did")

        verkey = d.pop("verkey")

        their_vk = d.pop("their_vk")

        connection = cls(
            connection_id=connection_id,
            did=did,
            verkey=verkey,
            their_vk=their_vk,
        )

        connection.additional_properties = d
        return connection

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
