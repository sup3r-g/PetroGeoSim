import re
from collections import defaultdict

from PetroGeoSim.distributions import DISTRIBUTIONS_KWARGS
# from PetroGeoSim.properties import ResultProperty

split_pat = re.compile(r"[\|\\\t _,/:;]+")


def config_maker(model, user_input: bool = True) -> None:
    config = {}

    for reg_name, reg in model.regions.items():
        props = defaultdict(dict)
        for prop_name, prop in reg.inputs.items():
            # Ask for user input or not
            if user_input:
                param_hint = ", ".join(
                    DISTRIBUTIONS_KWARGS[prop.distribution.name]
                )
                params_str = input(
                    f"Input distribution parameters for ( {param_hint} ) "
                    f"of Property {prop_name} in Region {reg_name}"
                )
                for param, value in zip(
                    DISTRIBUTIONS_KWARGS[prop.distribution.name],
                    re.split(split_pat, params_str),
                ):
                    props[prop_name][param] = float(value)
            else:
                props[prop_name] = DISTRIBUTIONS_KWARGS[
                    prop.distribution.name
                ]

        config[reg_name] = dict(props)

    return config
