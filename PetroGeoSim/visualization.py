import matplotlib.pyplot as plt

from PetroGeoSim.models import Model

plt.style.use("seaborn-notebook")
colors = plt.get_cmap("tab10")


def visualize_model(
    model: Model,
    bins: int | str = "auto",
    **mpl_kwargs
) -> None:
    """_summary_

    _extended_summary_

    Parameters
    ----------
    model : Model
        An initialized Model instance.
    bins : int | str, optional
        _description_, by default "auto"
    """

    _, ax = plt.subplots(figsize=(8, 8))
    (name, values), = model.get_result().items()

    ax.hist(values, bins=bins, ec="k", fc=colors(3), lw=0.3)
    ax.set_xlabel(name, **mpl_kwargs)
    ax.set_ylabel("Frequency", **mpl_kwargs)
    ax.set_title(f"Model {name}", **mpl_kwargs)


def visualize_properties(
    model: Model,
    bins: int | str = "auto",
    **mpl_kwargs
) -> None:
    """_summary_

    _extended_summary_

    Parameters
    ----------
    model : Model
        _description_
    bins : int | str, optional
        _description_, by default "auto"
    """

    properties = model.get_all_properties(
        'values',
        include=("inputs", "results"),
        invert_dict=True
    )
    _, axes = plt.subplots(
        len(properties), len(model.regions), sharey="row", **mpl_kwargs
    )
    for j, (prop_name, regions) in enumerate(properties.items()):
        for i, (reg_name, values) in enumerate(regions.items()):
            axes[j, i].hist(values, bins=bins, ec="k", fc=colors(j), lw=0.3)
            axes[j, i].set_title(f"{prop_name} for Region {reg_name}")
            axes[j, i].set_xlabel(prop_name)
            axes[j, i].set_ylabel("Frequency")
