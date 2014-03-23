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


def get_package_description_info(package_name):
    lines = get_package_description_lines(package_name)
    version_key = 'Version:'
    version = None
    for description_line in lines:
        if description_line.startswith(version_key):
            version = description_line[len(version_key):].strip()
    if not version:
        raise DescriptionParseError(package_name, 'Version field not found')
    return version


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


def download_packages(service):

    # download required package archives
    downloded_file_names = set()
    package_list = []
    for stanza, package_name in config.iter_stanzas(service, scheme):
        local_file_name = get_local_package_filename(package_name)
        local_package_path = os.path.join(packages_path, local_file_name)
        if not os.path.exists(local_package_path):
            version = get_package_description_info(package_name)
            package_url = get_remote_package_url(package_name, version)
            download_package(package_name, local_package_path, package_url)
        package_list.append({
            'name': package_name,
            'path': local_package_path
        })
        downloded_file_names.add(local_file_name)

    # remove packages that are no longer in the list of required packages
    for filename in os.listdir(packages_path):
        if not filename in downloded_file_names:
            script_path = os.path.join(packages_path, filename)
            os.remove(script_path)

    return package_list


def install_packages(downloaded_packages, service):

    # install downloaded packages
    installes_package_names = set()
    for package in downloaded_packages:
        package_name = package['name']
        library_package_path = os.path.join(library_path, package_name)
        if not os.path.exists(library_package_path):
            try:
                framework.install_package(service, library_path, package['path'])
            except framework.InstallError as install_error:
                raise PackageInstallError(package_name, install_error.message)
            except Exception as e:
                raise PackageInstallError(package_name, str(e))
        installes_package_names.add(package_name)

    # uninstall packages that are no longer in the list of required packages
    for package_name in os.listdir(library_path):
        if not package_name in installes_package_names:
            if not package_name.startswith('.'):
                package_path = os.path.join(packages_path, package_name)
                os.remove(package_path)


def update_library(service):

    # make sure directories exists
    if not os.path.exists(packages_path):
        os.makedirs(packages_path)
    if not os.path.exists(library_path):
        os.makedirs(library_path)

    downloaded_packages = download_packages(service)
    install_packages(downloaded_packages, service)


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def add(service, name):
    config.create_stanza(service, scheme, name, {
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)