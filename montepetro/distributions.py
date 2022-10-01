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

from numpy.random import (
    MT19937,
    PCG64,
    PCG64DXSM,
    SFC64,
    Philox,
)

PETROLEUM_DISTRIBUTION_PARAMETERS = {
    "Area": "lognormal",
    "Thickness": "lognormal",
    "Porosity": "normal",
    "Water saturation": "normal",
    "Density": "normal",
    "Volume factor": "normal",
}

SCIPY_DISTRIBUTIONS = {
    "uniform": uniform,
    "normal": norm,
    "beta": beta,
    "lognormal": lognorm,
    "triangular": triang,
    "truncated normal": truncnorm,
}

BIT_GENERATORS = {
    "PCG-64": PCG64,
    "PCG-64 DXSM": PCG64DXSM,
    "MT19937": MT19937,
    "Philox": Philox,
    "SFC64": SFC64,
}


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
