import json
import os.path
from copy import deepcopy
from typing import TextIO

import numpy as np

from PetroGeoSim.distributions import Distribution
from PetroGeoSim.utils.equation_parser import evaluate


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
        String representation of equation used in Result calculation,
        by default None.
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

    __slots__ = (
        "name",
        "variable",
        "prop_type",
        "distribution",
        "equation",
        "values",
        "stats"
    )

    def __init__(
        self,
        name: str,
        variable: str,
        distribution: str | None = None,
        equation: str | None = None,
        **kwargs
    ) -> None:
        self.name = name
        self.variable = variable
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
        if self.prop_type == "input":
            attr = "Distribution"
            math = self.distribution.name
        if self.prop_type == "result":
            attr = "Equation"
            math = self.equation

        return (
            f"{self.prop_type.upper()} PROPERTY {self.name}\n"
            f"* {attr}: \n{math}\n"
            f"* Stats: {self.stats}"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, Property) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    # Direct operations on property values
    def __add__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({self.name} + {other.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = self.values + other.values
        else:
            new = Property(
                f"({self.name} + {other})",
                f"{self.variable}_{other}"
            )
            new.values = self.values + other

        return new

    def __sub__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({self.name} - {other.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = self.values - other.values
        else:
            new = Property(
                f"({self.name} - {other})",
                f"{self.variable}_{other}"
            )
            new.values = self.values - other

        return new

    def __mul__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({self.name} * {other.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = self.values * other.values
        else:
            new = Property(
                f"({self.name} * {other})",
                f"{self.variable}_{other}"
            )
            new.values = self.values * other

        return new

    def __truediv__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({self.name} / {other.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = self.values / other.values
        else:
            new = Property(
                f"({self.name} /{other})",
                f"{self.variable}_{other}"
            )
            new.values = self.values / other

        return new

    # Inverse operations on property values
    def __radd__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({other.name} + {self.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = other.values + self.values
        else:
            new = Property(
                f"({other} + {self.name})",
                f"{self.variable}_{other}"
            )
            new.values = other + self.values

        return new

    def __rsub__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({other.name} - {self.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = other.values - self.values
        else:
            new = Property(
                f"({other} - {self.name})",
                f"{self.variable}_{other}"
            )
            new.values = other - self.values

        return new

    def __rmul__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({other.name} * {self.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = other.values * self.values
        else:
            new = Property(
                f"({other} * {self.name})",
                f"{self.variable}_{other}"
            )
            new.values = other * self.values

        return new

    def __rtruediv__(self, other):
        if isinstance(other, Property):
            new = Property(
                f"({other.name} / {self.name})",
                f"{self.variable}_{other.variable}"
            )
            new.values = other.values / self.values
        else:
            new = Property(
                f"({other} / {self.name})",
                f"{self.variable}_{other}"
            )
            new.values = other / self.values

        return new

    def __neg__(self):
        new = Property(f"(-{self.name})", self.variable)
        new.values = -self.values

        return new

    def _evaluate_equation(self, **kwargs) -> None:
        return evaluate(self.equation, kwargs)

    def calculate_stats(self) -> None:
        """Calculates values of statistical characteristics.

        Specified statistical characteristics are:
        Mean, Standard deviation, Percentiles, Median, Mode
        and others.
        """

        percents = ((10, 50, 90), ("P10", "P50", "P90"))
        percentiles = np.percentile(
            self.values, percents[0], method="median_unbiased"
        )
        self.stats.update(dict(zip(percents[1], percentiles)))

        self.stats["Mean"] = np.mean(self.values)
        self.stats["Std"] = np.std(self.values)

    def run_calculation(self, **calc_kwargs) -> dict[str, float]:
        """Starts the sampling of distribution or evaluation of string equation.

        * For Properties with defined `distribution` attribute
        samples the distribution with defined parameters.
        * For Properties with defined `equation` attribute
        evaluates the string equation using the `equation_parser` module.

        Returns
        -------
        dict[str, float]
            _description_
        """

        if self.prop_type == "input":
            self.values = self.distribution(**calc_kwargs)
        if self.prop_type == "result":
            self.values = self._evaluate_equation(**calc_kwargs)

        self.calculate_stats()

        return self.stats

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
                raise AttributeError(f'Property has no attribute "{attr}".')

    def serialize(
        self, exclude: tuple | list = ("name", "prop_type", "values", "stats")
    ) -> dict:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        exclude : tuple | list, optional
            _description_, by default ("name", "prop_type", "values", "stats")

        Returns
        -------
        dict
            _description_
        """

        serial_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in self.__slots__
            if slot not in exclude
        }

        # Handle special serialization cases
        if self.distribution and "distribution" not in exclude:
            # Continue the serialization down the hierarchy
            serial_dict["distribution"] = self.distribution.serialize()
            del serial_dict["equation"]
        if self.equation and "equation" not in exclude:
            del serial_dict["distribution"]
        if "values" not in exclude:
            serial_dict["values"] = serial_dict["values"].tolist()

        return serial_dict

    def to_json(self, **serialize_kwargs) -> None:
        """_summary_

        _extended_summary_
        """

        with open(
            f"Random Property {self.name}.json", "w", encoding="utf-8"
        ) as fp:
            json.dump(self.serialize(**serialize_kwargs), fp=fp, indent=4)

    @classmethod
    def deserialize(cls, serial_dict: TextIO, **kwargs) -> "Property":
        """_summary_

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            _description_

        Returns
        -------
        Property
            _description_

        Raises
        ------
        TypeError
            _description_
        """

        if not isinstance(serial_dict, dict):
            raise TypeError(
                "Can't perform deserialization from a non dictionary type."
            )

        # Handle special deserialization cases
        distr = serial_dict.get("distribution", {}).get("name", None)
        if distr:
            # Continue the deserialization down the hierarchy
            serial_dict["distribution"] = Distribution.deserialize(
                serial_dict["distribution"], **kwargs
            )
        if serial_dict.get("values", None):
            serial_dict["values"] = np.array(serial_dict["values"])

        # Property object creation
        name = serial_dict.pop("name", "property")
        var = serial_dict.pop("variable", name.lower())
        eq = serial_dict.pop("equation", None)
        prop = cls(name, var, distribution=distr, equation=eq)
        for slot, value in serial_dict.items():
            setattr(prop, slot, value)

        return prop

    @classmethod
    def from_json(cls, io: TextIO) -> "Property":
        """_summary_

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            _description_

        Returns
        -------
        Property
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
