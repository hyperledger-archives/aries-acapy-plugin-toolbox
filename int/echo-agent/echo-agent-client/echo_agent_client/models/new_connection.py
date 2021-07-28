from typing import Any, Dict, List, Type, TypeVar

import attr

T = TypeVar("T", bound="NewConnection")


@attr.s(auto_attribs=True)
class NewConnection:
    """ """

    seed: str
    endpoint: str
    their_vk: str
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        seed = self.seed
        endpoint = self.endpoint
        their_vk = self.their_vk

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "seed": seed,
                "endpoint": endpoint,
                "their_vk": their_vk,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        seed = d.pop("seed")

        endpoint = d.pop("endpoint")

        their_vk = d.pop("their_vk")

        new_connection = cls(
            seed=seed,
            endpoint=endpoint,
            their_vk=their_vk,
        )

        new_connection.additional_properties = d
        return new_connection

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
