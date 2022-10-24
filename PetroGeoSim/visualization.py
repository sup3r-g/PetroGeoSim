import matplotlib.pyplot as plt

from PetroGeoSim.models import Model

plt.style.use("seaborn-notebook")
colors = plt.get_cmap("tab10")


def visualize_model_result(
    model: Model,
    bins: int | str = "auto",
    **kwargs
) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    (name, values), = model.result().items()
    print(values)
    ax.hist(values, bins=bins, ec="k", fc=colors(3), lw=0.3)
    ax.set_xlabel(name, **kwargs)
    ax.set_ylabel("Frequency", **kwargs)
    ax.set_title(f"Model {name}", **kwargs)


def visualize_properties_distributions(
    model: Model,
    bins: int | str = "auto",
    **kwargs
) -> None:
    properties = model.get_all_properties(
        'values',
        include=("inputs", "results"),
        invert_dict=True
    )
    fig, axes = plt.subplots(
        len(properties), len(model.regions), sharey="row", **kwargs
    )
    for j, (prop_name, regions) in enumerate(properties.items()):
        for i, (reg_name, values) in enumerate(regions.items()):
            axes[j, i].hist(values, bins=bins, ec="k", fc=colors(j), lw=0.3)
            axes[j, i].set_title(f"{prop_name} for Region {reg_name}")
            axes[j, i].set_xlabel(prop_name)
            axes[j, i].set_ylabel("Frequency")
