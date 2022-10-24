from scipy.stats import rv_continuous, rv_discrete


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
