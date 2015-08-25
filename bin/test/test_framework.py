import r_framework
from test_service import Service, Stanza
from test_path import PathTestCase
import tempfile
import csv
import os
import r_scripts
import r_packages


class FrameworkTestCase(PathTestCase):
    def test_execute(self):
        service = Service([
            Stanza('script://test1', {}),
            Stanza('package://test2', {}),
            Stanza('script://test3', {}),
        ])
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_csv_filename = f.name
        try:
            script = 'output = data.frame(a=c(1,2,3))\n'
            script += 'write.csv(output, file = "' + output_csv_filename.replace('\\', '\\\\') + '")\n'
            r_framework.exeute(
                service,
                script,
                r_packages.get_library_path(),
                r_scripts.get_custom_scripts_path(),
            )
            with open(output_csv_filename, 'r') as f:
                reader = csv.reader(f)
                rows = [row for row in reader]
        finally:
            os.remove(output_csv_filename)
        self.assertEqual(len(rows), 4)


