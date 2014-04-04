import splunk.Intersplunk
import traceback
import sys
import csv
import os

try:

    (isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)
    if isgetinfo:
        splunk.Intersplunk.outputInfo(False, True, False, False, None, True)

    dirname, filename = os.path.split(os.path.abspath(__file__))
    csv_path = os.path.join(dirname, 'baby_names.csv')

    output = []
    with open(csv_path, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            output.append(row)

    splunk.Intersplunk.outputResults(output, fields=['Year', 'First Name', 'County', 'Sex', 'Count'])

except Exception as e:
    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))
