import path
import os
import urllib2
import framework
import config

scheme = 'package'
packages_path = path.get_named_path('packages')
library_path = path.get_named_path('library')


def refresh_packages(service):
    #make sure that required packages are downloaded
    if not os.path.exists(packages_path):
        os.makedirs(packages_path)
    package_list = []
    for stanza, package_name in config.iter_stanzas(service, scheme):
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
            framework.install_package(service, library_path, package['path'])