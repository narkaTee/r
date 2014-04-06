import csv
import tempfile
import os
import traceback
import sys
from StringIO import StringIO
import scripts
import packages
import framework
import errors
import re
import shutil
import uuid
from collections import Iterable


def log(service, fields):
    r_index = service.indexes["r"]
    args = {
        'index': r_index.name,
        'source': __file__,
        'sourcetype': 'r'
    }
    body = ''
    for k in fields:
        v = fields[k]
        if isinstance(v, list) or isinstance(v, set):
            body += ', '.join(['%s=\"%s\" ' % (k, f) for f in v])
        else:
            body += '%s=\"%s\" ' % (k, v)
    r_index.service.post(
        '/services/receivers/simple',
        body=body,
        **args)


def r(service, events, command_argument, fieldnames=None):
    if not events:
        events = []

    r_id = str(uuid.uuid1())

    log(service, {
        'r_id': r_id,
        'action': 'command',
        'phase': 'pre',
        'r_script': command_argument,
        'input_nb_events': len(events),
        'input_fieldnames': ', '.join(fieldnames)
    })

    #installing prerequirements
    scripts.create_files(service)
    packages.update_library(service)

    #collect field names
    if fieldnames is None:
        fieldnames = set()
        for result in events:
            for key in list(result.keys()):
                if not key in fieldnames:
                    fieldnames.add(key)
        if len(fieldnames) == 0:
            fieldnames = None

    input_csv_filename = None
    output_csv_filename = None
    try:
        #create CSV input file
        if fieldnames:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                input_csv_filename = f.name
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(events)
        #create CSV output file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_csv_filename = f.name

        #create script file
        script = ''
        if input_csv_filename:
            script += 'input <- read.csv("' + input_csv_filename.replace('\\', '\\\\') + '")\n'
        command_argument_regex = re.match(r'^(\w+\.[rR])$', command_argument)
        if command_argument_regex:
            script_name = command_argument_regex.group(1)
            script = 'source(\'' + script_name + '\')\n'
        else:
            script_content = command_argument
            script += script_content + '\n'
        script += 'write.csv(output, file = "' + output_csv_filename.replace('\\', '\\\\') + '")\n'

        framework.exeute(
            service,
            script,
            packages.get_library_path(),
            scripts.get_custom_scripts_path(),
        )

        #read csv output
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

        log(service, {
            'r_id': r_id,
            'action': 'command',
            'phase': 'post',
            'output_nb_events': len(output),
            'output_fieldnames': ', '.join(header_row)
        })

        return header_row, output

    #delete temp files
    finally:
        if input_csv_filename:
            os.remove(input_csv_filename)
        if output_csv_filename:
            os.remove(output_csv_filename)


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

        #read command arguments
        #keywords, kvs = splunk.Intersplunk.getKeywordsAndOptions()
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

        #connect to splunk using SDK
        service = get_service(settings['infoPath'])

        header, rows = r(service,
                         input_events,
                         command_argument,
                         fieldnames=fieldnames)
        splunk.Intersplunk.outputResults(rows, fields=header)

    except errors.Error as e:
        splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e)))

    except Exception as e:
        splunk.Intersplunk.outputResults(
            splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))


if __name__ == '__main__':
    main()