import unittest
from PetroGeoSim.properties import Property


class TestProperty(unittest.TestCase):
    def setUp(self):
        self.property = Property('Пористость', 'porosity', 'normal', num_samples=1000)

    def test_stats_size(self):
        self.assertTrue(len(self.property.run_calculation()) == 5)
        self.assertFalse(len(self.property.run_calculation()) != 5)
