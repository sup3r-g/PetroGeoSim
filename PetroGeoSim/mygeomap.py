from collections import defaultdict

from PetroGeoSim.models import Model


def send_mygeomap(model: Model) -> dict[str, dict]:
    initial_result = model.get_all_properties("values", include=("inputs", "results"))
    initial_stats = model.get_all_properties("stats", include=("inputs", "results"))

    # Converts all NumPy arrays to lists (to enable serialization)
    final_result = defaultdict(dict)
    for reg, props in initial_result.items():
        for prop, vals in props.items():
            final_result[reg][prop] = {
                "values": vals.tolist(),
                "stats": {
                    "P90": (initial_stats[reg][prop]["P10"], 90),
                    "P50": (initial_stats[reg][prop]["P50"], 50),
                    "P10": (initial_stats[reg][prop]["P90"], 10),
                },
            }

    return dict(final_result)


def receive_mygeomap(setup_config: dict[str, dict]) -> "Model":
    if "config" in setup_config:
        setup_config["regions"] = setup_config.pop("config")

    return Model.deserialize(setup_config)
