import json
from pathlib import Path

import numpy as np
import numpy.typing as npt

from PetroGeoSim.models import Model
from PetroGeoSim.properties import RandomProperty, ResultProperty


class Templates:

    __slots__ = ("templates", "available")

    def __init__(self) -> None:
        self.templates = {}
        self.available = tuple(
            temp.stem for temp in Path('PetroGeoSim/templates/').iterdir()
        )

    def load(self, code: str) -> None:
        if code not in self.available:
            raise KeyError(f"No template found for code {code}")

        with open(f"PetroGeoSim/templates/{code}.json", "r", encoding='utf8') as fp:
            self.templates = json.load(fp=fp)

    def show(self) -> dict:
        return self.templates

    def get(self, *args) -> dict:
        template_props = {}

        for opt in args:
            if opt in self.templates:
                template_props[opt] = (
                    RandomProperty(
                        opt, self.templates[opt][1]
                    )
                )
            else:
                print(
                    f"Found invalid template name: {opt}\nSkipping..."
                )

        return template_props


class OriginalOilInPlace(ResultProperty):

    __slots__ = ("info")

    def __init__(
        self,
        name: str,
        info: dict[str, npt.NDArray],
        *args,
        **kwargs
    ) -> None:
        super().__init__(name, *args, **kwargs)
        self.info = info

    def _calc(self) -> npt.NDArray[np.floating]:
        phi = self.info["Porosity"]
        area = self.info["Area"]
        s_w = self.info["Sw"]
        ooip = area * phi * (1.0 - s_w)
        return ooip


class ModelOriginalOilInPlace(ResultProperty):

    __slots__ = ("model")

    def __init__(self, model: Model, name: str, *args, **kwargs) -> None:
        super().__init__(name, *args, **kwargs)
        self.model = model

    def _calc(self) -> np.typing.NDArray[np.floating]:
        return np.sum(
            [
                reg.properties["OOIP"].values
                for reg in self.model.regions.values()
            ],
            axis=0,
        )
