import path
import os
from splunk.clilib import cli_common as cli
import base64

script_stanza_prefix = 'script://'
custom_scripts_path = path.get_named_path('scripts')

#read configuration file
cli.cacheConfFile('r')
r_config = cli.confSettings['r']


def refresh_files():

    if not os.path.exists(custom_scripts_path):
        os.makedirs(custom_scripts_path)

    for stanza_name in r_config:
        if stanza_name.startswith(script_stanza_prefix):
            script_stanza = r_config[stanza_name]
            script_content = base64.decodestring(script_stanza['content'])
            script_filename = stanza_name[len(script_stanza_prefix):] + '.r'
            script_full_path = os.path.join(custom_scripts_path, script_filename)
            with open(script_full_path, 'wb') as f:
                f.write(script_content)
