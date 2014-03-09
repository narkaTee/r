import splunk.Intersplunk
import traceback
import sys

try:

    (isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)
    if isgetinfo:
        splunk.Intersplunk.outputInfo(False, True, False, False, None, True)

    output = [
        {
            'Customer': 'Robert',
            'Product': 'Mercedes',
            'Category': 'Clothing'
        },
        {
            'Customer': 'Robert',
            'Product': 'Bobby Car',
            'Category': 'Vehicle'
        },
        {
            'Customer': 'Robert',
            'Product': 'Bobby Car',
            'Category': 'Vehicle'
        },
        {
            'Customer': 'Olivier',
            'Product': 'Hat',
            'Category': 'Clothing'
        },
        {
            'Customer': 'Olivier',
            'Product': 'Racing Bicycle',
            'Category': 'Vehicle'
        },
        {
            'Customer': 'Olivier',
            'Product': 'Audi',
            'Category': 'Vehicle'
        },
        {
            'Customer': 'Markus',
            'Product': 'Mercedes',
            'Category': 'Vehicle'
        },
    ]

    splunk.Intersplunk.outputResults(output)

except Exception as e:
    splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))
