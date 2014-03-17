import os
import config
import subprocess
import scripts
import tempfile


def exeute(script_path, packages_library_path):
    r_path = config.get_r_path()

    #check if the R library is installed
    if not os.path.exists(r_path):
        raise Exception('R not installed')

    r_output_filename = None
    try:
        #create r output file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            r_output_filename = f.name

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
        output, error = process.communicate()
        if error is not None and len(error) > 0:
            raise Exception(error)
        if output is not None and len(output) > 0:
            raise Exception(output)

    finally:
        #delete temp file
        if r_output_filename:
            os.remove(r_output_filename)
