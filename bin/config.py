from splunk.clilib import cli_common as cli

cli.cacheConfFile('r')

r_config = cli.confSettings['r']