from test_service import Service
from path_test import PathTestCase
import r_stats
import packages


class RStatsTestCase(PathTestCase):
    def test_get_r_config_file(self):
        service = Service()
        packages.add(service,'boot')
        r_stats.r_stats(service)
        indexed_events = [post['query']['body'] for post in service.indexes['r'].service.posts]

        self.assertEqual(len(indexed_events), 2)

        post = service.indexes['r'].service.posts[0]
        body = post['query']['body']
        self.assertTrue('stats_package_name=\"boot\"' in body)

        post = service.indexes['r'].service.posts[1]
        body = post['query']['body']
        self.assertTrue('stats_number_of_packages=\"1\"' in body)