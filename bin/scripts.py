import path
import os
import base64
import config

script_stanza_prefix = 'script://'
custom_scripts_path = path.get_named_path('scripts')


def refresh_files():

    if not os.path.exists(custom_scripts_path):
        os.makedirs(custom_scripts_path)

    for stanza_name in config.r_config:
        if stanza_name.startswith(script_stanza_prefix):
            script_stanza = config.r_config[stanza_name]
            script_content = base64.decodestring(script_stanza['content'])
            script_filename = stanza_name[len(script_stanza_prefix):] + '.r'
            script_full_path = os.path.join(custom_scripts_path, script_filename)
            with open(script_full_path, 'wb') as f:
                f.write(script_content)
