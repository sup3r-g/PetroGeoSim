from typing import Any

from joblib import Parallel, cpu_count, delayed
from numpy.random import SeedSequence

from PetroGeoSim.models import Model


class Simulation:

    # __slots__ = ("name", "sim_seed", "num_samples", "parallel", "num_simulations")

    def __init__(
        self,
        name,
        config: dict[str, Any],
        *args,
        sim_seed: int | None = None,
        num_samples: int = 100000,
        num_simulations: int = 1,
        parallel: bool = True,
        **kwargs,
    ) -> None:
        self.name = name
        if num_simulations <= 1:
            num_simulations = 1
            parallel = False
        self.sim_seed = sim_seed
        self.num_samples = num_samples

        self.parallel = parallel
        self.num_simulations = num_simulations
        self.config = config

        if self.num_simulations > 1:
            self.model_seeds = SeedSequence(self.sim_seed).generate_state(
                self.num_simulations
            )

    def __eq__(self, other) -> bool:
        return isinstance(other, Simulation) and (
            self.name,
            self.sim_seed,
            self.parallel,
            self.num_samples,
            self.num_simulations,
        ) == (
            other.name,
            other.sim_seed,
            other.parallel,
            other.num_samples,
            other.num_simulations,
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.name,
                self.sim_seed,
                self.parallel,
                self.num_samples,
                self.num_simulations,
            )
        )

    def __str__(self) -> str:
        pass

    def setup_model(self, name: str, seed: int, config: dict[str, Any]) -> None:
        model = Model(name, seed)
        model_regions = []
        model.add_regions(model_regions)

        random_properties = {}
        model.add_properties({random_properties})

        model.run(self.config)
        model.add_result_property("OOIP", OriginalOilInPlace)

        ooip = ModelOriginalOilInPlace(model)
        ooip.run_calculation()

    def run(self, n_jobs: int = cpu_count() // 2, **kwargs) -> None:
        if self.num_simulations == 1:
            self.setup_model("A simple reservoir model", self.sim_seed, self.config)

        if self.parallel or n_jobs > 1:
            _res = Parallel(n_jobs=n_jobs)(
                delayed(self.setup_model)(f"Simulation model №{i}", s, self.config)
                for i, s in enumerate(self.model_seeds)
            )
            results = dict(enumerate(_res))
        else:
            results = [
                self.setup_model(f"Simulation model №{i}", s, self.config)
                for i, s in enumerate(self.model_seeds)
            ]

        return results
