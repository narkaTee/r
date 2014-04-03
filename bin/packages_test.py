from test_service import Service, Stanza
from path_test import PathTestCase
import os
import packages


class PackagesTestCase(PathTestCase):
    def test_update_library(self):
        service = Service([
            Stanza('package://boot', {}),
        ])
        packages.update_library(service)
        installed_packages = os.listdir(packages.get_library_path())
        self.assertEqual(len(installed_packages), 1)
        self.assertEqual(installed_packages[0], 'boot')
        self.assertEqual(packages.get_package_state('boot'), packages.metadata_package_installed)
        packages.update_library(service)
        installed_packages = os.listdir(packages.get_library_path())
        self.assertEqual(len(installed_packages), 1)
        self.assertEqual(installed_packages[0], 'boot')
        self.assertEqual(packages.get_package_state('boot'), packages.metadata_package_installed)
        packages.add(service, 'forecast')
        self.assertEqual(packages.get_package_state('forecast'), packages.metadata_package_not_installed)
        packages.update_library(service)
        installed_packages = os.listdir(packages.get_library_path())
        self.assertTrue('boot' in installed_packages)
        self.assertTrue('forecast' in installed_packages)
        self.assertEqual(packages.get_package_state('boot'), packages.metadata_package_installed)
        self.assertEqual(packages.get_package_state('forecast'), packages.metadata_package_installed)
        packages.remove(service, 'boot')
        self.assertEqual(packages.get_package_state('boot'), packages.metadata_package_installed)
        packages.update_library(service)
        installed_packages = os.listdir(packages.get_library_path())
        self.assertFalse('boot' in installed_packages)
        self.assertTrue('timeDate' in installed_packages)
        self.assertTrue('forecast' in installed_packages)
        self.assertEqual(packages.get_package_state('boot'), packages.metadata_package_not_installed)
        self.assertEqual(packages.get_package_state('timeDate'), packages.metadata_package_installed)
        self.assertEqual(packages.get_package_state('forecast'), packages.metadata_package_installed)
