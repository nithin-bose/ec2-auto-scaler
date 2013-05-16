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
        self.check_func = None
        self.health_check_url = None
        try:
            if len(cluster['health_check_url']) > 0:
                self.health_check_url = cluster['health_check_url']
        except:
            self.health_check_url = None

        self.instance_properties = Collection()
        self.instance_properties.ami = cluster['ami']
        self.instance_properties.type = cluster['node_type']

    def start(self):
        while True:
            if self.check_func is not None:
                self._action(self.check_func)
            else:
                self._action(self._check_cpu_utilization())
            instances = self.provider.get_instances(self.security_group)
            self.load_balancer.setInstances(instances)
            self.load_balancer.reloadConfiguration()
            self._healthCheck()
            time.sleep(self.cooltime * 60)

    def _check_cpu_utilization(self):
        instances = self.provider.get_instances(self.security_group)
        instanceCount = len(instances)
        try:
            value = self.provider.cpu_utilization(instances)
        except ScaleError:
            return State.NORMAL
        if self.min_nodes > instanceCount:
            return State.SCALE_OUT
        elif value > self.scale_out_threshold:
            if self.max_nodes <= instanceCount:
                return State.MAX_LIMIT
            return State.SCALE_OUT
        elif value < self.scale_out_threshold * self.scale_down_ratio:
            if self.min_nodes >= instanceCount:
                return State.MIN_LIMIT
            return State.SCALE_DOWN
        return State.NORMAL

    def _action(self, state):
        if state == State.SCALE_OUT:
            if self.node_option == 'on-demand':
                self.provider.launch_instance(self.instance_properties)
            elif self.node_option == 'spot':
                self.provider.launch_spot_instance(self.instance_properties)
            else:
                raise InvalidPricingOption(self.node_option)
        elif state == State.SCALE_DOWN:
            if self.node_option == 'on-demand':
                for instance in self.provider.get_instances(
                                                        self.security_group):
                    try:
                        instance.terminate()
                    except:
                        continue
                    else:
                        break
                else:
                    raise InstanceTerminationFailed()
            elif self.node_option == 'spot':
                for instance in self.provider.get_instances(
                                                        self.security_group):
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
            else:
                raise InvalidPricingOption(self.node_option)
        elif state == State.MAX_LIMIT:
            pass
        elif state == State.MIN_LIMIT:
            pass
        elif state == State.NORMAL:
            pass
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