import ConfigParser
#from errors import ConfigFileError
from constants import NON_CLUSTER_SECTIONS
from providers.aws import AWS
from loadbalancers.HAProxy import HAProxy


class Configuration():

    def __init__(self, path):
        self.config_path = path
        self._load_config()
        self._check_config()

    def _load_config(self):
        Config = ConfigParser.ConfigParser()
        Config.read(self.config_path)
        config = {}
        for section in Config.sections():
            config[section] = {}
            for option in Config.options(section):
                config[section][option] = Config.get(section, option)
        self.parsed_config = config

    def _check_config(self):
        pass
        #if self.parsed_config['master']['az'] != \
                                        #self.parsed_config['worker']['az']:
            #raise ConfigFileError

    def get_config_details(self):
        config_details = {}
        clusters = []
        for index, cluster in self.parsed_config:
            if index not in NON_CLUSTER_SECTIONS:
                clusters.append(cluster)
                region_name = cluster['region_name']
                break

        config_details['clusters'] = clusters

        if self.parsed_config['main']['provider'] == 'aws':
            aws_access_key_id = self.parsed_config['aws']['access_key_id']
            secret_access_key = self.parsed_config['aws']['secret_access_key']
            config_details['provider'] = AWS(aws_access_key_id,
                                                secret_access_key, region_name)

        if self.parsed_config['main']['load_balancer'] == 'haproxy':
            config_details['load_balancer'] = HAProxy()
        return config_details
