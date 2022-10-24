import json
import os.path
from copy import deepcopy
from typing import Any, TextIO

from PetroGeoSim.properties import Property  # RandomProperty, ResultProperty


class Region:
    """Serves as the container for all the Input and Result 'Properties'.

    _extended_summary_

    Attributes
    ----------
    name : str
        Name of the Region, also used in hashing (MUST be unique).
    composition : str | None, optional
        Description of layer composition, by default None.
    inputs : SeedSequence
        Dictionary containing Input (Random) Properties.
    results : Generator
        Dictionary containing Result Properties.

    Methods
    -------
    add_property(seed, num_samples)
        Represent the photo in the given colorspace.
    get_properties(n=1.0)
        Change the photo's gamma exposure.
    to_json(n=1.0)
        Change the photo's gamma exposure.
    from_json(n=1.0)
        Change the photo's gamma exposure.

    Raises
    ------
    KeyError
        _description_
    KeyError
        _description_
    """

    __slots__ = ("name", "composition", "inputs", "results")

    def __init__(
        self,
        name: str,
        composition: str | None = None,
    ) -> None:
        self.name = name
        self.composition = composition
        self.inputs = {}
        self.results = {}

    def __str__(self) -> str:
        return (
            f"Region {self.name}\n"
            f"Inputs: {', '.join(self.inputs.keys())}"
            f"Results: {', '.join(self.results.keys())}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Region) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return (other.name in self.inputs) or (other.name in self.results)

    def add_property(self, prop: Property) -> None:
        """
        Adds a Property to the Region.
        Also handles different types of Properties.
        """
        if prop in self:
            raise KeyError(
                f'Encountered duplicate Property "{prop.name}" '
                f'in Region "{self.name}"'
            )
        # if isinstance(prop, RandomProperty):
        #     self.inputs[prop.name] = prop
        # elif isinstance(prop, ResultProperty):
        #     self.results[prop.name] = prop
        # else:
        #     raise KeyError("Invalid Property type")

        if prop.prop_type == "input":
            self.inputs[prop.name] = prop
        elif prop.prop_type == "result":
            self.results[prop.name] = prop
        else:
            raise KeyError("Invalid Property type")

    def get_properties(
        self,
        attribute: str,
        include: tuple[str] | list[str] = ("inputs", "results")
    ) -> dict[str, Any]:
        """
        Returns a dictionary, containing a specified attribute of
        all Properties in a Region.
        """

        attributes = {}
        match include:
            case ["inputs", "results"] | ["results", "inputs"]:
                all_properties = {**self.inputs, **self.results}
            case "inputs":
                all_properties = self.inputs
            case "results":
                all_properties = self.results
            case _:
                raise ValueError("Invalid value encountered in `include`")

        for prop_name, prop in all_properties.items():
            if hasattr(prop, attribute):
                attributes[prop_name] = getattr(prop, attribute)

        return attributes

    def to_json(
        self,
        to_str: bool = True,
        exclude: tuple = ("name")
    ) -> str | None:
        """
        Serialize the 'Region' to a JSON with a filename matching
        the 'Region' name attribute.
        """

        json_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in self.__slots__
            if slot not in exclude
        }

        for prop_name, prop in self.inputs.items():
            json_dict['inputs'][prop_name] = prop.to_json()
        for prop_name, prop in self.results.items():
            json_dict['results'][prop_name] = prop.to_json()

        if to_str:
            return json_dict

        with open(f"Region {self.name}.json", "w", encoding='utf-8') as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO, **kwargs) -> "Region":
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding='utf-8') as fp:
                    json_dict = json.load(fp=fp)

        for prop_name, prop in json_dict['inputs'].items():
            json_dict['inputs'][prop_name] = Property.from_json(prop)
        for prop_name, prop in json_dict['results'].items():
            json_dict['results'][prop_name] = Property.from_json(prop)

        name = json_dict.pop("name", "region")
        reg = cls(name)
        for slot, value in json_dict.items():
            setattr(reg, slot, value)

        return reg
