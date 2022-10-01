import matplotlib.pyplot as plt

plt.style.use("seaborn-notebook")


def visualize_model_property(prop, bins: int | str = "auto", **kwargs):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.hist(prop.values, bins=bins, ec="k", fc="g", lw=0.3)
    ax.set_xlabel("Original Oil in Place", **kwargs)
    ax.set_ylabel("Frequency", **kwargs)
    ax.set_title("Model Original Oil in Place", **kwargs)


def visualize_regional_distributions(model, bins: int | str = "auto", **kwargs):
    colors = plt.get_cmap("tab10")
    properties = model.get_all_properties()
    fig, axes = plt.subplots(
        len(properties), len(model.regions), sharey="row", **kwargs
    )
    for j, (prop_name, regions) in enumerate(properties.items()):
        for i, (region_name, values) in enumerate(regions.items()):
            axes[j, i].hist(values, bins=bins, ec="k", fc=colors(j), lw=0.3)
            axes[j, i].set_title(f"{prop_name} for region {region_name}")
