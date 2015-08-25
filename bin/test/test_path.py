from test_config import ConfigTestCase
import r_path

temp_tempdir_segment = None


class PathTestCase(ConfigTestCase):

    @classmethod
    def setUpClass(cls):
        ConfigTestCase.setUpClass()
        global temp_tempdir_segment
        temp_tempdir_segment = r_path.tempdir_segment
        r_path.tempdir_segment = 'r_test'

    @classmethod
    def tearDownClass(cls):
        r_path.tempdir_segment = temp_tempdir_segment
        ConfigTestCase.tearDownClass()

    def setUp(self):
        r_path.delete_path_root()