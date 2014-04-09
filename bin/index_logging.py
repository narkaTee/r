

def log(service, source, fields):
    r_index = service.indexes["r"]
    args = {
        'index': r_index.name,
        'source': source,
        'sourcetype': 'r'
    }
    body = ''
    for k in fields:
        v = fields[k]
        if isinstance(v, list) or isinstance(v, set):
            body += ', '.join(['%s=\"%s\" ' % (k, f) for f in v])
        else:
            body += '%s=\"%s\" ' % (k, v)
    r_index.service.post(
        '/services/receivers/simple',
        body=body,
        **args)