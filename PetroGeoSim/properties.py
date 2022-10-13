import json
import os.path
import re
from ast import literal_eval
from copy import deepcopy
from typing import Literal, TextIO

import numpy as np
from numpy.random import Generator, SeedSequence, default_rng

from PetroGeoSim.distributions import SCIPY_DISTRIBUTIONS


class Property:

    __slots__ = ("name", "desc", "values")

    def __init__(self, name: str, desc: str | None = None) -> None:
        self.name = name
        self.desc = desc
        self.values = None

    def __eq__(self, other) -> bool:
        return isinstance(other, Property) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class RandomProperty(Property):

    __slots__ = ("seed_sequence", "rng", "distribution", "num_samples", "stats")

    def __init__(
        self,
        name: str,
        distribution: str,
        num_samples: int = 10000,
        # bit_generator: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(name, **kwargs)

        self.seed_sequence = SeedSequence()
        self.rng = default_rng(self.seed_sequence)
        # self.bit_generator = BIT_GENERATORS.get(
        #     bit_generator, BIT_GENERATORS["PCG64"]  # type: ignore
        # )
        # self.rng = Generator(self.bit_generator(self.seed_sequence))

        # FOR NUMPY FUNCTIONS
        # if distribution is None:
        #     distribution = "normal"
        # self.distribution = getattr(
        #     self.rng, distribution
        # )

        # FOR SCIPY FUNCTIONS
        self.distribution = SCIPY_DISTRIBUTIONS.get(
            distribution.lower(), SCIPY_DISTRIBUTIONS["normal"]
        )
        # self.distribution = DistributionWrapper(distribution, self.rng)
        self.num_samples = num_samples
        self.stats = {}

    def __str__(self) -> str:
        return (
            f"RANDOM PROPERTY {self.name}\n"
            f"{self.desc}\n\n"
            f"* Seed Sequence: {self.seed_sequence}\n"
            # f"* Bit generator: {self.bit_generator}\n"
            f"* RNG function: {self.distribution}\n"
            f"* Number of values to generate: {self.num_samples}\n"
            f"* Mean: {self.stats}"
        )

    def _generate_values(self, *args, **kwargs) -> None:
        # FOR NUMPY FUNCTIONS
        # self.values = self.distribution(
        #     size=self.num_samples, *args, **kwargs
        # )

        # FOR SCIPY FUNCTIONS
        self.values = self.distribution.rvs(
            size=self.num_samples, random_state=self.rng, *args, **kwargs
        )

    def _calc_stats(self) -> None:
        self.stats["Mean"] = np.mean(self.values)
        self.stats["Std"] = np.std(self.values)

    def update_seed(self, seed_sequence: SeedSequence) -> None:
        self.seed_sequence = seed_sequence.spawn(1)[0]
        self.rng = default_rng(self.seed_sequence)
        # self.rng = Generator(self.bit_generator(self.seed_sequence))

    def run_calculation(self, *args, **kwargs) -> dict[str, float]:
        self._generate_values(*args, **kwargs)
        self._calc_stats()
        return self.stats

    def to_json(
        self,
        to_str: bool = True,
        exclude: tuple = ("values", "stats", "rng")
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
        seed_pat = re.compile(r'\(?,?\s+\)?')
        res = re.split(
            seed_pat,
            repr(json_dict["seed_sequence"])
        )
        seed_kw = {}
        for part in res[1:-1]:
            k, v = part.split('=')
            seed_kw[k] = literal_eval(v)

        # Dictionary clean up
        json_dict["seed_sequence"] = seed_kw
        json_dict["distribution"] = json_dict["distribution"].name
        # del json_dict["values"]
        # json_dict["values"] = json_dict["values"].tolist()
        # del json_dict["stats"]
        # del json_dict["rng"]
        # json_dict["bit_generator"] = json_dict["bit_generator"].__name__

        if to_str:
            return json_dict

        with open(f"Random Property {self.name}.json",
                  "w", encoding="utf-8") as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO):
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        json_dict["seed_sequence"] = SeedSequence(**json_dict["seed_sequence"])
        json_dict["rng"] = default_rng(json_dict["seed_sequence"])
        # json_dict["rng"] = Generator(json_dict["bit_generator"](json_dict["seed_sequence"]))
        json_dict["distribution"] = SCIPY_DISTRIBUTIONS[
            json_dict["distribution"]  # Distribution()
        ]
        # json_dict["values"] = np.array(json_dict["values"])
        # json_dict["bit_generator"] = BIT_GENERATORS[json_dict["bit_generator"]]

        name = json_dict.pop("name", "property")
        distrib = json_dict.pop("distribution", "normal")
        rand_prop = cls(name, distrib)
        for slot, value in json_dict.items():
            setattr(rand_prop, slot, value)

        rand_prop.run_calculation()

        return rand_prop


class ResultProperty(Property):

    __slots__ = ("stats")

    def __init__(
        self,
        name: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(name, *args, **kwargs)
        self.stats = {}

    def _calc(self) -> Literal[0]:
        return 0

    def _calc_stats(self) -> None:
        self.stats["P90"] = np.percentile(self.values, 10)
        self.stats["P50"] = np.percentile(self.values, 50)
        self.stats["P10"] = np.percentile(self.values, 90)
        self.stats["Mean"] = np.mean(self.values)

    def _generate_values(self) -> None:
        self.values = self._calc()

    def run_calculation(self) -> dict[str, float]:
        self._generate_values()
        self._calc_stats()
        return self.stats

    def to_json(
        self,
        to_str: bool = True,
        exclude: tuple = ("values", "info", "stats")
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

        # Dictionary clean up
        # del json_dict["values"]
        # json_dict["values"] = json_dict["values"].tolist()
        # del json_dict["info"]
        # json_dict["info"] = {name: arr.tolist() for name, arr in json_dict["info"].items()}
        # del json_dict["stats"]

        if to_str:
            return json_dict

        with open(f"Result Property {self.name}.json",
                  "w", encoding="utf-8") as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO):
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        # json_dict["values"] = np.array(json_dict["values"])
        # json_dict["info"] = {
        #     name: np.array(arr) for name, arr in json_dict["info"]
        # }

        name = json_dict.pop("name", "property")
        info_dict = json_dict.pop("info", {})
        res_prop = cls(name, info_dict)
        for slot, value in json_dict.items():
            setattr(res_prop, slot, value)

        res_prop.run_calculation()

        return res_prop
