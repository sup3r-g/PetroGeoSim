import json
import os
from collections import defaultdict

from PetroGeoSim.models import Model
# from PetroGeoSim.properties import Property
# from PetroGeoSim.regions import Region


def send_mygeomap(model: Model) -> dict[str, dict]:
    initial_result = model.get_all_properties(
        "values", include=("inputs", "results")
    )

    # Converts all NumPy arrays to lists (to enable serialization)
    final_result = defaultdict(dict)
    for reg, props in initial_result.items():
        for prop, vals in props.items():
            final_result[reg][prop] = vals.tolist()

    return dict(final_result)


def receive_mygeomap(file) -> "Model":
    if not os.path.isfile(file):
        raise FileNotFoundError("No such file or directory exists.")

    with open(file, "r", encoding="utf-8") as fp:
        setup_config = json.load(fp=fp)

    if "config" in setup_config:
        setup_config["regions"] = setup_config.pop("config")

    return Model.deserialize(setup_config)

    # model = Model(
    #     setup_config["name"],
    #     setup_config["seed"],
    #     setup_config["num_samples"]
    # )

    # run_config = defaultdict(dict)
    # for reg_name, reg_setup in setup_config["config"].items():
    #     region = Region(reg_name, reg_setup["composition"])
    #     model.add_regions(region)
    #     properties = []
    #     for prop_name, prop_setup in reg_setup["inputs"].items():
    #         prop = Property(
    #             prop_name,
    #             distribution=prop_setup["distribution"]["name"]
    #         )
    #         properties.append(prop)
    #         run_config[reg_name][prop_name] = prop_setup["distribution"]["params"]
    #     for prop_name, prop_setup in reg_setup["results"].items():
    #         prop = Property(
    #             prop_name,
    #             equation=prop_setup["equation"]
    #         )
    #         properties.append(prop)
    #     region.add_properties(*properties)

    # model.run(run_config)

    # return model
