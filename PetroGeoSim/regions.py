import json
import os.path
from copy import deepcopy
from typing import Any, TextIO

from numpy.random import SeedSequence

from PetroGeoSim.properties import Property


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
    add_properties(seed, num_samples)
        Represent the photo in the given colorspace.
    get_properties(attribute)
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
            f"REGION {self.name}\n"
            f"* Composition: {self.composition}\n"
            f"* Inputs: {', '.join(self.inputs.keys())}\n"
            f"* Results: {', '.join(self.results.keys())}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Region) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return (other.name in self.inputs) or (other.name in self.results)

    def add_properties(self, *props: tuple[Property]) -> None:
        """Add a single or multiple Properties to the Region.

        Also handles different types of Properties.

        Parameters
        ----------
        *props : tuple[Property]
            Positional arguments of defined `Property` objects.
        """

        for prop in props:
            if prop in self:
                raise KeyError(
                    f'Encountered duplicate Property "{prop.name}" '
                    f'in Region "{self.name}"'
                )

            if prop.prop_type == "input":
                self.inputs[prop.name] = prop
            elif prop.prop_type == "result":
                self.results[prop.name] = prop
            else:
                raise KeyError("Invalid Property type")

    def get_properties(
        self,
        attribute: str,
        include: tuple[str] | list[str] = ("inputs", "results"),
        variable_key: bool = False
    ) -> dict[str, Any]:
        """Returns a dictionary of a specified Properties' attribute.

        The attribute is collected for all Properties in the Region.

        Parameters
        ----------
        attribute : str
            The attribute to collect, used in getattr().
        include : tuple[str] | list[str], optional
            What Properties to include in the dictionary:
            results, inputs or both, by default ("inputs", "results").
        variable_key: bool, optional
            Whether the dictionary keys should be names of properties
            or variables, by default False.

        Returns
        -------
        dict[str, Any]
            A dictionary with structures:
            Property -> Attribute.

        Raises
        ------
        ValueError
            _description_
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

        for prop in all_properties.values():
            if hasattr(prop, attribute):
                key = prop.name if not variable_key else prop.variable
                attributes[key] = getattr(prop, attribute)

        return attributes

    def update_properties(self, seed: SeedSequence, num_samples: int) -> None:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        seed : SeedSequence
            _description_
        num_samples : int
            _description_
        """

        for prop in self.inputs.values():
            prop.distribution.update(seed, num_samples)

    def update(self, **update_kwargs: dict) -> None:
        """_summary_

        _extended_summary_

        Raises
        ------
        AttributeError
            _description_
        """

        for attr, val in update_kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, val)
            else:
                raise AttributeError(f'Region has no attribute "{attr}".')

    def serialize(self, exclude: tuple | list = ("name")) -> dict:
        """Serializes the `Region` to a dictionary.

        The primary method used in all other serialization types: to_json etc.

        Parameters
        ----------
        exclude : tuple | list, optional
            Attributes to not use during serialization, by default ("name")

        Returns
        -------
        dict
            A serialized dictionary.
        """

        serial_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in self.__slots__
            if slot not in exclude
        }

        # Continue the serialization down the hierarchy
        for prop_name, prop in self.inputs.items():
            serial_dict["inputs"][prop_name] = prop.serialize()
        for prop_name, prop in self.results.items():
            serial_dict["results"][prop_name] = prop.serialize()

        return serial_dict

    def to_json(self, **serialize_kwargs) -> None:
        """Serializes the `Region` to a JSON file.

        The generated file has a name `{Region.name}.json`.

        Parameters
        ----------
        **serialize_kwargs : dict
            Keyword arguments to pass on to serialize()
        """

        with open(f"Region {self.name}.json", "w", encoding="utf-8") as fp:
            json.dump(self.serialize(**serialize_kwargs), fp=fp, indent=4)

    @classmethod
    def deserialize(cls, serial_dict: TextIO, **kwargs) -> "Region":
        """_summary_

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            _description_

        Returns
        -------
        Region
            _description_
        """

        if not isinstance(serial_dict, dict):
            raise TypeError(
                "Can't perform deserialization from a non dictionary type."
            )

        # Continue the deserialization down the hierarchy
        # Inputs deserialization and calculation loop
        for prop_name, prop in serial_dict["inputs"].items():
            prop["name"] = prop_name
            inited_prop = Property.deserialize(prop, **kwargs)
            inited_prop.run_calculation()
            serial_dict["inputs"][prop_name] = inited_prop
        # Results deserialization and calculation loop
        for prop_name, prop in serial_dict["results"].items():
            prop["name"] = prop_name
            inited_prop = Property.deserialize(prop)
            inited_prop.run_calculation(
                **{prop.variable: prop.values
                   for prop in serial_dict["inputs"].values()
                   }
            )
            serial_dict["results"][prop_name] = inited_prop

        # Region object creation
        name = serial_dict.pop("name", "region")
        reg = cls(name)
        for slot, value in serial_dict.items():
            setattr(reg, slot, value)

        return reg

    @classmethod
    def from_json(cls, io: TextIO) -> "Region":
        """_summary_

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            _description_

        Returns
        -------
        Region
            _description_

        Raises
        ------
        FileNotFoundError
            _description_
        """

        if not os.path.isfile(io):
            raise FileNotFoundError("No such file or directory exists.")

        with open(io, "r", encoding="utf-8") as fp:
            serial_dict = json.load(fp=fp)

        return cls.deserialize(serial_dict)
