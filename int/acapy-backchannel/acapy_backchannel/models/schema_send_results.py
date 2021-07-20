from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.schema_send_results_txn import SchemaSendResultsTxn
from ..models.schema_sent import SchemaSent
from ..types import UNSET, Unset

T = TypeVar("T", bound="SchemaSendResults")


@attr.s(auto_attribs=True)
class SchemaSendResults:
    """ """

    sent: SchemaSent
    txn: Union[Unset, SchemaSendResultsTxn] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        sent = self.sent.to_dict()

        txn: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.txn, Unset):
            txn = self.txn.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sent": sent,
            }
        )
        if txn is not UNSET:
            field_dict["txn"] = txn

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        sent = SchemaSent.from_dict(d.pop("sent"))

        _txn = d.pop("txn", UNSET)
        txn: Union[Unset, SchemaSendResultsTxn]
        if isinstance(_txn, Unset):
            txn = UNSET
        else:
            txn = SchemaSendResultsTxn.from_dict(_txn)

        schema_send_results = cls(
            sent=sent,
            txn=txn,
        )

        schema_send_results.additional_properties = d
        return schema_send_results

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
