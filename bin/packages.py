import path
import os
from splunk.clilib import cli_common as cli
import urllib2
import subprocess
import framework

script_stanza_prefix = 'script://'
packages_path = path.get_named_path('packages')
library_path = path.get_named_path('library')

#read configuration file
cli.cacheConfFile('r')
r_config = cli.confSettings['r']


def refresh_packages():
    #make sure that required packages are downloaded
    if not os.path.exists(packages_path):
        os.makedirs(packages_path)
    packages_stanza_prefix = 'package://'
    package_list = []
    for stanza_name in r_config:
        if stanza_name.startswith(packages_stanza_prefix):
            package_stanza = r_config[stanza_name]
            package_name = stanza_name[len(packages_stanza_prefix):]
            package_path = os.path.join(packages_path, package_name) + '.tar.gz'
            if not os.path.exists(package_path):
                description_url = 'http://cran.r-project.org/web/packages/%s/DESCRIPTION' % package_name
                description_data = urllib2.urlopen(description_url).read(20000)
                version_key = 'Version:'
                for description_line in description_data.split("\n"):
                    if description_line.startswith(version_key):
                        version = description_line[len(version_key):].strip()
                        package_url = 'http://cran.r-project.org/src/contrib/%s_%s.tar.gz' % (package_name, version)
                        package_data = urllib2.urlopen(package_url).read()
                        with open(package_path, 'wb') as f:
                            f.write(package_data)
                        package_list.append({
                            'name': package_name,
                            'path': package_path
                        })
                        break

    #make sure that required packages are installed
    if not os.path.exists(library_path):
        os.makedirs(library_path)
    for package in package_list:
        library_package_path = os.path.join(library_path, package['name'])
        if not os.path.exists(library_package_path):
            command = "\"" + framework.r_path + "\" CMD INSTALL -l \"" + library_path + "\" \"" + package['path'] + "\""
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            _, output = process.communicate()
            if output is None:
                raise Exception('Unexpected output')
            if not 'DONE' in output:
                raise Exception('Unexpected output: %s' % output)