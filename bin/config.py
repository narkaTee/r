
_r_path = None
_r_config_file = None


def get_r_path(service):
    global _r_path
    if _r_path:
        return _r_path
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name == 'paths':
            _r_path = stanza.__getattr__('r')
            return _r_path
    raise Exception('missing r path argument')


def get_r_config_file(service):
    global _r_config_file
    if _r_config_file:
        return _r_config_file
    _r_config_file = service.confs.create('r')
    return _r_config_file


def iter_stanzas(service, scheme):
    prefix = '%s://' % scheme
    r_config_file = get_r_config_file(service)
    for stanza in r_config_file.list():
        if stanza.name.startswith(prefix):
            after_prefix = stanza.name[len(prefix):]
            yield stanza, after_prefix