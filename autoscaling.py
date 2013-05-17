import time
import logging
import urllib2
from errors import ScaleError, InvalidPricingOption, \
InstanceTerminationFailed, InvalidStateError


class State(object):
    SCALE_OUT = 'SHOULD SCALE OUT'
    SCALE_DOWN = 'SHOULD SCALE DOWN'
    MAX_LIMIT = 'MAX LIMIT REACHED'
    MIN_LIMIT = 'MIN LIMIT REACHED'
    NORMAL = 'NORMAL'


class Collection():
    pass


class AutoScale():
    def __init__(self, cluster, config_details):
        self.scale_out_threshold = cluster['scale_out_threshold']
        self.scale_down_ratio = cluster['scale_down_ratio']
        self.node_option = cluster['node_option']
        self.min_nodes = cluster['min_nodes']
        self.max_nodes = cluster['max_nodes']
        self.cooltime = cluster['cooltime']
        self.security_group = cluster['security_group']
        self.provider = config_details['provider']
        self.load_balancer = config_details['load_balancer']
        self.health_check_url = None
        try:
            if len(cluster['health_check_url']) > 0:
                self.health_check_url = cluster['health_check_url']
        except:
            self.health_check_url = None

        self.instance_properties = Collection()
        self.instance_properties.ami = cluster['ami']
        self.instance_properties.type = cluster['node_type']

    def run(self):
        logging.info('In run()')
        while True:
            logging.info('Checking to scale...')
            self._action(self._check_cpu_utilization())
            logging.info('Modifying load balancer...')
            instances = self._get_instances()
            self.load_balancer.setInstances(instances)
            self.load_balancer.reloadConfiguration()
            logging.info('Starting health check...')
            self._healthCheck()
            logging.info('Waiting until next scale check..')
            time.sleep(self.cooltime * 60)

    def _get_instances(self):
        if self.instances is None:
            self.instances = self.provider.get_instances(self.security_group)
        return self.instances

    def _check_cpu_utilization(self):
        logging.info('In _check_cpu_utilization()')
        logging.info('Getting instance list for %s' % self.security_group)
        instances = self._get_instances()
        instanceCount = len(instances)
        logging.info('Got %s instances in list' % instanceCount)
        try:
            value = self.provider.cpu_utilization(instances)
        except ScaleError:
            cluster_state = State.NORMAL

        logging.info('Computing cluster state..')
        if self.min_nodes > instanceCount:
            cluster_state = State.SCALE_OUT
        elif value > self.scale_out_threshold:
            if self.max_nodes <= instanceCount:
                cluster_state = State.MAX_LIMIT
            else:
                cluster_state = State.SCALE_OUT
        elif value < self.scale_out_threshold * self.scale_down_ratio:
            if self.min_nodes >= instanceCount:
                cluster_state = State.MIN_LIMIT
            else:
                cluster_state = State.SCALE_DOWN

        logging.info('Cluster state is %s' % cluster_state)
        return cluster_state

    def _action(self, state):
        if state == State.SCALE_OUT:
            logging.info('Modifying cluster..')
            if self.node_option == 'on-demand':
                logging.info('Creating on-demand instance...')
                self.provider.launch_instance(self.instance_properties)
                logging.info('Done')
            elif self.node_option == 'spot':
                logging.info('Creating spot instance..')
                self.provider.launch_spot_instance(self.instance_properties)
                logging.info('Done')
            else:
                raise InvalidPricingOption(self.node_option)
        elif state == State.SCALE_DOWN:
            logging.info('Scaling out cluster.')
            if self.node_option == 'on-demand':
                logging.info('Removing on-demand instance...')
                for instance in self._get_instances():
                    try:
                        instance.terminate()
                    except:
                        continue
                    else:
                        break
                else:
                    raise InstanceTerminationFailed()
                logging.info('Done')
            elif self.node_option == 'spot':
                logging.info('Removing spot instance...')
                for instance in self._get_instances():
                    try:
                        instance.terminate()
                        if instance.spot_instance_request_id is not None:
                            spot_request_id = instance.spot_instance_request_id
                            self.provider.get_spot_request_by_id(
                                                     spot_request_id).cancel()
                        instance.update()
                    except:
                        continue
                    else:
                        break
                else:
                    raise InstanceTerminationFailed()
                logging.info('Done')
            else:
                raise InvalidPricingOption(self.node_option)
        elif state == State.MAX_LIMIT:
            logging.info('Nothing to do.')
        elif state == State.MIN_LIMIT:
            logging.info('Nothing to do.')
        elif state == State.NORMAL:
            logging.info('Nothing to do.')
        else:
            raise InvalidStateError(state)

    def _healthCheck(self):
        # Do a health check on the url if specified.
        if self.health_check_url:
            logging.info('Performing health check.')
            try:
                logging.info('Checking %s' % self.health_check_url)
                response = urllib2.urlopen(self.health_check_url)
                logging.info('Response: %s' % response.read())
            except:
                # Assign the EIP to self.
                logging.warn('Health check failed.')
                print("Health check failed!!")
        else:
            logging.info('Health check URL not specified. Skipping')