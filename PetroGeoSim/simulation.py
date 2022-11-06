from copy import deepcopy

from joblib import Parallel, cpu_count, delayed
from numpy.random import SeedSequence

from PetroGeoSim.models import Model


class Simulation:

    # __slots__ = ("name", "sim_seed", "num_samples", "num_simulations", "models")

    def __init__(
        self,
        name: str,
        sim_seed: int | None = None,
        num_samples: int = 10000,
        num_simulations: int = 1
    ) -> None:
        self.name = name
        self.sim_seed = SeedSequence(sim_seed)
        self.num_samples = num_samples
        self.num_simulations = max(num_simulations, 1)
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
        # Multi model simulation cas
        if self.num_simulations > 1:
            model = deepcopy(model)

        model.update(**update_kwargs)
        model.run(model_config)

    def add_models(self, *models: tuple[Model]) -> None:
        """_summary_

        _extended_summary_

        Raises
        ------
        KeyError
            _description_
        """

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
        # (Basically no difference from the standalone Model)
        if self.num_simulations == 1:
            print("Number of simulations is set to 1, parallel mode disabled")

            self._setup_models(
                seed=self.sim_seed,
                num_samples=self.num_samples
            )

        # Multi model simulation case
        model_seeds = self.sim_seed.generate_state(
            self.num_simulations
        )

        if parallel:
            _res = Parallel(n_jobs=parallel)(
                delayed(self._setup_models)(
                    name=f"Simulation model №{i}",
                    seed=s,
                    num_samples=self.num_samples
                )
                for i, s in enumerate(model_seeds)
            )

            results = dict(enumerate(_res))
        else:
            results = [
                self._setup_models(
                    name=f"Simulation model №{i}",
                    seed=s,
                    num_samples=self.num_samples
                )
                for i, s in enumerate(model_seeds)
            ]

        return results
