import json
import os.path
from copy import deepcopy
from typing import TextIO

import numpy as np

from PetroGeoSim.distributions import Distribution
from PetroGeoSim.equation_parser import evaluate


class Property:
    """Class handles operations on `Model`s inputs and results.

    Acts as a container for values, sampled from distributions,
    distributions themselves, calculated statistics, mathematical operations
    and serialization/deserialization.

    Attributes
    ----------
    name : str
        Name of the Property, also used in hashing (MUST be unique).
    distribution : Distribution | None, optional
        Access to `Distribution` object instance, by default None.
    equation : str | None, optional
        String representation of equation used in Result calculation, by default None.
    values : Generator
        NumPy Array containing sampled (Inputs) or calculated (Results) values.
    stats : dict[str, float]
        Dictionary of specified statistical characteristics:
        Characteristic -> Values.

    Methods
    -------
    calculate_stats()
        Represent the photo in the given colorspace.
    run_calculation(n=1.0)
        Change the photo's gamma exposure.
    to_json(n=1.0)
        Change the photo's gamma exposure.
    from_json(n=1.0)
        Change the photo's gamma exposure.
    """

    __slots__ = ("name", "prop_type", "distribution", "equation", "values", "stats")

    def __init__(
        self,
        name: str,
        distribution: str | None = None,
        equation: str | None = None,
        **kwargs
    ) -> None:
        self.name = name
        self.distribution = None
        self.equation = None
        self.values = 0
        self.stats = {}

        if distribution:
            self.prop_type = "input"
            num_samples = kwargs.pop("num_samples", 10000)
            self.distribution = Distribution(
                distribution, num_samples, **kwargs
            )
        elif equation:
            self.prop_type = "result"
            self.equation = equation
        else:
            raise ValueError("Invalid property type")

    def __str__(self) -> str:
        return (
            f"{self.prop_type.upper()} PROPERTY {self.name}\n"
            f"* Distribution: \n{self.distribution.name}\n"
            f"* Equation: \n{self.equation}\n"
            f"* Stats: {self.stats}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Property) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    # Direct operations on property values
    def __add__(self, other):
        if isinstance(other, Property):
            new = Property(f"({self.name} + {other.name})")
            new.values = self.values + other.values
        else:
            new = Property(f"({self.name} + {other})")
            new.values = self.values + other

        return new

    def __sub__(self, other):
        if isinstance(other, Property):
            new = Property(f"({self.name} - {other.name})")
            new.values = self.values - other.values
        else:
            new = Property(f"({self.name} - {other})")
            new.values = self.values - other

        return new

    def __mul__(self, other):
        if isinstance(other, Property):
            new = Property(f"({self.name} * {other.name})")
            new.values = self.values * other.values
        else:
            new = Property(f"({self.name} * {other})")
            new.values = self.values * other

        return new

    def __truediv__(self, other):
        if isinstance(other, Property):
            new = Property(f"({self.name} / {other.name})")
            new.values = self.values / other.values
        else:
            new = Property(f"({self.name} /{other})")
            new.values = self.values / other

        return new

    # Inverse operations on property values
    def __radd__(self, other):
        if isinstance(other, Property):
            new = Property(f"({other.name} + {self.name})")
            new.values = other.values + self.values
        else:
            new = Property(f"({other} + {self.name})")
            new.values = other + self.values

        return new

    def __rsub__(self, other):
        if isinstance(other, Property):
            new = Property(f"({other.name} - {self.name})")
            new.values = other.values - self.values
        else:
            new = Property(f"({other} - {self.name})")
            new.values = other - self.values

        return new

    def __rmul__(self, other):
        if isinstance(other, Property):
            new = Property(f"({other.name} * {self.name})")
            new.values = other.values * self.values
        else:
            new = Property(f"({other} * {self.name})")
            new.values = other * self.values

        return new

    def __rtruediv__(self, other):
        if isinstance(other, Property):
            new = Property(f"({other.name} / {self.name})")
            new.values = other.values / self.values
        else:
            new = Property(f"({other} / {self.name})")
            new.values = other / self.values

        return new

    def __neg__(self):
        new = Property(f"(-{self.name})")
        new.values = -self.values

        return new

    def _evaluate_equation(self, **kwargs) -> None:
        return evaluate(self.equation, kwargs)

    def calculate_stats(self) -> None:
        """
        Calculates values of specified statistical characteristics.
        """

        self.stats["P90"] = np.percentile(self.values, 10)
        self.stats["P50"] = np.percentile(self.values, 50)
        self.stats["P10"] = np.percentile(self.values, 90)
        self.stats["Mean"] = np.mean(self.values)
        self.stats["Std"] = np.std(self.values)

    def run_calculation(self, **kwargs) -> dict[str, float]:
        if self.prop_type == "input":
            self.values = self.distribution(**kwargs)
        if self.prop_type == "result":
            self.values = self._evaluate_equation(**kwargs)

        self.calculate_stats()

        return self.stats

    def to_json(
        self, to_str: bool = True, exclude: tuple = ("name", "prop_type", "values", "stats")
    ) -> str | None:
        # slots = []
        # for cls in reversed(type(self).__mro__):
        #     cls_slots = getattr(cls, "__slots__", None)
        #     if isinstance(cls_slots, str):
        #         slots.append(cls_slots)
        #     if isinstance(cls_slots, tuple):
        #         slots.extend(cls_slots)

        json_dict = {
            slot: deepcopy(getattr(self, slot)) for slot in self.__slots__ if slot not in exclude
        }

        # Dictionary clean up
        if self.distribution and "distribution" not in exclude:
            json_dict["distribution"] = self.distribution.to_json()
            del json_dict["equation"]
        if self.equation and "equation" not in exclude:
            del json_dict["distribution"]
        if "values" not in exclude:
            json_dict["values"] = json_dict["values"].tolist()

        if to_str:
            return json_dict

        with open(f"Random Property {self.name}.json", "w", encoding="utf-8") as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO):
        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        json_dict["distribution"] = Distribution.from_json(json_dict["distribution"])
        if json_dict.get("values", None):
            json_dict["values"] = np.array(json_dict["values"])

        name = json_dict.pop("name", "property")
        distr = json_dict.pop("distribution", None)
        eq = json_dict.pop("equation", None)
        prop = cls(name, distribution=distr.name, equation=eq)
        for slot, value in json_dict.items():
            setattr(prop, slot, value)

        # prop.run_calculation()  # Don't know how to do it properly yet

        return prop


