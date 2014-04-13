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
            Stanza('package://race', {}),
        ])
        input_data = [{'Name': 'Robert'}]
        _, rows = r(service, input_data, '''
        library(race)
        output = input
        ''')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Robert')

    def test_r_package_usage(self):
        service = Service([
            Stanza('package://race', {}),
            Stanza('package://boot', {}),
        ])
        _, rows = r(service, None, '''
        library(race)
        library(boot)
        library(race)
        output = data.frame(h1=c('v1'))
        ''')
        indexed_events = [post['query']['body'] for post in service.indexes['r'].service.posts]
        self.assertEqual(len(indexed_events), 4)
        post = service.indexes['r'].service.posts[1]
        body = post['query']['body']
        self.assertTrue('action=\"package_usage\"' in body)
        self.assertTrue('package_name=\"race\"' in body)
        post = service.indexes['r'].service.posts[2]
        body = post['query']['body']
        self.assertTrue('action=\"package_usage\"' in body)
        self.assertTrue('package_name=\"boot\"' in body)
