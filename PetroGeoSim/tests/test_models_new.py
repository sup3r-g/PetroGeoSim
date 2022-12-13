import unittest
from PetroGeoSim.models import Model


class TestModels(unittest.TestCase):
    """ Не тестировали функции, которые ничего не возвращают.
    """

    def setUp(self):
        self.model = Model('A', 300, 100000)
        self.property = Model.get_all_properties(self.model, 'ddd', ['a', 'b', 'c'])
        self.result = Model.get_result(self.model)
        self.config = Model.check_config(self.model, {'A': self.property})
        self.serialize = Model.serialize(self.model)
        self.deserialize = {'A': [300, 100000]}

    def test_stats_size(self):
        self.assertFalse(type(self.model) == tuple)
        self.assertTrue(type(self.model) != tuple)

    def test_add_properties(self):
        pass

    def test_get_all_properties(self):
        self.assertFalse(type(self.property) != dict)
        self.assertTrue(type(self.property) == dict)

    def test_get_result(self):
        self.assertTrue(type(self.result) == dict)
        self.assertFalse(type(self.result) != dict)

    def test_check_config(self):
        '''
        В функции указано, что тип значений входного словаря может быть любым.
        Но на самом деле тербуется вложенный словарь.
        Не придумали, как проверить.
        '''

        self.assertTrue(type(self.config) == bool)
        self.assertFalse(type(self.config) != bool)

    def test_update(self):
        pass

    def test_tun(self):
        pass

    def test_serialize(self):
        self.assertTrue(type(self.serialize) == dict)
        self.assertFalse(type(self.serialize) != dict)

    def test_to_json(self):
        pass

    def test_deserialize(self):
        '''
        Есть вопросы.

        Failure
        Traceback (most recent call last):
        File "C:\Users\Timur\Documents\GitHub\MSU_petro_utils\PetroGeoSim\tests\test_models_new.py", line 63, in test_deserialize
        self.assertEquals(type(self.model), type(self.deserialize))
        AssertionError: <class 'PetroGeoSim.models.Model'> != <class 'dict'>
        '''

        self.assertEquals(type(self.model), type(self.deserialize))

    def test_from_json(self):
        pass
