import path
import os
import base64
import config

scheme = 'script'
custom_scripts_path = path.get_named_path('scripts')


def refresh_files():

    if not os.path.exists(custom_scripts_path):
        os.makedirs(custom_scripts_path)

    for stanza, name in config.iter_stanzas(scheme):
        script_content = base64.decodestring(stanza['content'])
        script_filename = name + '.r'
        script_full_path = os.path.join(custom_scripts_path, script_filename)
        with open(script_full_path, 'wb') as f:
            f.write(script_content)
