from PetroGeoSim.models import Model
from PetroGeoSim.properties import RegionalProperty
import numpy as np

class OriginalOilInPlace(RegionalProperty):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _calc(self):
        phi = self.region.properties["Porosity"].values
        area = self.region.properties["Area"].values
        s_w = self.region.properties["Sw"].values
        ooip = area * phi * (1.0 - s_w)
        return ooip


class ModelOriginalOilInPlace(RegionalProperty):
    def __init__(self, model: Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

    def _calc(self):
        ooips = [
            region.properties["OOIP"].values for region in self.model.regions.values()
        ]

        return np.sum(ooips, axis=0)
