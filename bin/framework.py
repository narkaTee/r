import os
from splunk.clilib import cli_common as cli

#read configuration file
cli.cacheConfFile('r')
r_config = cli.confSettings['r']

#check if the R library presence
r_path_config = r_config['paths']
r_path = r_path_config.get('r')

def is_installed():
    return os.path.exists(r_path)