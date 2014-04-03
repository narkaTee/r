from test_service import Service, Stanza
from path_test import PathTestCase
from r import r


class RTestCase(PathTestCase):
    def test_r(self):
        service = Service([])
        input_data = [{'Name': 'Robert'}]
        _, rows = r(service, input_data, 'output = input')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Robert')

    def test_r_package_installation(self):
        service = Service([
            Stanza('package://zoo', {}),
            Stanza('package://lattice', {}),
        ])
        input_data = [{'Name': 'Robert'}]
        _, rows = r(service, input_data, '''
        library(zoo)
        output = input
        ''')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Robert')
