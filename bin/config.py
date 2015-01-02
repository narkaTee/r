
def get_r_config_file(service):
    _r_config_file = service.confs['r']  # .create('r')
    return _r_config_file


def get_r_path(service):
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name == 'paths':
            _r_path = getattr(stanza, 'r')
            return _r_path
    raise Exception('missing r path argument')


def get_r_csv_read_options(service):
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name == 'csv':
            return getattr(stanza, 'read-options')
    raise Exception('missing csv read-options')


def get_r_csv_write_options(service):
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name == 'csv':
            return getattr(stanza, 'write-options')
    raise Exception('missing csv write-options')


def iter_stanzas(service, scheme):
    prefix = '%s://' % scheme
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name.startswith(prefix):
            after_prefix = stanza.name[len(prefix):]
            yield stanza, after_prefix


def create_stanza(service, scheme, name, attr):
    r_config_file = get_r_config_file(service)
    fullname = '%s://%s' % (scheme, name)
    for stanza in r_config_file.list():
        if stanza.name == fullname:
            stanza.delete()
    script_stanza = r_config_file.create(fullname)
    script_stanza.submit(attr)
    return script_stanza


def delete_stanza(service, scheme, name):
    r_config_file = get_r_config_file(service)
    fullname = '%s://%s' % (scheme, name)
    for stanza in r_config_file.list():
        if stanza.name == fullname:
            stanza.delete()
