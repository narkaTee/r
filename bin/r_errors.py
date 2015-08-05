

class Error(Exception):
    pass


class RError(Error):
    def __init__(self, message):
        self.message = message
        super(RError, self).__init__(message)


class InstallPackageError(RError):
    def __init__(self, package_name, message):
        self.package_name = package_name
        super(InstallPackageError, self).__init__(
            'Unable to install package \'%s\': %s' % (package_name, message)
        )
