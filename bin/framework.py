import os
import config
import subprocess
import scripts
import tempfile
import errors


class RError(errors.Error):
    def __init__(self, message):
        self.message = message
        super(RError, self).__init__(message)


def exeute(service, script, packages_library_path):
    r_path = config.get_r_path(service)

    #check if the R library is installed
    if not os.path.exists(r_path):
        raise Exception('R not installed')

    r_output_filename = None
    error_path = None
    script_path = None
    try:
        #create r output file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            r_output_filename = f.name

        #create error file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            error_path = f.name

        #create script file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            script_path = f.name
            f.write("""
tryCatch(
{
            """)
            f.write(script)
            f.write("""
},
error=function(err) {
            fileConn<-file('""")
            f.write(error_path.replace('\\', '\\\\'))
            f.write("""')
            writeLines(c(conditionMessage(err)), fileConn)
            close(fileConn)
})
            """)

        process = subprocess.Popen(
            "\"" + r_path + "\" --vanilla" + " < \"" + script_path + "\" > \"" + r_output_filename + "\"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=scripts.custom_scripts_path,
            env={
                'R_LIBS_USER': packages_library_path
            },
        )
        process.communicate()
        #output, error = process.communicate()
        #if error is not None and len(error) > 0:
        #    raise RError(error)
        #if output is not None and len(output) > 0:
        #    raise RError(output)

        with open(error_path) as f:
            err = f.read()
            if len(err) > 0:
                raise RError(err)

    finally:
        #delete temp files
        if error_path:
            os.remove(error_path)
        if r_output_filename:
            os.remove(r_output_filename)
        if script_path:
            os.remove(script_path)


class InstallPackageError(RError):
    def __init__(self, package_name, message):
        self.package_name = package_name
        super(InstallPackageError, self).__init__(
            'Unable to install package \'%s\': %s' % (package_name, message)
        )


def install_package(service, library_path, package_name, package_path):
    r_path = config.get_r_path(service)

    # check if the R library is installed
    if not os.path.exists(r_path):
        raise InstallPackageError(package_name, 'R not installed')

    # dont't install if the package already exists in library
    library_package_path = os.path.join(library_path, package_name)
    if os.path.exists(library_package_path):
        raise InstallPackageError(package_name, 'Already installed')

    command = "\"" + r_path + "\" CMD INSTALL -l \"" + library_path + "\" \"" + package_path + "\""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    _, output = process.communicate()

    # package directory doesn't exists after installation?
    if not os.path.exists(library_package_path):
        raise InstallPackageError(package_name, output)