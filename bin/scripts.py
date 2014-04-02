import path
import os
import base64
import config
import calendar
import datetime
import lockfile

scheme = 'script'
extension = 'r'


def get_custom_scripts_path():
    return path.get_named_path('scripts')


def create_custom_scripts_path():
    custom_scripts_path = get_custom_scripts_path()
    if not os.path.exists(custom_scripts_path):
        os.makedirs(custom_scripts_path)


def create_files(service):
    lock_file_path = path.get_named_path('scripts.lock')
    with lockfile.file_lock(lock_file_path):

        create_custom_scripts_path()
        custom_scripts_path = get_custom_scripts_path()

        filenames = set()

        # check configuration for requred scripts
        for stanza, name in config.iter_stanzas(service, scheme):
            filename = name + os.path.extsep + extension
            full_path = os.path.join(custom_scripts_path, filename)

            if os.path.exists(full_path):
                os.remove(full_path)
                create_file = True
                # TODO: compare file creation date with stanza creation date
            else:
                create_file = True

            if create_file:
                script_content = base64.decodestring(stanza.__getattr__('content'))
                with open(full_path, 'wb') as f:
                    f.write(script_content)

            filenames.add(filename)

        # remove files that are no longer in the list of configures scripts
        for filename in os.listdir(custom_scripts_path):
            if filename.endswith(os.path.extsep + extension):
                if not filename in filenames:
                    script_path = os.path.join(custom_scripts_path, filename)
                    os.remove(script_path)


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def get(service, script_name):
    for stanza, name in config.iter_stanzas(service, scheme):
        if name == script_name:
            return {
                'content': base64.decodestring(stanza.__getattr__('content')),
                'is_removable': stanza.access['removable'] == '1',
            }
    return None


def add(service, name, content):
    config.create_stanza(service, scheme, name, {
        'content': base64.encodestring(content).replace('\n', ''),
        'uploaded': calendar.timegm(datetime.datetime.now().utctimetuple())
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)