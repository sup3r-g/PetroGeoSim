import json
import os.path
import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable, Iterable, TextIO

import numpy as np
from numpy.random import SeedSequence

from PetroGeoSim.distributions import DISTRIBUTIONS_KWARGS
from PetroGeoSim.properties import Property
from PetroGeoSim.regions import Region

split_pat = re.compile(r"[\|\\\t _,/:;]+")


class Model:
    """Main container class that houses 'Regions' and their 'Properties'.

    If 'Simulation' is not defined it is the top container.

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    KeyError
        _description_
    KeyError
        _description_
    TypeError
        _description_
    KeyError
        _description_
    TypeError
        _description_
    TypeError
        _description_
    KeyError
        _description_
    """

    __slots__ = ("name", "seed", "num_samples", "results", "regions")

    def __init__(
        self, name: str, seed: int | None = None, num_samples: int = 10000
    ) -> None:
        self.name = name
        self.seed = SeedSequence(seed)
        self.num_samples = num_samples
        self.results = {}
        self.regions = {}

    def __str__(self) -> str:
        props = self.get_all_properties('name', invert_dict=True)
        return (
            f'MODEL "{self.name}"\n'
            f"* Seed: {self.seed.entropy}\n"
            f"* Number of samples: {self.num_samples}\n"
            f"* Regions: {', '.join(self.regions.keys())}\n"
            f"* Properties: {', '.join(props)}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Model) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return other.name in self.regions

    def add_regions(self, *regions: tuple[Region]) -> None:
        """Add a single or multiple Regions to the Model.

        Parameters
        ----------
        *regions : tuple[Region]
            Positional arguments of defined `Region` objects.

        Raises
        ------
        KeyError
            Can't add a `Region` with the same name.
        """

        for region in regions:
            if region in self:
                raise KeyError(
                    f'Encountered duplicate Region "{region.name}" '
                    f'in Model "{self.name}"'
                )

            # Resets all properties' values and updates distribution attributes
            for prop in region.inputs.values():  # reset_region() ???
                prop.distribution.update(self.seed, self.num_samples)
                prop.values = 0
            self.regions[region.name] = region

    def add_properties(
        self,
        *props_args: tuple[Property],
        **props_kwargs: dict[str, list[Property] | tuple[Property]],
    ) -> None:
        """Add a single or multiple Properties to the Model.

        Properties are passed as a dictionary.

        Parameters
        ----------
        *props_args : tuple[Property]
            Positional arguments of defined `Property` objects.
        **properties_kwargs : dict[str, list[Property] | tuple[Property]]
            Keyword arguments with the following structure:
            * Keys - names of `Region`s;
            * Values - defined `Property` objects.

        Raises
        ------
        TypeError
            Supplied positional or keyword arguments were not found.
        """

        # Resets the spawned children count
        self.seed = SeedSequence(self.seed.entropy)

        # Handles the positional arguments
        if props_args:
            for region in self.regions.values():
                region.add_properties(*deepcopy(props_args))
                region.update_properties(self.seed, self.num_samples)

        # Handles the keyword arguments
        if props_kwargs:
            for reg, props in props_kwargs.items():
                if reg not in self.regions:
                    raise KeyError(
                        f'Region "{reg}" not found in Model "{self.name}"'
                    )
                if not isinstance(props, Iterable):  # string case handler
                    props = (props,)

                region = self.regions[reg]
                region.add_properties(*deepcopy(props))
                region.update_properties(self.seed, self.num_samples)

    def get_all_properties(
        self,
        attribute: str,
        include: str | tuple[str] | list[str] = ("inputs", "results"),
        invert_dict: bool = False
    ) -> dict[str, dict]:
        """Returns a dictionary of a specified Properties' attribute.

        The attribute is collected for all Properties across all
        Regions in the Model.

        Parameters
        ----------
        attribute : str
            The attribute to collect, used in getattr()
        include: str | tuple[str] | list[str], optional
            What Properties to include in the dictionary:
            results, inputs or both, by default ("inputs", "results")
        invert : bool, optional
            Invert the dictionary: Property -> Region
            instead of Region -> Property, by default False

        Returns
        -------
        dict[str, dict]
            A nested dictionary with structures:
            1) Region -> Property -> Attribute
            2) Property -> Region -> Attribute
        """

        all_properties = {}
        attributes = defaultdict(dict)

        for reg_name, reg in self.regions.items():
            all_properties[reg_name] = reg.get_properties(attribute, include)
            if invert_dict:
                for prop_id, attr in all_properties[reg_name].items():
                    attributes[prop_id][reg_name] = attr

        if invert_dict:
            return dict(attributes)

        return all_properties

    def get_result(
        self,
        function: Callable[[list | tuple], list[float] | tuple[float]] = np.sum
    ) -> dict[str, list[float]]:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        function : Callable[[list | tuple], list[float] | tuple[float]], optional
            _description_, by default numpy.sum.

        Returns
        -------
        dict[str, list[float]]
            _description_.
        """

        initial_result = self.get_all_properties(
            "values", include="results", invert_dict=True
        )

        # Apply the function for all results only to their values
        for res_name, res in initial_result.items():
            self.results[res_name] = function(
                tuple(res.values()), axis=0
            )

        return self.results

    def make_config(self, user_input: bool = True) -> dict[str, Any]:
        """Makes the config for the run() method.

        _extended_summary_

        Parameters
        ----------
        user_input : bool, optional
            Whether to ask for user input or not, by default True

        Returns
        -------
        dict[str, Any]
            A dictionary containing the full config or just the parameters without values
        """

        config = {}
        for reg_name, reg in self.regions.items():
            props = defaultdict(dict)
            for prop_name, prop in reg.inputs.items():
                if user_input:
                    # With user input
                    param_hint = ", ".join(
                        DISTRIBUTIONS_KWARGS[prop.distribution.name]
                    )
                    params_str = input(
                        f"Input distribution parameters for ( {param_hint} ) "
                        f"of Property {prop_name} in Region {reg_name}"
                    )
                    for param, value in zip(
                        DISTRIBUTIONS_KWARGS[prop.distribution.name],
                        re.split(split_pat, params_str),
                    ):
                        props[prop_name][param] = float(value)
                else:
                    # Without user input
                    props[prop_name] = DISTRIBUTIONS_KWARGS[
                        prop.distribution.name
                    ]

            config[reg_name] = dict(props)

        return config

    def check_config(self, config: dict[str, Any]) -> bool:
        """Checks whether the supplied config is correct.

        It compares it with the internally generated one,
        using the `config_maker()`.

        Parameters
        ----------
        config : dict[str, Any]
            A nested dictionary with the following structure:
            Region -> Property -> Ditsribution parameters {key: values}

        Returns
        -------
        bool
            True if the config is valid, False otherwise.
        """

        config_test = deepcopy(config)

        for reg_name, reg in config_test.items():
            for prop_name, prop in reg.items():
                config_test[reg_name][prop_name] = set(prop.keys())

        # make_config() uses sets
        return config_test == self.make_config(user_input=False)

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
                raise AttributeError(f'Model has no attribute "{attr}".')

    def run(self, config: dict[str, Any]) -> None:
        """Runs all calculations in the Model

        Samples all Input 'Properties' from defined distributions and
        calculates all Result 'Properties'.

        Parameters
        ----------
        config : dict[str, Any]
            A nested dictionary with the following structure:
            Region -> Property -> Ditsribution parameters {key: values}

        Raises
        ------
        KeyError
            The check_config() found a problem, config check failed.
        """

        if not self.check_config(config):
            raise KeyError(
                "Invalid key is present or a key is missing in the config"
            )

        for reg_name, reg in self.regions.items():
            # Inputs calculation loop
            for prop_name, prop in reg.inputs.items():
                result_property_config = config[reg_name][prop_name]
                prop.run_calculation(**result_property_config)
            # Results calculation loop
            for prop_name, prop in reg.results.items():
                prop.run_calculation(
                    **reg.get_properties(
                        "values", include="inputs", variable_key=True
                    )
                )

    def serialize(self, exclude: tuple | list = ("results", )) -> dict:
        """Serializes the `Model` to a dictionary.

        The main method used in all other serialization types: to_json etc.

        Parameters
        ----------
        exclude : tuple | list, optional
            Attributes to not use during serialization, by default ().

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

        # Handle special serialization cases
        if "seed" not in exclude:
            serial_dict["seed"] = serial_dict["seed"].entropy

        # Continue the serialization down the hierarchy
        for reg_name, reg in self.regions.items():
            serial_dict["regions"][reg_name] = reg.serialize()

        return serial_dict

    def to_json(self, **serialize_kwargs) -> None:
        """Serializes the `Model` to a JSON file.

        The generated file has a name `{Model.name}.json`.

        Parameters
        ----------
        **serialize_kwargs : dict
            Keyword arguments to pass on to serialize()
        """

        with open(f"Model {self.name}.json", "w", encoding="utf-8") as fp:
            json.dump(self.serialize(**serialize_kwargs), fp=fp, indent=4)

    @classmethod
    def deserialize(cls, serial_dict: TextIO) -> "Model":
        """Creates/Deserializes the Model from a dictionary.

        The main method used in all other deserialization types: from_json etc.

        Parameters
        ----------
        io : TextIO
            A dictionary with the necessary data.

        Returns
        -------
        Model
            An initialized Model instance.
        """

        if not isinstance(serial_dict, dict):
            raise TypeError(
                "Can't perform deserialization from a non dictionary type."
            )

        # Handle special deserialization cases
        serial_dict["seed"] = SeedSequence(serial_dict["seed"])

        # Continue the deserialization down the hierarchy
        for reg_name, reg in serial_dict["regions"].items():
            serial_dict["regions"][reg_name] = Region.deserialize(
                reg, seed=serial_dict["seed"],
                num_samples=serial_dict["num_samples"]
            )

        # Model object creation
        name = serial_dict.pop("name", "model")
        model = cls(name)
        for slot, value in serial_dict.items():
            setattr(model, slot, value)

        return model

    @classmethod
    def from_json(cls, io: TextIO) -> "Model":
        """Creates/Deserializes the Model from a JSON file.

        Under the hood uses the deserialize() method.

        Parameters
        ----------
        io : TextIO
            _description_

        Returns
        -------
        Model
            An initialized Model instance.
        """

        if not os.path.isfile(io):
            raise FileNotFoundError("No such file or directory exists.")

        with open(io, "r", encoding="utf-8") as fp:
            serial_dict = json.load(fp=fp)

        return cls.deserialize(serial_dict)
