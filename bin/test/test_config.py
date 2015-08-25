from unittest import TestCase
import r_config
from test_service import Service, Stanza
import os


class ConfigTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        r_config.ignore_cache = True

    @classmethod
    def tearDownClass(cls):
        r_config.ignore_cache = False


class MyConfigTestCase(ConfigTestCase):
    def test_get_r_config_file(self):
        service = Service()
        r_config_file = r_config.get_r_config_file(service)
        self.assertIsNotNone(r_config_file)

    def test_get_r_path(self):
        service = Service()
        r_path = r_config.get_r_path(service)
        self.assertTrue(os.path.exists(r_path), 'invalid R path: %s' % r_path)

    def test_iter_stanzas(self):
        service = Service([
            Stanza('script://test1', {}),
            Stanza('package://test2', {}),
            Stanza('script://test3', {}),
        ])
        cnt = 0
        for stanza, name in r_config.iter_stanzas(service, 'script'):
            self.assertTrue(name.startswith('test'))
            self.assertTrue(stanza.name.startswith('script://'))
            cnt += 1
        self.assertEqual(2, cnt)

    def test_create_stanza(self):
        service = Service([
            Stanza('script://test1', {}),
            Stanza('package://test2', {}),
            Stanza('script://test3', {}),
        ])
        r_config.create_stanza(service, 'test', 'test4', {
            'a': 'b'
        })
        cnt = 0
        for stanza, name in r_config.iter_stanzas(service, 'test'):
            self.assertEqual(cnt, 0)
            cnt += 1
            self.assertEqual(getattr(stanza, 'a'), 'b')

    def test_delete_stanza(self):
        service = Service([
            Stanza('script://test1', {}),
            Stanza('package://test2', {}),
            Stanza('script://test3', {}),
        ])
        r_config.delete_stanza(service, 'script', 'test3')
        r_config.delete_stanza(service, 'script', 'test1')
        for _ in r_config.iter_stanzas(service, 'script'):
            self.fail('No stanza should be found')
        cnt = 0
        for stanza, name in r_config.iter_stanzas(service, 'package'):
            self.assertEqual('package://test2', stanza.name)
            cnt += 1
        self.assertEqual(1, cnt)
