from typing import Any

from joblib import Parallel, cpu_count, delayed
from numpy.random import SeedSequence

from montepetro.models import Model
from montepetro.petroleum_properties import ModelOriginalOilInPlace, OriginalOilInPlace


class Simulation:
    def __init__(
        self,
        *args,
        sim_seed: int | None = None,
        num_samples: int = 100000,
        config: dict[str, Any],
        num_simulations: int = 1,
        parallel: bool = True,
        **kwargs,
    ) -> None:
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

    def __str__(self) -> str:
        pass

    def setup_model(self, name: str, seed: int, config: dict[str, Any]) -> None:
        model = Model(name, seed)
        model_regions = []
        model.add_regions(model_regions)

        random_properties = {}
        model.add_properties(random_properties)

        model.run(self.config)
        model.add_regional_property("OOIP", OriginalOilInPlace)

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
