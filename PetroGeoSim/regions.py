import json
import os.path
from copy import deepcopy
from typing import Any, TextIO

from PetroGeoSim.properties import Property, RandomProperty, ResultProperty


class Region:

    __slots__ = ("name", "composition", "properties")  # "results"

    def __init__(
        self,
        name: str,
        composition: str | None = None,
    ) -> None:
        self.name = name
        self.composition = composition
        self.properties = {}
        # self.results = {}

    def __str__(self) -> str:
        return (
            f"Region {self.name}\n"
            f"Properties: {', '.join(self.properties.keys())}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Region) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return other.name in self.properties

    def add_property(self, prop: Property) -> None:
        if prop in self:
            raise KeyError(
                f'Encountered duplicate Property "{prop.name}" '
                f'in Region "{self.name}"'
            )

        self.properties[prop.name] = prop

    def get_properties(self, attribute: str) -> dict[str, Any]:
        attributes = {}

        for prop_name, prop in self.properties.items():
            if hasattr(prop, attribute):
                attributes[prop_name] = getattr(prop, attribute)

        return attributes

    def to_json(
        self,
        to_str: bool = True,
        exclude: tuple = ()
    ) -> str | None:
        slots = []
        for cls in reversed(type(self).__mro__):
            cls_slots = getattr(cls, '__slots__', None)
            if isinstance(cls_slots, str):
                slots.append(cls_slots)
            if isinstance(cls_slots, tuple):
                slots.extend(cls_slots)
        
        json_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in slots
            if slot not in exclude
        }  # deepcopy(vars(self))

        for prop_name, prop in self.properties.items():
            json_dict['properties'][prop_name] = prop.to_json()

        if to_str:
            return json_dict

        with open(f"Region {self.name}.json", "w", encoding='utf-8') as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO):
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding='utf-8') as fp:
                    json_dict = json.load(fp=fp)

        for prop_name, prop in json_dict['properties'].items():
            if 'random_number_function' in prop:
                json_dict['properties'][prop_name] = RandomProperty.from_json(prop)
            else:
                json_dict['properties'][prop_name] = ResultProperty.from_json(prop)

        name = json_dict.pop("name", "region")
        reg = cls(name)
        for slot, value in json_dict.items():
            setattr(reg, slot, value)

        # reg.__dict__ = json_dict.copy()
        return reg
