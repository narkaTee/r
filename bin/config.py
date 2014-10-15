
_r_path = None
_r_config_file = None

ignore_cache = True


def get_r_config_file(service):
    if not ignore_cache:
        global _r_config_file
        if _r_config_file:
            return _r_config_file
    _r_config_file = service.confs['r']#.create('r')
    return _r_config_file


def get_r_path(service):
    if not ignore_cache:
        global _r_path
        if _r_path:
            return _r_path
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name == 'paths':
            _r_path = getattr(stanza, 'r')
            return _r_path
    raise Exception('missing r path argument')


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
