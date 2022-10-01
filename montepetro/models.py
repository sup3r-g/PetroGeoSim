import json
import os.path
from copy import deepcopy
from typing import Any
from typing_extensions import Self

from numpy.random import SeedSequence

from montepetro.properties import Property
from montepetro.regions import Region


class Model:
    def __init__(self, name: str, seed: int | None = None) -> None:
        self.name = name
        self.seed_sequence = SeedSequence(seed)
        # self.properties = {}
        self.regions = {}

    def __str__(self) -> str:
        return (
            f"MODEL {self.name}\n"
            f"* Seed: {self.seed_sequence.entropy}\n"
            f"* Regions: {', '.join(self.regions.keys())}\n"
            f"* Properties: {', '.join(self.get_all_properties().keys())}"
        )

    def add_region(self, region: Region) -> None:
        if region.name in self.regions:
            raise KeyError(
                f'Encountered duplicate Region "{region.name}"'
                f'in Model "{self.name}"'
            )
        for prop in region.properties.values():
            prop.update_seed(self.seed_sequence)
            prop.values = None
        self.regions[region.name] = region

    def add_regions(self, regions: list[Region] | tuple[Region]) -> None:
        for reg in regions:
            self.add_region(reg)

    def add_property(
        self,
        prop: Property,
        add_to: str | list[str] | tuple[str] = "all"
    ) -> None:
        if isinstance(add_to, str):
            if add_to == "all":
                for region in self.regions.values():
                    prop.update_seed(self.seed_sequence)
                    region.add_property(deepcopy(prop))
            elif add_to in self.regions:
                prop.update_seed(self.seed_sequence)
                self.regions[add_to].add_property(prop)
            else:
                raise KeyError(
                    f'No such Region "{add_to}" found in Model "{self.name}"'
                )
        elif isinstance(add_to, (list, tuple)):
            reg_list = set(add_to).intersection(self.regions.keys())
            if not reg_list:
                raise KeyError(
                    'No Regions with corresponding names found'
                    f'in Model "{self.name}"'
                )

            for reg in reg_list:
                prop.update_seed(self.seed_sequence)
                self.regions[reg].add_property(deepcopy(prop))
        else:
            raise TypeError('Invalid `add_to` type, see documenation')

    def add_properties(
        self, props: dict[Property, str] | list[Property] | tuple[Property]
    ) -> None:
        if isinstance(props, dict):
            for prop, region in props.items():
                self.add_property(prop, region)
        elif isinstance(props, (list, tuple)):
            for prop in props:
                self.add_property(prop, "all")
        else:
            raise TypeError('Invalid `props` type, see documenation')

    def add_regional_property(self, prop_name: str, prop: Property) -> None:
        if not isinstance(prop_name, str):
            raise TypeError('`prop_name` must be a string')

        for region in self.regions.values():
            # self.add_property(prop(name=prop_name), "all")
            region.properties[prop_name] = prop(name=prop_name, region=region)
            region.properties[prop_name].generate_values()

    def get_all_properties(self):
        properties = {}
        for region_name, region in self.regions.items():
            for prop_name, prop in region.properties.items():
                properties.setdefault(prop_name, {})[region_name] = prop.values
        return properties

    def run(self, config: dict[str, Any]) -> None:
        # check config validity!!!
        for region_name, region in self.regions.items():
            for property_name, prop in region.properties.items():
                regional_property_config = config[region_name][property_name]
                prop.generate_values(**regional_property_config)
                
    def to_json(self, to_str: bool = True) -> str | None:
        string = vars(self).copy()
        
        for name, region in self.regions.items():
            string['regions'][name] = region.to_json()
        
        if to_str:
            return json.dumps(string, indent=4)
        
        with open(f"Region {self.name}.json", "w") as fp:
            json.dump(string, fp=fp, indent=4)
            
    @classmethod
    def from_json(cls, io: str) -> Self@Model:
        if os.path.isfile(io):
            with open(io, "r") as fp:
                json.load(fp=fp)
        else:
            json.loads(s=io)
        
        model = cls()
        return model
