from test_service import Service, Stanza
from path_test import PathTestCase
from r import r
import scripts as scriptlib


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
        import index_logging
        index_logging.clear_log_entries()

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
        indexed_events = index_logging.get_log_entries()
        self.assertEqual(len(indexed_events), 4)
        self.assertTrue('action=\"package_usage\"' in indexed_events[1])
        self.assertTrue('package_name=\"race\"' in indexed_events[1])
        self.assertTrue('action=\"package_usage\"' in indexed_events[2])
        self.assertTrue('package_name=\"boot\"' in indexed_events[2])

    def test_r_package_usage_from_custom_script(self):
        import index_logging
        index_logging.clear_log_entries()

        service = Service([
            Stanza('package://race', {}),
            Stanza('package://boot', {}),
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
        indexed_events = index_logging.get_log_entries()
        self.assertEqual(len(indexed_events), 3)
        self.assertTrue('action=\"package_usage\"' in indexed_events[1])
        self.assertTrue('package_name=\"race\"' in indexed_events[1])

    def test_r_multi_value_output(self):
        service = Service([])
        _, rows = r(service, None, 'output = data.frame(Result=list(1, 2, 5))')
        #self.assertTrue(False,str(rows))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Result'], [1,2,5])
