import matplotlib.pyplot as plt

from PetroGeoSim.models import Model
from PetroGeoSim.properties import Property

plt.style.use("seaborn-notebook")
colors = plt.get_cmap("tab10")

def visualize_model_result(
    prop: Property,
    bins: int | str = "auto",
    **kwargs
) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.hist(prop.values, bins=bins, ec="k", fc=colors(3), lw=0.3)
    ax.set_xlabel("Original Oil in Place", **kwargs)
    ax.set_ylabel("Frequency", **kwargs)
    ax.set_title("Model Original Oil in Place", **kwargs)


def visualize_properties_distributions(
    model: Model,
    bins: int | str = "auto",
    **kwargs
) -> None:
    properties = model.get_all_properties('values')
    fig, axes = plt.subplots(
        len(properties), len(model.regions), sharey="row", **kwargs
    )
    for j, (prop_name, regions) in enumerate(properties.items()):
        for i, (reg_name, values) in enumerate(regions.items()):
            axes[j, i].hist(values, bins=bins, ec="k", fc=colors(j), lw=0.3)
            axes[j, i].set_title(f"{prop_name} for Region {reg_name}")
            axes[j, i].set_xlabel(prop_name)
            axes[j, i].set_ylabel("Frequency")
