import splunk.rest
import splunk.bundle as bundle
import splunk.auth as auth
import scripts as scripts_lib


class ScriptsHandler(splunk.rest.BaseRestHandler):

    def handle_GET(self):
        entries = {}

        r_conf = bundle.getConf("r", self.sessionKey, namespace='r', owner=self.request['userId'])
        scripts = r_conf.findStanzas(scripts_lib.scheme+"*")

        for name, script in scripts.iteritems():
            name = name[len(scripts_lib.scheme)+3:]
            entries[name] = {
                "name": name+'.r',
                'is_removable': '0',  # stanza.access['removable'] == '1',
                'owner': self.request['userName']  # stanza.access['owner'],
            }
        return entries