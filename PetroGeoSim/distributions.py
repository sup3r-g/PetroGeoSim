from ast import literal_eval
from copy import deepcopy
import json
import os
import re
from typing import Any, TextIO
from scipy.stats import (
    beta,
    lognorm,
    norm,
    triang,
    truncnorm,
    uniform,
)
from numpy.random import SeedSequence, default_rng
from numpy import exp

DISTRIBUTIONS_KWARGS = {
    "uniform": {"min", "max"},
    "normal": {"mean", "std"},
    "beta": {"a", "b", "min", "max"},
    "lognormal": {"std", "shift", "mean"},
    "triangular": {"mode", "min", "max"},
    "truncated normal": {"min", "max", "mean", "std"},
}


class Distribution:
    """Encapsulates the distribution choice logic, replaces
    init parameters for SciPy functions.

    _extended_summary_

    Attributes
    ----------
    name : str
        Name of the function and a lookup key in `SCIPY_NAMES`.
    num_samples : int, optional
        Number of samples to draw from the distribution, by default 10000.
    seed : SeedSequence
        Exposure in seconds.
    rng : Generator
        Exposure in seconds.
    function : rv_continuous
        Exposure in seconds.

    Methods
    -------
    update(seed, num_samples)
        Represent the photo in the given colorspace.
    gamma(n=1.0)
        Change the photo's gamma exposure.
    gamma(n=1.0)
        Change the photo's gamma exposure.
    gamma(n=1.0)
        Change the photo's gamma exposure.
    """

    __slots__ = ("name", "num_samples", "seed", "rng", "function", "params")

    SCIPY_NAMES = {
        "uniform": uniform,
        "normal": norm,
        "beta": beta,
        "lognormal": lognorm,
        "triangular": triang,
        "truncated normal": truncnorm,
    }

    def __init__(self, name: str, num_samples: int = 10000, **kwargs) -> None:
        self.name = name.lower()
        self.num_samples = num_samples
        self.seed = SeedSequence()
        self.rng = default_rng(self.seed)
        self.function = self._init_func()
        self.params = kwargs

    def __str__(self) -> str:
        return (
            f"* Name: {self.name}\n"
            f"* Seed: {self.seed}\n"
            f"* Number of samples: {self.num_samples}\n"
        )

    def __call__(self, **kwargs: Any) -> Any:
        if kwargs:
            self.params = kwargs
        scipy_params = self._intersept_kwargs(**self.params)
        values = self.function.rvs(
            size=self.num_samples,
            random_state=self.rng,
            **scipy_params
        )

        return values

    def _init_func(self):
        """Initializes the function from the `self.name`.

        Uses the `SCIPY_NAMES` dictionary to look up supported functions,
        else raises a KeyError.

        Returns
        -------
        rv_continuous
            SciPy function to be used in sampling.

        Raises
        ------
        KeyError
            The supplied function name didn't match anything,
            hence it is not supported yet.
        """

        function = self.SCIPY_NAMES.get(self.name, None)
        if function is not None:
            return function

        raise KeyError("Function with a corresponding name not supported yet")

    def _intersept_kwargs(self, **kwargs) -> dict[str, Any]:
        """Intersepts keyword arguments and converts them to SciPy arguments.

        The functions allows to get and convert a more user-friendly version
        of arguments, specified in `DISTRIBUTIONS_KWARGS` to those
        understood by SciPy functions.

        Returns
        -------
        dict[str, Any]
            Keyword arguments to be supplied to a SciPy function.

        Raises
        ------
        NotImplementedError
            The supplied function name didn't match anything,
            hence it is not supported yet.
        """

        left, right = kwargs.get("min"), kwargs.get("max")
        mean, std = kwargs.get("mean"), kwargs.get("std")
        a, b = kwargs.get("a"), kwargs.get("b")
        shift = kwargs.get("shift")
        mode = kwargs.get("mode")

        match self.name:
            case "uniform":  # loc = left, scale = right-left
                return {"loc": left, "scale": right - left}
            case "normal":  # loc = Mean (mu), scale = Standard Deviation (sigma)
                return {"loc": mean, "scale": std}
            case "beta":  # mode = (a - 1) / (a + b - 2) ; b = (a - 1 - (a - 2)*mode) / mode --->> a = shift+1, b = (a - 1 - (a - 2)*mode) / mode
                return {"a": a, "b": b, "loc": left, "scale": right}
            case "lognormal":  # s = sigma, scale = exp(mu), loc = shift (left boundary position)
                return {"s": std, "loc": shift, "scale": exp(mean)}
            case "triangular":  # c = (mode - left) / (right - left), loc = left, scale = right - left, c=[0, 1]
                return {
                    "c": (mode - left) / (right - left),
                    "loc": left,
                    "scale": right - left,
                }
            case "truncated normal":  # a, b = (left - loc) / scale, (right - loc) / scale
                return {
                    "a": (left - mean) / std,
                    "b": (right - mean) / std,
                    "loc": mean,
                    "scale": std,
                }
            case _:
                raise NotImplementedError("Function not supported yet")

    def update(self, seed: SeedSequence, num_samples: int) -> None:
        """Updates attributes to match the supplied ones.

        Parameters
        ----------
        seed : SeedSequence
            _description_
        num_samples : int
            Number of samples to draw from the distribution.
        """

        self.num_samples = num_samples
        self.seed = seed.spawn(1)[0]
        self.rng = default_rng(self.seed)

    def to_json(
        self,
        to_str: bool = True,
        exclude: tuple | list = (
            "rng",
            "function",
            "num_samples",
            "seed"
        )
    ) -> str | None:
        """Serializes the `Distribution` into a JSON file or a dictionary.

        The generated file has a name `{Distribution.name}.json`.

        Parameters
        ----------
        to_str : bool, optional
            Controls the output destination (string or file), by default True.
        exclude : tuple | list, optional
            Attributes to not use during serialization, by default ( "rng", "function", "num_samples", "seed" ).

        Returns
        -------
        str | None
            A serialized dictionary or None (writes to file).
        """

        json_dict = {
            slot: deepcopy(getattr(self, slot))
            for slot in self.__slots__
            if slot not in exclude
        }

        # SeedSequence parser using RegEx
        if "seed" not in exclude:
            seed_pat = re.compile(r"\(?,?\s+\)?")
            res = re.split(seed_pat, repr(json_dict["seed"]))
            seed_kw = {}
            for part in res[1:-1]:
                k, v = part.split("=")
                seed_kw[k] = literal_eval(v)

            # Dictionary clean up
            json_dict["seed"] = json_dict["seed"].entropy  # seed_kw

        if to_str:
            return json_dict

        with open(
            f"Distribution {self.name}.json",
            "w", encoding="utf-8"
        ) as fp:
            json.dump(json_dict, fp=fp, indent=4)

    @classmethod
    def from_json(cls, io: TextIO, **kwargs) -> "Distribution":
        """Creates/Deserializes the `Distribution` from a JSON file.

        _extended_summary_

        Parameters
        ----------
        io : TextIO
            A dictionary or a file path with the necessary data.

        Returns
        -------
        Distribution
            An initialized `Distribution` instance.
        """

        if isinstance(io, dict):
            json_dict = io
        else:
            if os.path.isfile(io):
                with open(io, "r", encoding="utf-8") as fp:
                    json_dict = json.load(fp=fp)

        json_dict["seed"] = SeedSequence(**json_dict["seed"])
        json_dict["rng"] = default_rng(json_dict["seed"])

        name = json_dict.pop("name", "normal")
        distrib = cls(name)
        for slot, value in json_dict.items():
            setattr(distrib, slot, value)

        return distrib
