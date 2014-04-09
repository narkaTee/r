from unittest import TestCase
from test_service import Service
import index_logging


class IndexLoggingTestCase(TestCase):
    def test_get_r_config_file(self):
        service = Service()
        index_logging.log(service, __file__, {
            'f1': 'v1'
        })
        self.assertEqual(len(service.indexes['r'].service.posts),1)
        post = service.indexes['r'].service.posts[0]
        body = post['query']['body']
        self.assertTrue('f1=\"v1\"' in body)