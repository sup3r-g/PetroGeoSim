import json
import os.path
import re
from ast import literal_eval
from collections import defaultdict
from copy import deepcopy
from typing import Any, Literal, TextIO

from numpy.random import SeedSequence

from PetroGeoSim.config_maker import config_maker
from PetroGeoSim.properties import Property
from PetroGeoSim.regions import Region


class Model:

    __slots__ = ("name", "seed_sequence", "desc", "regions")  # "access"

    def __init__(
        self, name: str, seed: int | None = None, desc: str | None = None
    ) -> None:
        self.name = name
        self.seed_sequence = SeedSequence(seed)
        self.desc = desc
        self.regions = {}
        # self.access = [
        #     (reg_name, prop_name)
        #     for reg_name, reg in self.regions.items()
        #     for prop_name in reg.properties
        #   ]

    def __str__(self) -> str:
        return (
            f'MODEL "{self.name}"\n'
            f"* Seed: {self.seed_sequence.entropy}\n"
            f"* Regions: {', '.join(self.regions.keys())}\n"
            f"* Properties: {', '.join(self.get_all_properties('name'))}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Model) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __contains__(self, other) -> bool:
        return other.name in self.regions

    def _add_resolver(self, add_to) -> tuple | str | list:
        if isinstance(add_to, str):
            if add_to == "all":
                return tuple(self.regions.keys())
            if add_to in self.regions:
                return add_to
            raise KeyError(
                f'Region "{add_to}" not found in Model "{self.name}"'
            )
        if isinstance(add_to, (list, tuple)):
            error_extra = set(add_to).issubset(self.regions.keys())
            if not error_extra:
                not_found = '", "'.join(
                    set(add_to).difference(self.regions.keys())
                )
                raise KeyError(
                    f'Region(s) "{not_found}" not found in Model "{self.name}"'
                )
            return add_to
        raise TypeError("Invalid `add_to` type, see documentation")

    def add_region(self, region: Region) -> None:
        if region in self:
            raise KeyError(
                f'Encountered duplicate Region "{region.name}" '
                f'in Model "{self.name}"'
            )

        for prop in region.properties.values():  # reset_region() ???
            prop.update_seed(self.seed_sequence)
            prop.values = None
        self.regions[region.name] = region

    def add_regions(self, *args) -> None:  # regions: list[Region] | tuple[Region]
        for reg in args:  # regions
            self.add_region(reg)

    def add_property(
        self,
        prop: Property,
        add_to: Literal["all"] | str | list[str] | tuple[str] = "all",
    ) -> None:
        for reg in self._add_resolver(add_to):
            prop.update_seed(self.seed_sequence)
            self.regions[reg].add_property(deepcopy(prop))

    def add_properties(
        self,
        props: dict[Property, str | list[Property] | tuple[Property]]
        | list[Property]
        | tuple[Property],
    ) -> None:
        if isinstance(props, dict):
            for prop, add_to in props.items():
                self.add_property(prop, add_to)
        elif isinstance(props, (list, tuple)):
            for prop in props:
                self.add_property(prop, "all")
        else:
            raise TypeError("Invalid `props` type, see documentation")

    def add_result_property(self, prop_name: str, prop: Property) -> None:
        if not isinstance(prop_name, str):
            raise TypeError("`prop_name` must be a string")

        for reg in self.regions.values():
            res_prop = prop(name=prop_name, info=reg.get_properties("values"))
            res_prop.run_calculation()
            reg.add_property(res_prop)

    def get_all_properties(self, attribute: str) -> dict[str, dict]:
        attributes = defaultdict(dict)

        for reg_name, reg in self.regions.items():
            for prop_name, prop in reg.properties.items():
                if hasattr(prop, attribute):
                    attributes[prop_name][reg_name] = getattr(prop, attribute)
        return dict(attributes)

    def check_config(self, config):
        config_test = deepcopy(config)

        for reg_name, reg in config_test.items():
            for prop_name, prop in reg.items():
                config_test[reg_name][prop_name] = set(prop.keys())

        return config_test == config_maker(self, user_input=False)

    def run(self, config: dict[str, Any]) -> None:
        if not self.check_config(config):
            raise KeyError(
                "Invalid key is present or a key is missing in the config"
            )

        for reg_name, reg in self.regions.items():
            for prop_name, prop in reg.properties.items():
                result_property_config = config[reg_name][prop_name]
                prop.run_calculation(**result_property_config)

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

        # SeedSequence parser using RegEx
        seed_pat = re.compile(r"\(?,?\s+\)?")
        res = re.split(seed_pat, repr(json_dict["seed_sequence"]))
        seed_kw = {}
        for part in res[1:-1]:
            k, v = part.split("=")
            seed_kw[k] = literal_eval(v)

        # Dictionary clean up
        json_dict["seed_sequence"] = seed_kw
        for reg_name, reg in self.regions.items():
            json_dict["regions"][reg_name] = reg.to_json()

        if to_str:
            return json_dict

        with open(f"Model {self.name}.json", "w", encoding="utf-8") as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO):
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        for reg_name, reg in json_dict["regions"].items():
            json_dict["regions"][reg_name] = Region.from_json(reg)

        json_dict["seed_sequence"] = SeedSequence(**json_dict["seed_sequence"])

        name = json_dict.pop("name", "model")
        model = cls(name)
        for slot, value in json_dict.items():  # model.__dict__ = json_dict.copy()
            setattr(model, slot, value)

        return model
