import path
import os
import urllib2
import framework
import config
import errors
from sys import platform as _platform

scheme = 'package'
packages_path = path.get_named_path('packages')
library_path = path.get_named_path('library')


class PackageInstallError(errors.Error):
    def __init__(self, name, reason):
        self.name = name
        super(PackageInstallError, self).__init__(
            'Cannot install package \'%s\'. %s' % (name, reason)
        )


class DescriptionDownloadError(PackageInstallError):
    def __init__(self, name, http_error):
        self.http_error = http_error
        super(DescriptionDownloadError, self).__init__(
            name,
            'Attempt to download CRAN description: %s' % str(http_error)
        )


class ArchiveDownloadError(PackageInstallError):
    def __init__(self, name, http_error):
        self.http_error = http_error
        super(ArchiveDownloadError, self).__init__(
            name,
            'Attempt to download compressed file: %s' % str(http_error)
        )


class ArchiveSaveError(PackageInstallError):
    def __init__(self, name, exception):
        self.exception = exception
        super(ArchiveSaveError, self).__init__(
            name,
            'Attempt to save compressed file: %s' % str(exception)
        )


def get_package_description_lines(package_name):
    description_url = 'http://cran.r-project.org/web/packages/%s/DESCRIPTION' % package_name
    try:
        description_data = urllib2.urlopen(description_url).read(20000)
    except urllib2.HTTPError as http_error:
        raise DescriptionDownloadError(package_name, http_error)
    return description_data.split("\n")


def refresh_packages(service):
    #make sure that required packages are downloaded
    if not os.path.exists(packages_path):
        os.makedirs(packages_path)
    package_list = []
    for stanza, package_name in config.iter_stanzas(service, scheme):
        package_path = os.path.join(packages_path, package_name) + '.tar.gz'
        if not os.path.exists(package_path):
            lines = get_package_description_lines(package_name)
            version_key = 'Version:'
            for description_line in lines:
                if description_line.startswith(version_key):
                    version = description_line[len(version_key):].strip()
                    if _platform == "linux" or _platform == "linux2":
                        # download source version
                        package_url = 'http://cran.r-project.org/src/contrib/%s_%s.tar.gz' % (package_name, version)
                    elif _platform == "darwin":
                        # Mac binary
                        package_url = 'http://cran.r-project.org/bin/macosx/contrib/r-release/%s_%s.tgz' % (
                            package_name, version)
                    elif _platform == "win32":
                        # Windows binary
                        package_url = 'http://cran.r-project.org/bin/windows/contrib/r-release/%s_%s.zip' % (
                            package_name, version)
                    else:
                        # download source version
                        package_url = 'http://cran.r-project.org/src/contrib/%s_%s.tar.gz' % (package_name, version)
                    try:
                        package_data = urllib2.urlopen(package_url).read()
                    except urllib2.HTTPError as http_error:
                        raise ArchiveDownloadError(package_name, http_error)
                    try:
                        with open(package_path, 'wb') as f:
                            f.write(package_data)
                    except Exception as e:
                        raise ArchiveSaveError(package_name, e)
                    break
        package_list.append({
            'name': package_name,
            'path': package_path
        })

    #make sure that required packages are installed
    if not os.path.exists(library_path):
        os.makedirs(library_path)
    for package in package_list:
        library_package_path = os.path.join(library_path, package['name'])
        if not os.path.exists(library_package_path):
            try:
                framework.install_package(service, library_path, package['path'])
            except framework.InstallError as install_error:
                raise PackageInstallError(package['name'], install_error.message)
            except Exception as e:
                raise PackageInstallError(package['name'], str(e))


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def add(service, name):
    config.create_stanza(service, scheme, name, {
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)