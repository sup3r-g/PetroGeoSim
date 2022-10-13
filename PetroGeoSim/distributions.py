from typing import Any
from scipy.stats import (
    beta,
    lognorm,
    norm,
    rv_continuous,
    rv_discrete,
    triang,
    truncnorm,
    uniform,
)
from numpy.random import Generator

# SCIPY_DISTRIBUTIONS_MAPPINGS = {
#     "uniform": "uniform",
#     "normal": "norm",
#     "beta": "beta",
#     "lognormal": "lognorm",
#     "triangular": "triang",
#     "truncated normal": "truncnorm",
# }

# SCIPY_DISTRIBUTIONS_MAPPINGS.update(
#     dict(reversed(item) for item in SCIPY_DISTRIBUTIONS_MAPPINGS.items())
# )


SCIPY_DISTRIBUTION_KWARGS = {
    "uniform": {"loc", "scale"},
    "norm": {"loc", "scale"},
    "beta": {"a", "b", "loc", "scale"},
    "lognorm": {"s", "loc", "scale"},
    "triang": {"c", "loc", "scale"},
    "truncnorm": {"a", "b", "loc", "scale"},
}

SCIPY_DISTRIBUTION_CONV = {
    "uniform": lambda left, right: (
        left,
        right - left,
    ),  # Uniform: loc = left, scale = right-left
    "norm": lambda loc, scale: (
        loc,
        scale,
    ),  # loc = Mean (mu), scale = Standard Deviation (sigma)
    "beta": lambda a, b, loc, scale: (
        a, b, 
        loc, scale
    ),
    "lognorm": (
        "s",
        lambda loc: loc,
        lambda scale: scale,
    ),  # Lognormal: Suppose a normally distributed random variable X has mean mu and standard deviation sigma. Then Y = exp(X) is lognormally distributed with s = sigma and scale = exp(mu).
    "triang": lambda left, right, mode: (
        (mode - left) / (right - left),
        left,
        right - left,
    ),  # Triangular: c = (mode - left) / (right - left), loc = left, scale = right - left c=[0, 1]
    "truncnorm": lambda left, right, loc, scale: (
        (left - loc) / scale,
        (right - loc) / scale,
        loc,
        scale,
    ),  # Truncated normal: a, b = (left - loc) / scale, (right - loc) / scale
}


class Distribution:
    """Encapsulates the distribution choice logic, unifies
    init parameters for SciPy and NumPy functions
    """

    # __slots__ = ("name", "rng", "numpy", "func")
    SCIPY_DISTRIBUTIONS = {
        "uniform": uniform,
        "normal": norm,
        "beta": beta,
        "lognormal": lognorm,
        "triangular": triang,
        "truncated normal": truncnorm,
    }

    def __init__(self, name: str, rng: Generator) -> None:
        self.name = name.lower()
        self.rng = rng
        self.numpy = False
        self.func = self._init_func()

    def __call__(self, size, *args: Any, **kwargs: Any) -> Any:
        # Intersept kwargs and preprocess them
        self._unified_params(*args, **kwargs)

        # FOR NUMPY FUNCTIONS
        if self.numpy:
            values = self.func(size=size, *args, **kwargs)

        # FOR SCIPY FUNCTIONS
        values = self.func.rvs(
            size=size, random_state=self.rng, *args, **kwargs
        )

        return values

    def _init_func(self):
        # FOR SCIPY FUNCTIONS
        func = self.SCIPY_DISTRIBUTIONS.get(self.name, None)
        if func is not None:
            self.numpy = False
            return func
        # FOR NUMPY FUNCTIONS
        if hasattr(self.rng, self.name):
            self.numpy = True
            return getattr(self.rng, self.name)
        raise KeyError(
            "Function with a corresponding name " "not found in SciPy or NumPy"
        )

    def _unified_params(self, **kwargs):
        if not self.numpy:
            SCIPY_DISTRIBUTION_CONV[self.name]
            kwargs
        pass


# from numpy.random import (
#     MT19937,
#     PCG64,
#     PCG64DXSM,
#     SFC64,
#     Philox,
# )

# BIT_GENERATORS = {
#     "PCG64": PCG64,
#     "PCG64DXSM": PCG64DXSM,
#     "MT19937": MT19937,
#     "Philox": Philox,
#     "SFC64": SFC64,
# }


class UserContinuousDistribution(rv_continuous):
    """
    Allows to create user-defined distributions by defining
    PDF or PPF
    """

    def _pdf(self, x):
        pass

    def _cdf(self, x):
        pass


class UserDiscreteDistribution(rv_discrete):
    """
    Allows to create user-defined distributions by defining
    PDF(Probability density function) or PPF(Percent point function)
    functions as shown below
    """

    def _pdf(self, x):
        pass

    def _cdf(self, x):
        pass


# nmin = 0
# nmax = 50
# new_distribution = UserContinuousDistribution(
#     a=nmin, b=nmax, name="My Distribution Name"
# )
# N = 50000
# X = new_distribution.rvs(size=N, random_state=1)