# class RandomProperty:

#     __slots__ = ("name", "distribution", "values", "stats")

#     def __init__(
#         self,
#         name: str,
#         distribution: str,
#         **kwargs,
#     ) -> None:
#         self.name = name
#         self.distribution = None
#         self.values = 0
#         self.stats = {}

#         num_samples = kwargs.pop("num_samples", 10000)
#         self.distribution = Distribution(
#             distribution, num_samples, **kwargs
#         )

#     def __str__(self) -> str:
#         return (
#             f"RANDOM PROPERTY {self.name}\n"
#             f"* Distribution: \n{self.distribution}\n"
#             f"* Stats: {self.stats}"
#         )

#     def calculate_stats(self) -> None:
#         """
#         Calculates values of specified statistical characteristics.
#         """

#         self.stats["P90"] = np.percentile(self.values, 10)
#         self.stats["P50"] = np.percentile(self.values, 50)
#         self.stats["P10"] = np.percentile(self.values, 90)
#         self.stats["Mean"] = np.mean(self.values)
#         self.stats["Std"] = np.std(self.values)

#     def run_calculation(self, **kwargs) -> dict[str, float]:

#         self.values = self.distribution(**kwargs)  # self._generate_values()
#         self.calculate_stats()

#         return self.stats

#     def to_json(
#         self, to_str: bool = True, exclude: tuple = ("name", "values", "stats")
#     ) -> str | None:
#         # slots = []
#         # for cls in reversed(type(self).__mro__):
#         #     cls_slots = getattr(cls, "__slots__", None)
#         #     if isinstance(cls_slots, str):
#         #         slots.append(cls_slots)
#         #     if isinstance(cls_slots, tuple):
#         #         slots.extend(cls_slots)

