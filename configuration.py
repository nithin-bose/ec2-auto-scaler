import ConfigParser
#from errors import ConfigFileError
from constants import NON_CLUSTER_SECTIONS
from providers.aws import AWS
from loadbalancers.HAProxy import HAProxy
from errors import UnknownProviderError, UnknownLoadBalancerError


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

    def _get_provider(self, cluster):
        if self.parsed_config['main']['provider'] == 'aws':
            aws_access_key_id = self.parsed_config['aws']['access_key_id']
            secret_access_key = self.parsed_config['aws']['secret_access_key']
            region_name = cluster['region_name']
            provider = AWS(aws_access_key_id, secret_access_key, region_name)
        else:
            raise UnknownProviderError()
        return provider

    def _get_load_balancer(self):
        if self.parsed_config['main']['load_balancer'] == 'haproxy':
            try:
                executable = self.parsed_config['haproxy']['executable']
            except:
                executable = None

            try:
                pid_file = self.parsed_config['haproxy']['pid_file']
            except:
                pid_file = None

            try:
                config_file = self.parsed_config['haproxy']['config_file']
            except:
                config_file = None

            try:
                config_tpl = self.parsed_config['haproxy']['config_tpl']
            except:
                config_tpl = None

            load_balancer = HAProxy(config_tpl, config_file, pid_file,
                                                                    executable)
        else:
            raise UnknownLoadBalancerError()
        return load_balancer

    def get_cluster_details(self):
        clusters = []
        load_balancer = self._get_load_balancer()
        for index, cluster in self.parsed_config.iteritems():
            if index not in NON_CLUSTER_SECTIONS:
                cluster['provider'] = self._get_provider(cluster)
                cluster['load_balancer'] = load_balancer
                clusters.append(cluster)

        return clusters
