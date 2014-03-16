from splunk.clilib import cli_common as cli

cli.cacheConfFile('r')

r_config = cli.confSettings['r']


def get_r_path():
    path_config = r_config['paths']
    r_path = path_config.get('r')
    return r_path


def iter_stanzas(scheme):
    prefix = '%s://' % scheme
    for stanza_name in r_config:
        if stanza_name.startswith(prefix):
            stanza = r_config[stanza_name]
            after_prefix = stanza_name[len(prefix):]
            yield stanza, after_prefix