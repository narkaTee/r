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
import lockfile
from splunklib.binding import HTTPError

scheme = 'package'

_make_sure_directories_exists_called = False

metadata_package_installed = 'Installed'
metadata_package_installing = 'Installing'
metadata_package_downloading = 'Downloading'
metadata_package_installing_dependencies = 'Installing Dependencies'
metadata_package_installation_error = 'Installation Error'
metadata_package_not_installed = 'Not Installed'

metadata_package_value_set = set()
metadata_package_value_set.add(metadata_package_installed)
metadata_package_value_set.add(metadata_package_installing)
metadata_package_value_set.add(metadata_package_downloading)
metadata_package_value_set.add(metadata_package_installing_dependencies)
metadata_package_value_set.add(metadata_package_installation_error)
metadata_package_value_set.add(metadata_package_not_installed)


def get_packages_path():
    return path.get_directory('packages')


def get_library_path():
    return path.get_directory('library')


def get_packages_metadata_path():
    return path.get_directory('metadata', 'packages')


def lock_packages_and_library():
    lock_file_path = path.get_file('packages_and_library.lock')
    return lockfile.file_lock(lock_file_path)


def lock_metadata():
    lock_file_path = path.get_file('metadata.lock')
    return lockfile.file_lock(lock_file_path)


class PackageInstallError(errors.Error):
    def __init__(self, name, reason):
        self.name = name
        super(PackageInstallError, self).__init__(
            'Cannot install package \'%s\'. %s' % (name, reason)
        )


