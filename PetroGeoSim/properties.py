import json
import os.path
from typing_extensions import Self

import numpy as np
from numpy.random import Generator

from PetroGeoSim.distributions import BIT_GENERATORS, SCIPY_DISTRIBUTIONS


class Property:
    def __init__(self, name: str | None = None, desc: str | None = None):
        self.name = name
        self.desc = desc
        self.values = None


class RandomProperty(Property):
    def __init__(
        self,
        *args,
        bit_generator: str | None = None,
        random_number_function: str | None = None,
        num_samples: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.seed_sequence = None  # SeedSequence()
        self.bit_generator = BIT_GENERATORS.get(
            bit_generator, BIT_GENERATORS["PCG-64"]  # type: ignore
        )
        self.rng = None  # Generator(self.bit_generator(self.seed_sequence))

        # FOR NUMPY FUNCTIONS
        # if random_number_function is None:
        #     random_number_function = "normal"
        # rnf = random_number_function.lower()
        # self.random_number_function = getattr(self.rng, rnf)

        # FOR SCIPY FUNCTIONS
        self.random_number_function = SCIPY_DISTRIBUTIONS.get(
            random_number_function, SCIPY_DISTRIBUTIONS["normal"]
        )

        self.num_samples = num_samples
        self.mean = None

    def __str__(self) -> str:
        return (
            f"RANDOM PROPERTY {self.name}\n"
            f"{self.desc}\n\n"
            f"* Seed Sequence: {self.seed_sequence}\n"
            f"* Bit generator: {self.bit_generator}\n"
            f"* RNG function: {self.random_number_function}\n"
            f"* Number of values to generate: {self.num_samples}\n"
            f"* Mean: {self.mean}"
        )

    def update_seed(self, seed_sequence) -> None:
        self.seed_sequence = seed_sequence.spawn(1)[0]
        self.rng = Generator(self.bit_generator(self.seed_sequence))

    def generate_values(self, *args, **kwargs) -> None:
        # FOR NUMPY FUNCTIONS
        # self.values = self.random_number_function(
        #     size=self.num_samples, *args, **kwargs
        # )

        # FOR SCIPY FUNCTIONS
        self.values = self.random_number_function.rvs(
            size=self.num_samples, random_state=self.rng, *args, **kwargs
        )

    def calc_stats(self) -> None:
        self.mean = np.mean(self.values)
    
    def to_json(self, to_file: bool = False) -> str | None:
        string = vars(self).copy()
        
        string['values'] = string['values'].to_list()
        string['seed_sequence'] = string['seed_sequence'].to_list()
        string['bit_generator'] = string['bit_generator'].__name__
        string['random_number_function'] = string['random_number_function'].name
        del string['rng']
        
        if to_file:
            with open(f"Random Property {self.name}.json", "w") as fp:
                json.dump(string, fp=fp, indent=4)
        else:
            return json.dumps(string, indent=4)
    
    @classmethod
    def from_json(cls, io: str) -> Self@RandomProperty:
        if os.path.isfile(io):
            with open(io, "r") as fp:
                json.load(fp=fp)
        else:
            json.loads(s=io)
        
        rand_prop = cls()
        return rand_prop  



class RegionalProperty(Property):
    def __init__(self, region, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {}
        self.region = region

    def _calc(self):
        return 0

    def _calc_stats(self) -> None:
        self.stats["P90"] = np.percentile(self.values, 10)
        self.stats["P50"] = np.percentile(self.values, 50)
        self.stats["P10"] = np.percentile(self.values, 90)
        self.stats["Mean"] = np.mean(self.values)

    def generate_values(self) -> None:
        self.values = self._calc()

    def run_calculation(self) -> dict[str, float]:
        self.generate_values()
        self._calc_stats()
        return self.stats
    
    def to_json(self, to_str: bool = True) -> str | None:
        string = vars(self).copy()
        string['values'] = string['values'].to_list()
        
        if to_str:
            return json.dumps(string, indent=4)
        
        with open(f"Regional Property {self.name}.json", "w") as fp:
            json.dump(string, fp=fp, indent=4)
            
    
    @classmethod
    def from_json(cls, io: str) -> Self@RegionalProperty:
        if os.path.isfile(io):
            with open(io, "r") as fp:
                json.load(fp=fp)
        else:
            json.loads(s=io)
        
        reg_prop = cls()
        return reg_prop
