import traceback
import sys
import errors
import config
import uuid
import packages
import index_logging


def log(fields):
    index_logging.log(__file__, fields)


def r_stats(service):

    stats_id = str(uuid.uuid1())

    number_of_packages = 0
    for _, package_name in config.iter_stanzas(service, packages.scheme):
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