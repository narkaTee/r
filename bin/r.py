from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, validators, Option
import csv
import tempfile
import os
import subprocess
import sys
from splunk.clilib import cli_common as cli
import base64
import urllib2
import lockfile

#authToken = settings['authString']
#import splunklib.client as client
#service = client.connect(token=authToken)
#a = service.apps["search"]
#st = a.state()

@Configuration(
    overrides_timeorder=True,
    local=True,
    retainsevents=False,
    passauth=True,
    stderr_dest='message'
)
class RCommand(StreamingCommand):

    def stream(self, records):

        r_snippet = self.script
        temp_path = tempfile.gettempdir()

        #read configuration file
        cli.cacheConfFile('r')
        r_config = cli.confSettings['r']

        #check if the R library presence
        r_path_config = r_config['paths']
        r_path = r_path_config.get('r')
        if not os.path.exists(r_path):
            raise Exception('Cannot find R executable at path \'%s\'' % r_path)

        #lock installing prerequirements
        lockfile_path = os.path.join(temp_path, 'r.lock')
        with lockfile.file_lock(lockfile_path):

            #make sure the temp directory exist
            r_temp_path = os.path.join(temp_path, 'r')
            #if os.path.exists(r_temp_path):
            #    import shutil
            #    shutil.rmtree(r_temp_path)
            if not os.path.exists(r_temp_path):
                os.makedirs(r_temp_path)

            #make sure that custom script files exists
            custom_scripts_path = os.path.join(r_temp_path, 'scripts')
            if not os.path.exists(custom_scripts_path):
                os.makedirs(custom_scripts_path)
            script_stanza_prefix = 'script://'
            for stanza_name in r_config:
                if stanza_name.startswith(script_stanza_prefix):
                    script_stanza = r_config[stanza_name]
                    script_content = base64.decodestring(script_stanza['content'])
                    script_filename = stanza_name[len(script_stanza_prefix):] + '.r'
                    script_full_path = os.path.join(custom_scripts_path, script_filename)
                    with open(script_full_path, 'wb') as f:
                        f.write(script_content)

            #make sure that required packages are downloaded
            packages_path = os.path.join(r_temp_path, 'packages')
            if not os.path.exists(packages_path):
                os.makedirs(packages_path)
            packages_stanza_prefix = 'package://'
            packages = []
            for stanza_name in r_config:
                if stanza_name.startswith(packages_stanza_prefix):
                    #package_stanza = r_config[stanza_name]
                    package_name = stanza_name[len(packages_stanza_prefix):]
                    package_path = os.path.join(packages_path, package_name) + '.tar.gz'
                    if not os.path.exists(package_path):
                        description_url = 'http://cran.r-project.org/web/packages/%s/DESCRIPTION' % package_name
                        description_data = urllib2.urlopen(description_url).read(20000)
                        version_key = 'Version:'
                        for description_line in description_data.split("\n"):
                            if description_line.startswith(version_key):
                                version = description_line[len(version_key):].strip()
                                package_url = 'http://cran.r-project.org/src/contrib/%s_%s.tar.gz' % (
                                    package_name, version)
                                package_data = urllib2.urlopen(package_url).read()
                                with open(package_path, 'wb') as f:
                                    f.write(package_data)
                                packages.append({
                                    'name': package_name,
                                    'path': package_path
                                })
                                break

            #make sure that required packages are installed
            library_path = os.path.join(r_temp_path, 'library')
            if not os.path.exists(library_path):
                os.makedirs(library_path)
            for package in packages:
                library_package_path = os.path.join(library_path, package['name'])
                if not os.path.exists(library_package_path):
                    command = "\"" + r_path + "\" CMD INSTALL -l \"" + library_path + "\" \"" + package['path'] + "\""
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        cwd=custom_scripts_path
                    )
                    _, output = process.communicate()
                    if output is None:
                        raise Exception('Unexpected output')
                    if not 'DONE' in output:
                        raise Exception('Unexpected output: %s' % output)

        #collect field names
        fieldnames = set()
        for result in records:
            for key in list(result.keys()):
                if not key in fieldnames:
                    fieldnames.add(key)
        fieldnames = list(fieldnames)
        if len(fieldnames) == 0:
            fieldnames = None

        input_csv_filename = None
        output_csv_filename = None
        script_filename = None
        r_output_filename = None
        try:
            #create CSV input file
            if fieldnames:
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    input_csv_filename = f.name
                    writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                    writer.writeheader()
                    writer.writerows(records)
            #create CSV output file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                output_csv_filename = f.name
            #create script file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                script_filename = f.name
                if input_csv_filename:
                    f.write('input <- read.csv("' + input_csv_filename.replace('\\', '\\\\') + '")\n')
                f.write(r_snippet + '\n')
                f.write('write.csv(output, file = "' + output_csv_filename.replace('\\', '\\\\') + '")\n')
            #create r output file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                r_output_filename = f.name

            #with open(input_csv_filename, "r") as f:
            #    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(f.read()))
            #    exit(0)
            process = subprocess.Popen(
                "\"" + r_path + "\" --vanilla" + " < \"" + script_filename + "\" > \"" + r_output_filename + "\"",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                cwd=custom_scripts_path,
                env={
                    'R_LIBS_USER': library_path
                },
            )
            output, error = process.communicate()
            if error is not None and len(error) > 0:
                raise Exception(error)
            if output is not None and len(output) > 0:
                raise Exception(output)

            #with open(output_csv_filename, "r") as f:
            #    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(f.read()))
            #    exit(0)

            #read csv output
            with open(output_csv_filename, "r") as f:
                reader = csv.reader(f)
                rows = [row for row in reader]
                if len(rows) > 0:
                    header_row = rows[0]
                    for row in rows[1:]:
                        record = {}
                        for i, cell in enumerate(row):
                            record[header_row[i]] = cell
                        yield record

        #delete temp files
        finally:
            if input_csv_filename:
                os.remove(input_csv_filename)
            if output_csv_filename:
                os.remove(output_csv_filename)
            if script_filename:
                os.remove(script_filename)
            if r_output_filename:
                os.remove(r_output_filename)

    script = Option(require=True)


dispatch(RCommand, sys.argv, sys.stdin, sys.stdout, __name__)