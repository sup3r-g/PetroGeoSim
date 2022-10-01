import json
import os.path
from typing_extensions import Self

from PetroGeoSim.properties import Property


class Region:
    def __init__(self, parent=None, name=None, composition=None):
        self.parent = parent
        self.name = name
        self.composition = composition
        self.properties = {}

    def __str__(self) -> str:
        return (
            f"Region {self.name}\n"
            f"Properties: {', '.join(self.properties.keys())}"
        )

    def add_property(self, prop: Property) -> None:
        if prop.name in self.properties.keys():
            raise KeyError(f"Encountered duplicate Property {prop.name} in Region {self.name}.")
        
        self.properties[prop.name] = prop
    
    def to_json(self, to_str: bool = True) -> str | None:
        string = vars(self).copy()
        
        for name, prop in self.properties.items():
            string['properties'][name] = prop.to_json()
        
        if to_str:
            return json.dumps(string, indent=4)
        
        with open(f"Region {self.name}.json", "w") as fp:
            json.dump(string, fp=fp, indent=4)
            
    
    @classmethod
    def from_json(cls, io: str) -> Self@Region:
        if os.path.isfile(io):
            with open(io, "r") as fp:
                json.load(fp=fp)
        else:
            json.loads(s=io)
        
        reg = cls() 
        return reg
