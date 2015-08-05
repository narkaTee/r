# coding=utf-8
import csv
import tempfile
import os
import traceback
import sys
from StringIO import StringIO
import scripts
import packages
import framework
import r_errors
import re
import shutil
import uuid
import index_logging
import config


def log(fields):
    index_logging.log(__file__, fields)


def r(service, events, command_argument, fieldnames=None):
    if not events:
        events = []

    # collect field names
    if fieldnames is None:
        fieldnames = set()
        for result in events:
            for key in list(result.keys()):
                if key not in fieldnames:
                    fieldnames.add(key)
        if len(fieldnames) == 0:
            fieldnames = None

    r_id = str(uuid.uuid1())

    log({
        'r_id': r_id,
        'action': 'command',
        'phase': 'pre',
        'r_script': command_argument,
        'input_nb_events': len(events),
        'input_fieldnames': ', '.join(fieldnames) if fieldnames else '',
        })

    # installing prerequirements
    scripts.create_files(service)
    packages.update_library(service)

    input_csv_filename = None
    output_csv_filename = None
    output_library_usage_csv_filename = None
    try:
        # create CSV input file
        if fieldnames:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                input_csv_filename = f.name
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(events)
        # create CSV output files
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_csv_filename = f.name
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_library_usage_csv_filename = f.name

        # create script file
        script = 'library.usage = data.frame(name=c()) \n'
        script += 'original_library = library \n'
        script += 'new_library <- function(pkg, help, pos = 2, lib.loc = NULL, character.only = FALSE, '
        script += ' logical.return = FALSE, warn.conflicts = TRUE, quietly = FALSE, verbose = getOption("verbose"))\n'
        script += '{\n'
        script += '  if( is.symbol(substitute(pkg)) ) pkg=deparse(substitute(pkg))\n'
        script += '  library.usage <<- rbind(library.usage, data.frame(name=pkg))\n'
        script += '  return (original_library(package=pkg, help, pos, lib.loc, character.only=TRUE, logical.return,'
        script += '    warn.conflicts, quietly , verbose))\n'
        script += '}\n'
        script += 'library = new_library\n'

        # read content of csv file into input variable
        if input_csv_filename:
            options = 'check.names=FALSE, stringsAsFactors=FALSE'
            if options:
                options = options.strip()
            if options and len(options) > 0:
                options_with_comma = ', '+options
            else:
                options_with_comma = ''
            script += 'input <- read.csv( "' + input_csv_filename.replace('\\', '\\\\') + '" ' \
                      + options_with_comma + ')\n'

        command_argument_regex = re.match(r'^(\w+\.[rR])$', command_argument)
        if command_argument_regex:
            script_name = command_argument_regex.group(1)
            script += 'source(\'' + script_name + '\')\n'
        else:
            script_content = command_argument
            script += script_content + '\n'

        # write content of output variable to csv file
        options = ''
        if options:
            options = options.strip()
        if options and len(options) > 0:
            options_with_comma = ', '+options
        else:
            options_with_comma = ''
        script += 'write.csv(output, file = "' + output_csv_filename.replace('\\', '\\\\') + '" '\
                  + options_with_comma + ')\n'

        script += 'write.csv(library.usage, file = "' + output_library_usage_csv_filename.replace('\\', '\\\\') + '")\n'

        framework.exeute(
            service,
            script,
            packages.get_library_path(),
            scripts.get_custom_scripts_path(),
        )

        # read library usage
        with open(output_library_usage_csv_filename, "r") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
            package_names = set()
            if len(rows) > 0:
                header_row = rows[0]
                for row in rows[1:]:
                    event = {}
                    for i, cell in enumerate(row):
                        event[header_row[i]] = cell
                    package_name = event['name']
                    if package_name not in package_names:
                        package_names.add(package_name)
                        log({
                            'r_id': r_id,
                            'action': 'package_usage',
                            'package_name': package_name,
                            })

        # read csv output
        with open(output_csv_filename, "r") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
            if len(rows) == 0:
                return []
            header_row = rows[0]
            output = []
            for row in rows[1:]:
                event = {}
                for i, cell in enumerate(row):
                    event[header_row[i]] = cell
                output.append(event)

        log({
            'r_id': r_id,
            'action': 'command',
            'phase': 'post',
            'output_nb_events': len(output),
            'output_fieldnames': ', '.join(header_row) if header_row else '',
            })

        return header_row, output

    except Exception as e:
        log({
            'r_id': r_id,
            'action': 'command',
            'phase': 'exception',
            'exception': str(e),
            })
        raise

    # delete temp files
    finally:
        if input_csv_filename:
            os.remove(input_csv_filename)
        if output_csv_filename:
            os.remove(output_csv_filename)
        if output_library_usage_csv_filename:
            os.remove(output_library_usage_csv_filename)


def main():
    from splunklib.searchcommands import csv as splunkcsv

    del splunkcsv

    import splunk.Intersplunk

    from utils import get_service, read_fieldnames_from_command_input

    try:
        # check execution mode: it could be 'getinfo' to get some information about
        # how to execute the actual command
        (isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)
        if isgetinfo:
            splunk.Intersplunk.outputInfo(
                streaming=False,  # because it only runs on a search head
                generating=False,
                retevs=False,
                reqsop=False,
                preop=None,
                timeorder=True,
                clear_req_fields=False,
                req_fields=None
            )

        # read command arguments
        # keywords, kvs = splunk.Intersplunk.getKeywordsAndOptions()
        if len(sys.argv) < 2:
            raise Exception("Missing actual R script parameter")
        command_argument = sys.argv[1]

        # read header, fieldnames, and events from input stream
        input_data = StringIO()
        shutil.copyfileobj(sys.stdin, input_data)
        input_data.seek(0)
        fieldnames = read_fieldnames_from_command_input(input_buf=input_data)
        input_data.seek(0)
        settings = {}
        input_events = splunk.Intersplunk.readResults(input_data, settings)

        # connect to splunk using SDK
        service = get_service(settings['infoPath'])

        header, rows = r(service,
                         input_events,
                         command_argument,
                         fieldnames=fieldnames)
        splunk.Intersplunk.outputResults(rows, fields=header)

    except r_errors.Error as e:
        splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e)))

    except Exception as e:
        splunk.Intersplunk.outputResults(
            splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))


if __name__ == '__main__':
    main()