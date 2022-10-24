import json
import os.path

# import re
# from ast import literal_eval
from collections import defaultdict
from copy import deepcopy
from typing import Any, Literal, TextIO

from numpy.random import SeedSequence

from PetroGeoSim.config_maker import config_maker
from PetroGeoSim.properties import Property
from PetroGeoSim.regions import Region


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

    __slots__ = ("name", "seed", "num_samples", "regions")  # "access"

    def __init__(
        self, name: str, seed: int | None = None, num_samples: int = 10000
    ) -> None:
        self.name = name
        self.seed = SeedSequence(seed)
        self.num_samples = num_samples
        self.regions = {}
        # self.access = [
        #     (reg_name, prop_name)
        #     for reg_name, reg in self.regions.items()
        #     for prop_name in reg.properties
        #   ]

    def __str__(self) -> str:
        return (
            f'MODEL "{self.name}"\n'
            f"* Seed: {self.seed.entropy}\n"
            f"* Number of samples: {self.num_samples}\n"
            f"* Regions: {', '.join(self.regions.keys())}\n"
            f"* Properties: {', '.join(self.get_all_properties('name', invert_dict=True))}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Model) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return other.name in self.regions

    def _add_resolver(self, add_to: str | list | tuple) -> tuple | str | list:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        add_to : str | list | tuple
            _description_

        Returns
        -------
        tuple | str | list
            _description_

        Raises
        ------
        KeyError
            _description_
        KeyError
            _description_
        TypeError
            _description_
        """

        if isinstance(add_to, str):
            if add_to == "all":
                return tuple(self.regions.keys())
            if add_to in self.regions:
                return (add_to, )
            raise KeyError(f'Region "{add_to}" not found in Model "{self.name}"')
        if isinstance(add_to, (list, tuple)):
            error_extra = set(add_to).issubset(self.regions.keys())
            if not error_extra:
                not_found = '", "'.join(set(add_to).difference(self.regions.keys()))
                raise KeyError(
                    f'Region(s) "{not_found}" not found in Model "{self.name}"'
                )
            return add_to
        raise TypeError("Invalid `add_to` type, see documentation")

    def add_region(self, region: Region) -> None:
        """Add a single Region to the Model.

        _extended_summary_

        Parameters
        ----------
        region : Region
            A defined `Region` object to be added

        Raises
        ------
        KeyError
            Can't add a `Region` with the same name.
        """

        if region in self:
            raise KeyError(
                f'Encountered duplicate Region "{region.name}" '
                f'in Model "{self.name}"'
            )

        for prop in region.inputs.values():  # reset_region() ???
            if prop.prop_type == "input":
                prop.distribution.update(self.seed, self.num_samples)
            prop.values = None
        self.regions[region.name] = region

    def add_regions(self, *regions: tuple[Region]) -> None:
        """Add multiple Regions to the Model.

        This method calls add_region() in a loop.

        Parameters
        ----------
        *regions : tuple[Region]
            Positional arguments of type `Region`
        """

        for reg in regions:
            self.add_region(reg)

    def add_property(
        self,
        prop: Property,
        add_to: Literal["all"] | str | list[str] | tuple[str] = "all",
    ) -> None:
        """Add a single Property to the Model.

        Calls private method `_add_resolver()` that handles various input types.

        Parameters
        ----------
        prop : Property
            _description_
        add_to : Literal[&quot;all&quot;] | str | list[str] | tuple[str], optional
            _description_, by default "all"
        """

        for reg in self._add_resolver(add_to):
            if prop.prop_type == "input":
                prop.distribution.update(self.seed, self.num_samples)
            self.regions[reg].add_property(deepcopy(prop))

    def add_properties(
        self,
        props: dict[Property, str | list[Property] | tuple[Property]]
        | list[Property]
        | tuple[Property],
    ) -> None:
        """Add multiple Properties to the Model.

        Properties are passed as a dictionary.
        Calls add_property() method in a loop.

        Parameters
        ----------
        props : dict[Property, str | list[Property] | tuple[Property]] 
                | list[Property] | tuple[Property]
            A dictionary with Properties as keys and string, list or tuple of Regions names.

        Raises
        ------
        TypeError
            _description_
        """

        if isinstance(props, dict):
            for prop, add_to in props.items():
                self.add_property(prop, add_to)
        elif isinstance(props, (list, tuple)):
            for prop in props:
                self.add_property(prop, "all")
        else:
            raise TypeError("Invalid `props` type, see documentation")

    # def add_result_property(self, prop_name: str, prop: Property) -> None:
    #     """_summary_

    #     _extended_summary_

    #     Parameters
    #     ----------
    #     prop_name : str
    #         _description_
    #     prop : Property
    #         _description_

    #     Raises
    #     ------
    #     TypeError
    #         _description_
    #     """

    #     if not isinstance(prop_name, str):
    #         raise TypeError("`prop_name` must be a string")

    #     for reg in self.regions.values():
    #         res_prop = prop(name=prop_name, info=reg.get_properties("values"))
    #         res_prop.run_calculation()
    #         reg.add_property(res_prop)

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
            What Properties in the dictionary:
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
                for prop_name, attr in all_properties[reg_name].items():
                    attributes[prop_name][reg_name] = attr

        if invert_dict:
            return dict(attributes)

        return all_properties

    def result(self, how: str = "sum"):
        model_results = {}
        for reg in self.regions.values():
            for res_name, res in reg.get_properties("values", "results").items():
                model_results[res_name] = model_results.get(res_name, res) + res

        return model_results

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

        return config_test == config_maker(self, user_input=False)

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
            raise KeyError("Invalid key is present or a key is missing in the config")

        for reg_name, reg in self.regions.items():
            for prop_name, prop in reg.inputs.items():
                result_property_config = config[reg_name][prop_name]
                prop.run_calculation(**result_property_config)
            for prop_name, prop in reg.results.items():
                prop.run_calculation(
                    **reg.get_properties("values", include="inputs")
                )

    def to_json(self, to_str: bool = True, exclude: tuple | list = ()) -> dict | None:
        """Serializes the `Model` into a JSON file or a dictionary.

        The generated file has a name `{Model.name}.json`.

        Parameters
        ----------
        to_str : bool, optional
            Controls the output destination (string or file), by default True.
        exclude : tuple | list, optional
             Attributes to not use during serialization, by default ().

        Returns
        -------
        dict | None
            A serialized dictionary or None (writes to file).
        """

        json_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in self.__slots__
            if slot not in exclude
        }

        # Dictionary clean up
        json_dict["seed"] = json_dict["seed"].entropy

        for reg_name, reg in self.regions.items():
            json_dict["regions"][reg_name] = reg.to_json()

        if to_str:
            return json_dict

        with open(f"Model {self.name}.json", "w", encoding="utf-8") as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO) -> "Model":
        """Creates/Deserializes the Model from a JSON file.

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            A dictionary or a file path with the necessary data.

        Returns
        -------
        Model
            An initialized Model instance.
        """

        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        for reg_name, reg in json_dict["regions"].items():
            json_dict["regions"][reg_name] = Region.from_json(reg)

        json_dict["seed"] = SeedSequence(**json_dict["seed"])

        name = json_dict.pop("name", "model")
        model = cls(name)
        for slot, value in json_dict.items():
            setattr(model, slot, value)

        return model

    def send_mygeomap(self):
        return self.get_all_properties("values", include="results")

    @classmethod
    def receive_mygeomap(cls, file):
        if os.path.isfile(file):
            with open(file, "r", encoding="utf-8") as fp:
                setup_config = json.load(fp=fp)

        model = cls(
            setup_config["name"],
            setup_config["seed"],
            setup_config["num_samples"]
        )

        run_config = defaultdict(dict)
        for reg_name, reg_setup in setup_config["config"].items():
            region = Region(reg_name, reg_setup["composition"])
            model.add_region(region)
            for prop_name, prop_setup in reg_setup["inputs"].items():
                prop = Property(
                    prop_name,
                    distribution=prop_setup["distribution"]["name"]
                )
                model.add_property(prop, reg_name)
                run_config[reg_name][prop_name] = prop_setup["distribution"]["params"]
            for prop_name, prop_setup in reg_setup["results"].items():
                prop = Property(
                    prop_name,
                    equation=prop_setup["equation"]
                )
            model.add_property(prop, reg_name)

        model.run(run_config)

        return model
