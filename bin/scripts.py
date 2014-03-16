import path
import os
import base64
import config

scheme = 'script'
custom_scripts_path = path.get_named_path('scripts')
extension = 'r'

def refresh_files():

    if not os.path.exists(custom_scripts_path):
        os.makedirs(custom_scripts_path)

    filenames = set()

    # check configuration for requred scripts
    for stanza, name in config.iter_stanzas(scheme):
        filename = name + os.path.extsep + extension
        full_path = os.path.join(custom_scripts_path, filename)

        if os.path.exists(full_path):
            os.remove(full_path)
            create_file = True
            # TODO: compare file creation date with stanza creation date
        else:
            create_file = True

        if create_file:
            script_content = base64.decodestring(stanza['content'])
            with open(full_path, 'wb') as f:
                f.write(script_content)

        filenames.add(filename)

    # remove files that are no longer in the list of configures scripts
    for filename in os.listdir(custom_scripts_path):
        if filename.endswith(os.path.extsep + extension):
            if not filename in filenames:
                path = os.path.join(custom_scripts_path, filename)
                os.remove(path)