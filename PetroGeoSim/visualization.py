import matplotlib.pyplot as plt
import numpy as np

from PetroGeoSim.models import Model

plt.style.use("seaborn-notebook")

colors = plt.get_cmap("hsv")(np.linspace(0, 1, 20))
rng = np.random.default_rng()
rng.shuffle(colors)


def visualize_model(model: Model, bins: int | str = "auto", **mpl_kwargs) -> None:
    """_summary_

    _extended_summary_

    Parameters
    ----------
    model : Model
        An initialized Model instance.
    bins : int | str, optional
        _description_, by default "auto"
    """
    figsize = mpl_kwargs.pop("figsize", (20, 10))

    result_properties = model.get_result()
    _, axs = plt.subplots(
        len(result_properties), 2, squeeze=False, clear=True, figsize=figsize
    )

    for i, (name, values) in enumerate(result_properties.items()):
        hist, bin_edges = np.histogram(values, bins=bins, density=True)
        pdf_norm = hist * 100 / hist.sum()
        sf = 100 - pdf_norm.cumsum()
        percentiles = np.percentile(values, (10, 50, 90), method="median_unbiased")[
            ::-1
        ]

        parameters = (
            (
                0,
                f"PDF of Model {name}",
                pdf_norm,
                pdf_norm[np.digitize(percentiles, bin_edges)],
            ),
            (1, f"SF of Model {name}", sf, sf[np.digitize(percentiles, bin_edges)]),
        )

        for j, title, weight, y_coord in parameters:
            axs[i, j].hist(
                bin_edges[:-1],
                weights=weight,
                bins=bins,
                ec="k",
                fc=colors[-1],
                lw=0.3,
            )
            axs[i, j].stem(percentiles, y_coord, "k--", markerfmt="ko", basefmt=" ")
            axs[i, j].stem(
                y_coord,
                percentiles,
                "k--",
                markerfmt="ko",
                basefmt=" ",
                orientation="horizontal",
                bottom=bin_edges[:-1].min()
            )
            axs[i, j].set(
                title=title,
                xlabel=name,
                ylabel="Probability, %",
                xlim=(bin_edges[:-1].min(), bin_edges[:-1].max()),
                **mpl_kwargs,
            )


def visualize_input_properties(
    model: Model, bins: int | str = "auto", **mpl_kwargs
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
    figsize = mpl_kwargs.pop("figsize", (20, 60))

    properties = model.get_all_properties("values", include="inputs", invert_dict=True)
    _, axs = plt.subplots(
        len(properties),
        len(model.regions),
        sharey="row",
        squeeze=False,
        clear=True,
        figsize=figsize,
    )

    for i, (prop_name, regions) in enumerate(properties.items()):
        for j, (reg_name, values) in enumerate(regions.items()):
            hist, bin_edges = np.histogram(values, bins=bins, density=True)
            normalized = hist * 100 / hist.sum()
            axs[i, j].hist(
                bin_edges[:-1],
                weights=normalized,
                bins=hist.shape[0],
                ec="k",
                fc=colors[i],
                lw=0.3,
            )
            axs[i, j].set(
                title=f"{prop_name} for Region {reg_name}",
                xlabel=prop_name,
                ylabel="Probability, %",
                xlim=(bin_edges[:-1].min(), bin_edges[:-1].max()),
            )


def visualize_result_properties(
    model: Model, bins: int | str = "auto", **mpl_kwargs
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
    figsize = mpl_kwargs.pop("figsize", (10, 20))

    properties = model.get_all_properties(
        "values", include="results", invert_dict=False
    )

    _, axs = plt.subplots(
        2,
        len(model.regions),
        sharey="row",
        squeeze=False,
        clear=True,
        figsize=figsize,
    )

    for i, (reg_name, props) in enumerate(properties.items()):
        ((prop_name, values),) = props.items()
        hist, bin_edges = np.histogram(values, bins=bins, density=True)
        pdf_norm = hist * 100 / hist.sum()
        sf = 100 - pdf_norm.cumsum()
        percentiles = np.percentile(values, (10, 50, 90), method="median_unbiased")[
            ::-1
        ]

        parameters = (
            (
                0,
                f"PDF of {prop_name} for Region {reg_name}",
                pdf_norm,
                pdf_norm[np.digitize(percentiles, bin_edges)],
            ),
            (
                1,
                f"SF of {prop_name} for Region {reg_name}",
                sf,
                sf[np.digitize(percentiles, bin_edges)],
            ),
        )

        for j, title, weight, y_coord in parameters:
            axs[j, i].hist(
                bin_edges[:-1],
                weights=weight,
                bins=hist.shape[0],
                ec="k",
                fc=colors[-1],
                lw=0.3,
            )
            axs[j, i].stem(percentiles, y_coord, "k--", markerfmt="ko", basefmt=" ")
            axs[j, i].stem(
                y_coord,
                percentiles,
                "k--",
                markerfmt="ko",
                basefmt=" ",
                orientation="horizontal",
                bottom=bin_edges[:-1].min()
            )
            axs[j, i].set(
                title=title,
                xlabel=prop_name,
                ylabel="Probability, %",
                xlim=(bin_edges[:-1].min(), bin_edges[:-1].max()),
                **mpl_kwargs,
            )
