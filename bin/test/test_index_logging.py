from unittest import TestCase
from test_service import Service
import r_index_logging


class IndexLoggingTestCase(TestCase):
    def test_get_r_config_file(self):
        import r_index_logging
        r_index_logging.clear_log_entries()

        r_index_logging.log(__file__, {
            'f1': 'v1'
        })

        log_entries = r_index_logging.get_log_entries()

        self.assertEqual(len(log_entries), 1)
        self.assertTrue('f1=\"v1\"' in log_entries[0])
