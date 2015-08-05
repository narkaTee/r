import os
import config
import subprocess
import tempfile
from errors import RError, InstallPackageError


def verify_r_path(r_path, raise_error):
    if r_path is None or r_path == '':
        raise_error('R path not set')
        return False
    if not os.path.exists(r_path):
        raise_error('Cannot find R at path \'%s\'' % r_path)
        return False
    if os.path.isdir(r_path):
        raise_error('Path \'%s\' points to a directory, but it should point to the R executalbe.' % r_path)
        return False
    if os.name != 'nt':
        if not os.access(r_path, os.X_OK):
            raise_error('Path \'%s\' points to non-executable file, but it should point to the R executalbe.' % r_path)
            return False
    else:
        if not r_path.endswith('.exe') and not r_path.endswith('.EXE'):
            raise_error('Path \'%s\' doesn\'t point to a .EXE file, but it should point to the R executalbe.' % r_path)
            return False
    return True


def exeute(service, script, library_path, scripts_path):
    r_path = config.get_r_path(service)

    # check if the R library is installed
    def raise_e_path_error(msg):
        raise RError(msg)
    verify_r_path(r_path, raise_e_path_error)

    r_output_filename = None
    error_path = None
    script_path = None
    try:
        # create r output file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            r_output_filename = f.name

        # create error file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            error_path = f.name

        # create script file
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
            cwd=scripts_path,
            env={
                'R_LIBS_USER': library_path
            },
        )
        std_output, std_error = process.communicate()
        if process.returncode:
            if std_error is not None and len(std_error) > 0:
                output = std_error.strip()
            elif std_output is not None and len(std_output) > 0:
                output = std_output.strip()
            else:
                output = None
            if output:
                raise RError('R exited with code %s: %s' % (process.returncode, output))
            else:
                raise RError('R exited with code %s' % process.returncode)

        with open(error_path) as f:
            err = f.read().strip()
            if len(err) > 0:
                if std_error is not None and len(std_error) > 0:
                    raise RError('%s, %s' % (err, std_error.strip()))
                elif std_output is not None and len(std_output) > 0:
                    raise RError('%s, %s' % (err, std_output.strip()))
                else:
                    raise RError('%s' % err)

    finally:
        # delete temp files
        if error_path:
            os.remove(error_path)
        if r_output_filename:
            os.remove(r_output_filename)
        if script_path:
            os.remove(script_path)


def install_package(service, library_path, package_name, package_path):
    r_path = config.get_r_path(service)

    # check if the R library is installed
    def raise_e_path_error(msg):
        raise InstallPackageError(package_name, msg)
    verify_r_path(r_path, raise_e_path_error)

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
