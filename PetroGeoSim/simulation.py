from copy import deepcopy
from typing import Literal

from joblib import Parallel, cpu_count, delayed
from numpy.random import SeedSequence

from PetroGeoSim.models import Model


class Simulation:

    # __slots__ = ("name", "sim_seed", "num_samples", "num_simulations", "multi_model", "models")

    def __init__(
        self,
        name: str,
        sim_seed: int | None = None,
        num_samples: int = 10000,
        num_simulations: int = 1,
        mode: Literal["single", "multi"] = "single"
    ) -> None:
        self.name = name
        self.sim_seed = SeedSequence(sim_seed)
        self.num_samples = num_samples
        self.num_simulations = max(num_simulations, 1)
        self.mode = mode
        self.models = {}

    def __eq__(self, other) -> bool:
        return isinstance(other, Simulation) and (
            self.name,
            self.sim_seed,
            self.num_samples,
            self.num_simulations,
        ) == (
            other.name,
            other.sim_seed,
            other.num_samples,
            other.num_simulations,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.name,
                self.sim_seed,
                self.num_samples,
                self.num_simulations,
            )
        )

    def __str__(self) -> str:
        return (
            f'SIMULATION "{self.name}"\n'
            f"* Simulation seed: {self.sim_seed}\n"
            f"* Number of samples: {self.num_samples}\n"
            f"* Number of simulations: {self.num_simulations}\n"
        )

    def _setup_models(self, **update_kwargs: dict) -> None:
        # Single model simulation case
        model = list(self.models.values())[0]
        # Multi model simulation case
        if self.num_simulations > 1:
            model = deepcopy(model)

        model.update(**update_kwargs)
        model.run(model_config)

        return model

    def _spawn_simulations(self) -> None:
        for i, model in enumerate(self.models):
            single_simulation = deepcopy(self)
            single_simulation.update(
                name=f"{self.name}_sub_{i}",
                mode="single",
                models={model.name: model}
            )
            single_simulation.run()

        return 

    def add_models(self, *models: tuple[Model]) -> None:
        """_summary_

        _extended_summary_

        Raises
        ------
        KeyError
            _description_
        """

        if self.mode == "single" and len(models) > 1:
            raise TypeError(
                "Can't add more than one model when ",
                "not in single model mode ('mode' set to 'single')"
            )

        for model in models:
            if model in self.models:
                raise KeyError(
                    f'Encountered duplicate Model "{model.name}" '
                    f'in Simulation "{self.name}"'
                )

            self.models[model.name] = model

    def update(self, **update_kwargs: dict) -> None:
        """_summary_

        _extended_summary_

        Raises
        ------
        AttributeError
            _description_
        """

        for attr, val in update_kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, val)
            else:
                raise AttributeError(f'Simulation has no attribute "{attr}".')

    def run(self, parallel: bool | int = cpu_count() // 2) -> dict | list:
        """_summary_

        _extended_summary_

        Parameters
        ----------
        parallel : bool | int, optional
            _description_, by default cpu_count()//2

        Returns
        -------
        dict | list
            _description_
        """

        # Single model simulation case
        # (Basically the same as the standalone Model)
        if self.num_simulations == 1:
            parallel = False
            print("Number of simulations is set to 1, parallel mode disabled")

            model = self._setup_models(
                seed=self.sim_seed,
                num_samples=self.num_samples
            )

            return model

        # Multi model simulation case
        model_seeds = self.sim_seed.generate_state(
            self.num_simulations
        )

        _res = Parallel(n_jobs=parallel)(
            delayed(self._setup_models)(
                name=f"Simulation model №{i}",
                seed=s,
                num_samples=self.num_samples
            )
            for i, s in enumerate(model_seeds)
        )

        return dict(enumerate(_res))
