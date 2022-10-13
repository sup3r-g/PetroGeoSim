import re
from collections import defaultdict

from PetroGeoSim.distributions import SCIPY_DISTRIBUTION_KWARGS
from PetroGeoSim.properties import ResultProperty

split_pat = re.compile(r"[\|\\\t _,/:;]+")


def config_maker(model, user_input: bool = True) -> None:
    config = {}

    for reg_name, reg in model.regions.items():
        props = defaultdict(dict)
        for prop_name, prop in reg.properties.items():

            # Check to skip result properties if the model has been run already
            if isinstance(prop, ResultProperty):
                continue

            # Ask for user input or not
            if user_input:
                param_hint = ", ".join(
                    SCIPY_DISTRIBUTION_KWARGS[prop.distribution.name]
                )
                params_str = input(
                    f"Input distibution parameters for ( {param_hint} ) "
                    f"of Property {prop_name} in Region {reg_name}"
                )
                for param, value in zip(
                    SCIPY_DISTRIBUTION_KWARGS[prop.distribution.name],
                    re.split(split_pat, params_str),
                ):
                    props[prop_name][param] = float(value)
            else:
                props[prop_name] = SCIPY_DISTRIBUTION_KWARGS[
                    prop.distribution.name
                ]

        config[reg_name] = dict(props)

    return config