class DependendPackageError(PackageInstallError):
    def __init__(self, name, dependend_package_name, inner_error):
        self.inner_error = inner_error
        super(DependendPackageError, self).__init__(
            name,
            'Dependend package %s: %s' % (dependend_package_name, str(inner_error))
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


def get_remote_package_url(package_name, version, force_source=False):
    package_url_prefix = 'http://cran.r-project.org'
    if _platform == "linux" or _platform == "linux2" or force_source:
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


skip_package_names = set()
skip_package_names.add('R')
skip_package_names.add('base')
skip_package_names.add('boot')
skip_package_names.add('class')
skip_package_names.add('cluster')
skip_package_names.add('codetools')
skip_package_names.add('compiler')
skip_package_names.add('datasets')
skip_package_names.add('foreign')
skip_package_names.add('graphics')
skip_package_names.add('grDevices')
skip_package_names.add('grid')
skip_package_names.add('KernSmooth')
skip_package_names.add('lattice')
skip_package_names.add('MASS')
skip_package_names.add('Matrix')
skip_package_names.add('methods')
skip_package_names.add('mgcv')
skip_package_names.add('nlme')
skip_package_names.add('nnet')
skip_package_names.add('parallel')
skip_package_names.add('rpart')
skip_package_names.add('spatial')
skip_package_names.add('splines')
skip_package_names.add('stats')
skip_package_names.add('stats4')
skip_package_names.add('survival')
skip_package_names.add('tcltk')
skip_package_names.add('tools')
skip_package_names.add('utils')

pkg_name_regex = re.compile(r'\s*([\w\.]+)\s*(?:\(.*\))?\s*')


def get_package_name(description_file):
    control_file = ControlFile(fileobj=description_file)
    if 'Package' in control_file.para:
        depends_value = control_file.para['Package']
        return depends_value
    return None


supported_tar_extensions = set()
supported_tar_extensions.add('.tgz')
supported_tar_extensions.add('.tar')
supported_tar_extensions.add('.gz')
supported_tar_extensions.add('.gztar')
supported_tar_extensions.add('.bztar')


def get_package_name_from_archive_file(archive_filename, archive_file):
    from os.path import splitext
    root, ext = splitext(archive_filename)
    if ext in supported_tar_extensions:
        import tarfile
        with tarfile.open(fileobj=archive_file, mode='r') as tar:
            for tarinfo in tar:
                if tarinfo.name.endswith('DESCRIPTION'):
                    description_file = tar.extractfile(tarinfo)
                    package_name = get_package_name(description_file)
                    return package_name
    if ext == '.zip':
        import zipfile
        with zipfile.ZipFile(archive_file, 'r') as z:
            for memberInfo in z.infolist():
                if memberInfo.filename.endswith('DESCRIPTION'):
                    with z.open(memberInfo.filename) as description_file:
                        package_name = get_package_name(description_file)
                        return package_name
    raise errors.Error('Unsupported archive: %s' % archive_filename)


def get_package_dependencies(package_name, description_path):
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
                        raise DescriptionParseError(
                            package_name,
                            'Invalid \'Depends\' component: %s' % depends_component
                        )
                    dependend_package_name = match.group(1)
                    if dependend_package_name not in skip_package_names:
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


def get_metadata_package_state_filename(package_name):
    return package_name


def get_metadata_package_state_filepath(package_name):
    packages_metadata_path = get_packages_metadata_path()
    return os.path.join(packages_metadata_path, get_metadata_package_state_filename(package_name))


def _update_package_state(package_name, state):
    with lock_metadata():
        package_metadata_path = get_metadata_package_state_filepath(package_name)
        with open(package_metadata_path, 'w+') as f:
            f.write(state)
    return state


def get_package_state(package_name):
    with lock_metadata():
        package_metadata_path = get_metadata_package_state_filepath(package_name)
        if os.path.exists(package_metadata_path):
            with open(package_metadata_path, 'r') as f:
                state = f.read()
            state = state.strip()
            if state in metadata_package_value_set:
                return state
            else:
                os.remove(package_metadata_path)
                return get_package_state(package_name)
        else:
            library_path = get_library_path()
            library_package_path = os.path.join(library_path, package_name)
            library_installed = os.path.exists(library_package_path)
            if library_installed:
                return _update_package_state(package_name, metadata_package_installed)
            else:
                return _update_package_state(package_name, metadata_package_not_installed)


def install_package(service, name):
    with lock_packages_and_library():

        # check if packages is already installed or currently installing
        state = get_package_state(name)
        if state != metadata_package_not_installed \
                and state != metadata_package_installation_error:
            return

        installed = False
        try:
            # download is not exists
            archive_name = get_local_package_filename(name)
            packages_path = get_packages_path()
            archive_path = os.path.join(packages_path, archive_name)
            if not os.path.exists(archive_path):
                _update_package_state(name, metadata_package_downloading)
                lines = get_package_description_lines(name)
                version = get_package_version(name, lines)
                package_url = get_remote_package_url(name, version)
                try:
                    download_package(name, archive_path, package_url)
                except ArchiveDownloadError:
                    package_url = get_remote_package_url(name, version, force_source=True)
                    download_package(name, archive_path, package_url)

            # install package if required
            library_path = get_library_path()
            library_package_path = os.path.join(library_path, name)
            if not os.path.exists(library_package_path):
                _update_package_state(name, metadata_package_installing)
                try:
                    framework.install_package(service, library_path, name, archive_path)
                except errors.InstallPackageError as install_error:
                    raise PackageInstallError(name, install_error.message)
                except Exception as e:
                    raise PackageInstallError(name, str(e))

            # check dependencies
            description_path = os.path.join(library_package_path, 'DESCRIPTION')
            dependencies = get_package_dependencies(name, description_path)
            if len(dependencies) > 0:
                _update_package_state(name, metadata_package_installing_dependencies)
                for dependent_package_name in dependencies:
                    try:
                        install_package(service, dependent_package_name)
                    except Exception as e:
                        raise DependendPackageError(name, dependent_package_name, e)

            installed = True
        finally:
            if not installed:
                state = _update_package_state(name, metadata_package_installation_error)
            else:
                state = _update_package_state(name, metadata_package_installed)
    return state


def dependent_package_names(name):
    yielded_names = set()
    library_path = get_library_path()
    library_package_path = os.path.join(library_path, name)
    description_path = os.path.join(library_package_path, 'DESCRIPTION')
    dependencies = get_package_dependencies(name, description_path)
    for dependent_package_name in dependencies:
        if dependent_package_name not in yielded_names:
            yielded_names.add(dependent_package_name)
            for package_name in dependent_package_names(dependent_package_name):
                yielded_names.add(package_name)
    return yielded_names


def all_package_names(service):
    yielded_names = set()
    for _, package_name in config.iter_stanzas(service, scheme):
        yielded_names.add(package_name)
        for dependent_package_name in dependent_package_names(package_name):
            yielded_names.add(dependent_package_name)
    return yielded_names


def update_library(service):
    with lock_packages_and_library():

        # download required package archives
        for stanza, package_name in config.iter_stanzas(service, scheme):
            install_package(service, package_name)

        # collect files that should be present
        archive_filenames = set()
        package_metadata_filenames = set()
        package_names = all_package_names(service)
        for package_name in package_names:
            archive_filenames.add(get_local_package_filename(package_name))
            package_metadata_filenames.add(get_metadata_package_state_filename(package_name))

        # remove packages that are no longer in the list of required packages
        packages_path = get_packages_path()
        for filename in os.listdir(packages_path):
            if filename not in archive_filenames:
                script_path = os.path.join(packages_path, filename)
                os.remove(script_path)

        # uninstall packages that are no longer in the list of required packages
        library_path = get_library_path()
        for package_name in os.listdir(library_path):
            if package_name not in package_names:
                if not package_name.startswith('.'):
                    package_path = os.path.join(library_path, package_name)
                    shutil.rmtree(package_path)

        # delete packages metadata that are no longer in the list of required packages
        packages_metadata_path = get_packages_metadata_path()
        for filename in os.listdir(packages_metadata_path):
            if filename not in package_metadata_filenames:
                if not filename.startswith('.'):
                    package_metadata_path = os.path.join(packages_metadata_path, filename)
                    os.remove(package_metadata_path)


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def can_add(service):
    config_file = config.get_r_config_file(service)
    try:
        return config_file.itemmeta()['access']['can_write'] == '1'
    except HTTPError:
        return False


def add(service, name):
    config.create_stanza(service, scheme, name, {
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)
