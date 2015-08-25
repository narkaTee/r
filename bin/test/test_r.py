from test_service import Service, Stanza
from test_path import PathTestCase
from r import r
import r_scripts as scriptlib

class RTestCase(PathTestCase):
    def test_r(self):
        service = Service([
        ])
        input_data = [{'Name': 'Robert'}]
        _, rows = r(service, input_data, 'output = input')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Robert')

    def test_r_package_installation(self):
        service = Service([
            Stanza('package://race', {})
        ])
        input_data = [{'Name': 'Robert'}]
        _, rows = r(service, input_data, '''
        library(race)
        output = input
        ''')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Name'], 'Robert')

    def test_r_package_usage(self):
        import r_index_logging
        r_index_logging.clear_log_entries()

        service = Service([
            Stanza('package://race', {}),
            Stanza('package://boot', {})
        ])
        _, rows = r(service, None, '''
        library(race)
        library(boot)
        library(race)
        output = data.frame(h1=c('v1'))
        ''')
        indexed_events = r_index_logging.get_log_entries()

        def is_indexed(text):
            for e in indexed_events:
                if text in e:
                    return True
            return False
        self.assertTrue(is_indexed('action=\"package_usage\"'))
        self.assertTrue(is_indexed('package_name=\"race\"'))
        self.assertTrue(is_indexed('action=\"package_usage\"'))
        self.assertTrue(is_indexed('package_name=\"boot\"'))

    def test_r_package_usage_from_custom_script(self):
        import r_index_logging
        r_index_logging.clear_log_entries()

        service = Service([
            Stanza('package://race', {}),
            Stanza('package://boot', {})
        ])
        scriptlib.add(service, 'test', """
        library(race)
        add <- function(a,b) {
          c = a+b
          return(c)
        }
        result = add(4,10)
        output = data.frame(Result=c(result))
        """)
        _, rows = r(service, None, 'test.r')
        indexed_events = r_index_logging.get_log_entries()

        def is_indexed(text):
            for e in indexed_events:
                if text in e:
                    return True
            return False
        self.assertTrue(is_indexed('action=\"package_usage\"'))
        self.assertTrue(is_indexed('package_name=\"race\"'))
