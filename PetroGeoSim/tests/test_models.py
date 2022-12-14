import unittest
from PetroGeoSim.models import Model
from PetroGeoSim.regions import Region


class TestModel(unittest.TestCase):
    # setUp method is overridden from the parent class TestCase
    def setUp(self):
        self.model = Model('name')

    # Each test method starts with the keyword test_

    def test_add_regions(self):
      """
      CHECK FOR PEP8, indentation must by 4 spaces!!!

      В PetroGeoSim Probabillistic Reserves RU сказано, что нельзя добавлять
      два региона с одинаковыми именами. В данной функции я создал два региона
      с одинаковыми именами и разными составами. При этом никакой ошибки не
      возникает.
      """

      region_1 = Region('A','Sandstone')
      region_2 = Region('A','Dolomite')
      print(region_1)  # print in test is redundant
      print(region_2)  # print in test is redundant
      self.assertTrue(region_1 == region_2)
      # add assertFalse condition (if not your test will always show true)
