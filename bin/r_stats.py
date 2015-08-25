import traceback
import sys
import r_errors
import r_config
import uuid
import r_packages
import r_index_logging


def log(fields):
    r_index_logging.log(__file__, fields)


def r_stats(service):

    stats_id = str(uuid.uuid1())

    number_of_packages = 0
    for _, package_name in r_config.iter_stanzas(service, r_packages.scheme):
        log({
            'stats_id': stats_id,
            'stats_package_name': package_name,
            })
        number_of_packages += 1

    log({
        'stats_id': stats_id,
        'stats_number_of_packages': number_of_packages,
        })


def main():
    from splunklib.searchcommands import csv as splunkcsv

    del splunkcsv

    import splunk.Intersplunk

    from r_utils import get_service

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
        if len(sys.argv) != 1:
            raise Exception("No parameter allowed")

        # read header, fieldnames, and events from input stream
        settings = {}
        splunk.Intersplunk.readResults(sys.stdin, settings)

        # connect to splunk using SDK
        service = get_service(settings['infoPath'])

        r_stats(service)
        splunk.Intersplunk.outputResults([])

    except r_errors.Error as e:
        splunk.Intersplunk.outputResults(splunk.Intersplunk.generateErrorResults(str(e)))

    except Exception as e:
        splunk.Intersplunk.outputResults(
            splunk.Intersplunk.generateErrorResults(str(e) + ": " + traceback.format_exc()))


if __name__ == '__main__':
    main()