#         json_dict = {
#             slot: deepcopy(getattr(self, slot)) for slot in self.__slots__ if slot not in exclude
#         }

#         # Dictionary clean up
#         if self.distribution and "distribution" not in exclude:
#             json_dict["distribution"] = self.distribution.to_json()
#         if "values" not in exclude:
#             json_dict["values"] = json_dict["values"].tolist()

#         if to_str:
#             return json_dict

#         with open(f"Random Property {self.name}.json", "w", encoding="utf-8") as fp:
#             json.dump(json_dict, fp=fp, indent=4)

#     @classmethod
#     def from_json(cls, io: TextIO) -> "RandomProperty":
#         if isinstance(io, dict):
#             json_dict = io
#         else:
#             if os.path.isfile(io):
#                 with open(io, "r", encoding="utf-8") as fp:
#                     json_dict = json.load(fp=fp)

#         json_dict["distribution"] = Distribution.from_json(json_dict["distribution"])
#         if json_dict.get("values", None):
#             json_dict["values"] = np.array(json_dict["values"])

#         name = json_dict.pop("name", "property")
#         rand_prop = cls(name, json_dict["distribution"].name)
#         for slot, value in json_dict.items():
#             setattr(rand_prop, slot, value)

#         # rand_prop.run_calculation()  # Don't know how to do it properly yet

#         return rand_prop


# class ResultProperty:

#     __slots__ = ("name", "equation", "values", "stats")

#     def __init__(self, name: str, equation: str) -> None:
#         self.name = name
#         self.equation = None
#         self.values = 0
#         self.stats = {}

#     def _calc(self) -> Literal[0]:
#         return 0

#     def _generate_values(self, **kwargs) -> None:
#         self.values = evaluate(self.equation, kwargs)

#     def calculate_stats(self) -> None:
#         self.stats["P90"] = np.percentile(self.values, 10)
#         self.stats["P50"] = np.percentile(self.values, 50)
#         self.stats["P10"] = np.percentile(self.values, 90)
#         self.stats["Mean"] = np.mean(self.values)

#     def run_calculation(self, **kwargs) -> dict[str, float]:
#         self._generate_values()
#         self.calculate_stats()
#         return self.stats

#     def to_json(
#         self, to_str: bool = True, exclude: tuple = ("name", "values", "info", "stats")
#     ) -> str | None:
#         slots = []
#         for cls in reversed(type(self).__mro__):
#             cls_slots = getattr(cls, "__slots__", None)
#             if isinstance(cls_slots, str):
#                 slots.append(cls_slots)
#             if isinstance(cls_slots, tuple):
#                 slots.extend(cls_slots)

#         json_dict = {
#             slot: deepcopy(getattr(self, slot)) for slot in slots if slot not in exclude
#         }

#         # Dictionary clean up
#         if "values" not in exclude:
#             json_dict["values"] = json_dict["values"].tolist()
#         # del json_dict["info"]
#         # json_dict["info"] = {name: arr.tolist() for name, arr in json_dict["info"].items()}

#         if to_str:
#             return json_dict

#         with open(f"Result Property {self.name}.json", "w", encoding="utf-8") as fp:
#             json.dump(json_dict, fp=fp, indent=4)

#     @classmethod
#     def from_json(cls, io: TextIO):
#         if isinstance(io, dict):
#             json_dict = io
#         else:
#             if os.path.isfile(io):
#                 with open(io, "r", encoding="utf-8") as fp:
#                     json_dict = json.load(fp=fp)

#         # json_dict["values"] = np.array(json_dict["values"])
#         # json_dict["info"] = {
#         #     name: np.array(arr) for name, arr in json_dict["info"]
#         # }

#         name = json_dict.pop("name", "property")
#         info_dict = json_dict.pop("info", {})
#         res_prop = cls(name, info_dict)
#         for slot, value in json_dict.items():
#             setattr(res_prop, slot, value)

#         # res_prop.run_calculation()  # Don't know how to do it properly yet

#         return res_prop
