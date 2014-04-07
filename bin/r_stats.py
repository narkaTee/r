import traceback
import sys
import errors
import config
import uuid
import packages


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


def r_stats(service):

    stats_id = str(uuid.uuid1())

    log(service, {
        'stats_id': stats_id,
        'stats_action': 'pre',
        })

    number_of_packages = 0
    for _, package_name in config.iter_stanzas(service, packages.scheme):
        log(service, {
            'stats_id': stats_id,
            'stats_action': 'stats_packages_package',
            'stats_package_name': package_name,
            })
        number_of_packages += 1

    log(service, {
        'stats_id': stats_id,
        'stats_action': 'stats_packages_summary',
        'stats_number_of_packages': number_of_packages,
        })


def main():
    from splunklib.searchcommands import csv as splunkcsv

    del splunkcsv

    import splunk.Intersplunk

    from utils import get_service

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
        if len(sys.argv) != 1:
            raise Exception("No parameter allowed")

        # read header, fieldnames, and events from input stream
        settings = {}
        splunk.Intersplunk.readResults(sys.stdin, settings)

        #connect to splunk using SDK
        service = get_service(settings['infoPath'])

        r_stats(service)
        splunk.Intersplunk.outputResults([])

    except errors.Error as e:
        splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e)))

    except Exception as e:
        splunk.Intersplunk.outputResults(
            splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))


if __name__ == '__main__':
    main()