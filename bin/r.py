from splunklib.searchcommands import csv as splunkcsv
del splunkcsv
import csv
import tempfile
import splunk.Intersplunk
import os
import traceback
import sys
import lockfile
from utils import get_service
import path
import scripts
import packages
import framework
import errors

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

    #read command options, input headers and data
    keywords, kvs = splunk.Intersplunk.getKeywordsAndOptions()
    if len(sys.argv) < 2:
        raise Exception("Missing actual R script parameter")
    r_snippet = sys.argv[1]
    settings = {}
    input_data = splunk.Intersplunk.readResults(sys.stdin, settings)

    #connect to splunk using SDK
    service = get_service(settings['infoPath'])

    #lock installing prerequirements
    lock_file_path = path.get_named_path('r.lock')
    with lockfile.file_lock(lock_file_path):
        scripts.create_files(service)
        packages.refresh_packages(service)

    #collect field names
    fieldnames = set()
    for result in input_data:
        for key in list(result.keys()):
            if not key in fieldnames:
                fieldnames.add(key)
    fieldnames = list(fieldnames)
    if len(fieldnames) == 0:
        fieldnames = None

    input_csv_filename = None
    output_csv_filename = None
    script_filename = None
    try:
        #create CSV input file
        if fieldnames:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                input_csv_filename = f.name
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                writer.writerows(input_data)
        #create CSV output file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_csv_filename = f.name
        #create script file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            script_filename = f.name
            if input_csv_filename:
                f.write('input <- read.csv("' + input_csv_filename.replace('\\', '\\\\') + '")\n')
            f.write(r_snippet + '\n')
            f.write('write.csv(output, file = "' + output_csv_filename.replace('\\', '\\\\') + '")\n')

        framework.exeute(service, script_filename, packages.library_path)

        #read csv output
        output = []
        with open(output_csv_filename, "r") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
            if len(rows) == 0:
                splunk.Intersplunk.outputResults([])
                exit(0)
            header_row = rows[0]
            for row in rows[1:]:
                event = {}
                for i, cell in enumerate(row):
                    event[header_row[i]] = cell
                output.append(event)

        splunk.Intersplunk.outputResults(output)

    #delete temp files
    finally:
        if input_csv_filename:
            os.remove(input_csv_filename)
        if output_csv_filename:
            os.remove(output_csv_filename)
        if script_filename:
            os.remove(script_filename)

except errors.Error as e:
    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e)))

except Exception as e:
    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))
