from xml.etree import ElementTree
import sys
from splunklib.searchcommands import csv as splunkcsv
del splunkcsv
import csv
from urlparse import urlsplit
from splunklib.client import Service

_search_results_info = None
_service = None


def get_search_results_info(search_results_info_path):
    global _search_results_info
    if _search_results_info:
        return _search_results_info

    info_path = search_results_info_path

    def convert_field(field):
        return (field[1:] if field[0] == '_' else field).replace('.', '_')

    def convert_value(field, value):
        if field == 'countMap':
            split = value.split(';')
            value = dict((key, int(value))
                         for key, value in zip(split[0::2], split[1::2]))
        elif field == 'vix_families':
            value = ElementTree.fromstring(value)
        elif value == '':
            value = None
        else:
            try:
                value = float(value)
                if value.is_integer():
                    value = int(value)
            except ValueError:
                pass
        return value

    with open(info_path, 'rb') as f:
        from collections import namedtuple
        reader = csv.reader(f, dialect='splunklib.searchcommands')
        fields = [convert_field(x) for x in reader.next()]
        values = [convert_value(f, v) for f, v in zip(fields, reader.next())]

    search_results_info_type = namedtuple("SearchResultsInfo", fields)
    _search_results_info = search_results_info_type._make(values)
    return _search_results_info


def get_service(search_results_info_path):
    global _service
    if _service:
        return _service

    search_results_info = get_search_results_info(search_results_info_path)

    _, netloc, _, _, _ = urlsplit(
        search_results_info.splunkd_uri,
        search_results_info.splunkd_protocol,
        allow_fragments=False
    )
    splunkd_host, _ = netloc.split(':')
    _service = Service(
        scheme=search_results_info.splunkd_protocol,
        host=splunkd_host,
        port=search_results_info.splunkd_port,
        token=search_results_info.auth_token,
        app=search_results_info.ppc_app
    )
    return _service


def read_fieldnames_from_command_input(input_buf, has_command_header=True):
    if has_command_header:
        while True:
            line = input_buf.readline()
            line = line[:-1]
            if len(line) == 0:
                break

    csvr = csv.reader(input_buf)
    fieldnames = []
    for line in csvr:
        fieldnames = line
        break
    return fieldnames


def output_info(streaming, generating, retevs, reqsop, preop, timeorder=False, clear_req_fields=False, req_fields=None):
    import splunk.Intersplunk

    infodict = {
        'streaming_preop': preop,
        'streaming': '0',
        'generating': '0',
        'retainsevents': '0',
        'requires_preop': '0',
        'generates_timeorder': '0',
        'overrides_timeorder': '1',
        'clear_required_fields': '0'
    }

    if streaming:
        infodict['streaming'] = '1'

    if generating:
        infodict['generating'] = '1'
        if timeorder:
            infodict['generates_timeorder'] = '1'
    else:
        if timeorder:
            infodict['overrides_timeorder'] = '0'

    if retevs:
        infodict['retainsevents'] = '1'

    if reqsop:
        infodict['requires_preop'] = '1'

    if clear_req_fields:
        infodict['clear_required_fields'] = '1'

    if req_fields is not None and len(req_fields) > 0:
        infodict['required_fields'] = req_fields

    infodict['supports_multivalues'] = '1'

    splunk.Intersplunk.outputResults([infodict], mvdelim=',')
    sys.exit()
