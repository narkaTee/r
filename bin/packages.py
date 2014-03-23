import path
import os
import urllib2
import framework
import config
import errors
from sys import platform as _platform
import shutil
import re
from controlfile import ControlFile

scheme = 'package'
packages_path = path.get_named_path('packages')
library_path = path.get_named_path('library')


class PackageInstallError(errors.Error):
    def __init__(self, name, reason):
        self.name = name
        super(PackageInstallError, self).__init__(
            'Cannot install package \'%s\'. %s' % (name, reason)
        )


class DescriptionParseError(PackageInstallError):
    def __init__(self, name, reason):
        self.reason = reason
        super(DescriptionParseError, self).__init__(
            name,
            'Attempt to parse CRAN description: %s' % reason
        )


class DescriptionDownloadError(PackageInstallError):
    def __init__(self, name, url, reason):
        self.reason = reason
        self.url = url
        super(DescriptionDownloadError, self).__init__(
            name,
            'Attempt to download CRAN description from \'%s\': %s' % (url, reason)
        )


class ArchiveDownloadError(PackageInstallError):
    def __init__(self, name, url, reason):
        self.reason = reason
        super(ArchiveDownloadError, self).__init__(
            name,
            'Attempt to download compressed file from \'%s\': %s' % (url, reason)
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
        raise DescriptionDownloadError(package_name, description_url, str(http_error))
    except urllib2.URLError as url_error:
        raise DescriptionDownloadError(package_name, description_url, url_error.reason)
    return description_data.split('\n')


def get_local_package_filename(package_name):
    if _platform == "linux" or _platform == "linux2":
        package_file_name = '%s.tar.gz' % package_name
    elif _platform == "darwin":
        package_file_name = '%s.tgz' % package_name
    elif _platform == "win32":
        package_file_name = '%s.zip' % package_name
    else:
        package_file_name = '%s.tar.gz' % package_name
    return package_file_name


def get_remote_package_url(package_name, version):
    package_url_prefix = 'http://cran.r-project.org'
    if _platform == "linux" or _platform == "linux2":
        package_url = '%s/src/contrib/%s_%s.tar.gz' % (package_url_prefix, package_name, version)
    elif _platform == "darwin":
        package_url = '%s/bin/macosx/contrib/r-release/%s_%s.tgz' % (
            package_url_prefix, package_name, version)
    elif _platform == "win32":
        package_url = '%s/bin/windows/contrib/r-release/%s_%s.zip' % (
            package_url_prefix, package_name, version)
    else:
        package_url = '%s/src/contrib/%s_%s.tar.gz' % (package_url_prefix, package_name, version)
    return package_url


def get_package_version(package_name, lines):
    version_key = 'Version:'
    for description_line in lines:
        if description_line.startswith(version_key):
            return description_line[len(version_key):].strip()
    raise DescriptionParseError(package_name, 'Version field not found')


pkg_name_regex = re.compile(r'\s*(\w+)\s*(?:\(.*\))?\s*')


def get_package_dependencies(package_name, description_path):
    ship_package_names = set()
    ship_package_names.add('R')
    ship_package_names.add('graphics')
    ship_package_names.add('stats')
    ship_package_names.add('utils')
    ship_package_names.add('methods')
    ship_package_names.add('grDevices')
    ship_package_names.add('grid')
    ship_package_names.add('parallel')
    with open(description_path, 'r') as f:
        control_file = ControlFile(fileobj=f)
        dependencies = []
        package_list_keys = ['Depends', 'Imports']
        for package_list_key in package_list_keys:
            if package_list_key in control_file.para:
                depends_value = control_file.para[package_list_key]
                for depends_component in depends_value.split(','):
                    match = pkg_name_regex.match(depends_component)
                    if not match:
                        raise DescriptionParseError(package_name, 'Invalid \'Depends\' component: %s' % depends_component)
                    dependend_package_name = match.group(1)
                    if not dependend_package_name in ship_package_names:
                        dependencies.append(dependend_package_name)
        return dependencies


def download_package(package_name, package_path, package_url):
    try:
        package_data = urllib2.urlopen(package_url).read()
    except urllib2.HTTPError as http_error:
        raise ArchiveDownloadError(package_name, package_url, str(http_error))
    except urllib2.URLError as url_error:
        raise ArchiveDownloadError(package_name, package_url, url_error.reason)
    try:
        with open(package_path, 'wb') as f:
            f.write(package_data)
    except Exception as e:
        raise ArchiveSaveError(package_name, e)


def update_library(service):

    # make sure directories exists
    if not os.path.exists(packages_path):
        os.makedirs(packages_path)
    if not os.path.exists(library_path):
        os.makedirs(library_path)

    downloaded_filenames = set()
    installes_packages = set()

    def require_package(name):
        archive_name = get_local_package_filename(name)

        # check if packages is already downloaded
        if archive_name in downloaded_filenames:
            return

        # download is not exists
        archive_path = os.path.join(packages_path, archive_name)
        if not os.path.exists(archive_path):
            lines = get_package_description_lines(name)
            version = get_package_version(name, lines)
            package_url = get_remote_package_url(name, version)
            download_package(name, archive_path, package_url)
        downloaded_filenames.add(archive_name)

        # install package if required
        library_package_path = os.path.join(library_path, name)
        if not os.path.exists(library_package_path):
            try:
                framework.install_package(service, library_path, name, archive_path)
            except framework.InstallPackageError as install_error:
                raise PackageInstallError(name, install_error.message)
            except Exception as e:
                raise PackageInstallError(name, str(e))
        installes_packages.add(name)

        # check dependencies
        description_path = os.path.join(library_package_path, 'DESCRIPTION')
        #with open(description_path) as f:
        #    lines = f.read().split('\n')
        dependencies = get_package_dependencies(name, description_path)
        for dependent_package_name in dependencies:
            require_package(dependent_package_name)

    # download required package archives
    for stanza, package_name in config.iter_stanzas(service, scheme):
        require_package(package_name)

    # remove packages that are no longer in the list of required packages
    for filename in os.listdir(packages_path):
        if not filename in downloaded_filenames:
            script_path = os.path.join(packages_path, filename)
            os.remove(script_path)

    # uninstall packages that are no longer in the list of required packages
    for package_name in os.listdir(library_path):
        if not package_name in installes_packages:
            if not package_name.startswith('.'):
                package_path = os.path.join(library_path, package_name)
                shutil.rmtree(package_path)


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def add(service, name):
    config.create_stanza(service, scheme, name, {
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)