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
        self.scale_out_threshold = float(cluster['scale_out_threshold'])
        self.scale_down_ratio = float(cluster['scale_down_ratio'])
        self.node_option = cluster['node_option']
        self.min_nodes = float(cluster['min_nodes'])
        self.max_nodes = float(cluster['max_nodes'])
        self.security_group = cluster['security_group']
        self.provider = config_details['provider']
        self.load_balancer = config_details['load_balancer']
        self.instances = None
        self.health_check_url = None
        try:
            if len(cluster['health_check_url']) > 0:
                self.health_check_url = cluster['health_check_url']
        except:
            self.health_check_url = None

        self.instance_properties = Collection()
        self.instance_properties.ami = cluster['ami']
        self.instance_properties.type = cluster['node_type']
        self.instance_properties.key_pair_name = cluster['node_key_pair_name']
        self.instance_properties.security_group = self.security_group
        self.instance_properties.availability_zone = \
                                                cluster['availability_zone']

    def run(self):
        logging.info('In run()')
        logging.info('Checking to scale...')
        self._action(self._check_cpu_utilization())
        logging.info('Modifying load balancer...')
        instances = self._get_instances()
        instanceCount = len(instances)
        logging.info('%s instances: %s' % (self.security_group, instanceCount))
        self.load_balancer.setInstances(instances)
        self.load_balancer.reloadConfiguration()
        logging.info('Starting health check...')
        self._healthCheck()
        logging.info('Scaling complete')

    def _get_instances(self):
        logging.info('Getting instance list...')
        if self.instances is None:
            logging.info('Instances list seems to have changed. Refreshing...')
            self.instances = self.provider.get_instances(self.security_group)
            logging.info('Instances list refreshed')
        return self.instances

    def _check_cpu_utilization(self):
        logging.info('In _check_cpu_utilization()')
        instances = self._get_instances()
        instanceCount = len(instances)
        cpu_utilization = 0
        try:
            cpu_utilization = self.provider.cpu_utilization(instances)
        except ScaleError:
            cluster_state = State.NORMAL

        logging.info('Computing cluster state..')
        if self.min_nodes > instanceCount:
            logging.info('min_nodes(%s) > instanceCount(%s)' %
                                            (self.min_nodes, instanceCount))
            cluster_state = State.SCALE_OUT
        elif cpu_utilization > self.scale_out_threshold:
            logging.info('cpu_utilization(%s) > scale_out_threshold(%s)' %
                                (cpu_utilization, self.scale_out_threshold))
            if self.max_nodes <= instanceCount:
                logging.info('max_nodes(%s) <= instanceCount(%s)' %
                                            (self.max_nodes, instanceCount))
                cluster_state = State.MAX_LIMIT
            else:
                logging.info('max_nodes(%s) > instanceCount(%s)' %
                                            (self.max_nodes, instanceCount))
                cluster_state = State.SCALE_OUT
        elif cpu_utilization < self.scale_out_threshold * self.scale_down_ratio:
            logging.info('cpu_util(%s) < scle_ot_thrshld(%s)*scle_dwn_rtio(%s)'
          % (cpu_utilization, self.scale_out_threshold, self.scale_down_ratio))
            if self.min_nodes >= instanceCount:
                logging.info('min_nodes(%s) >= instanceCount(%s)' %
                                            (self.min_nodes, instanceCount))
                cluster_state = State.MIN_LIMIT
            else:
                logging.info('min_nodes(%s) < instanceCount(%s)' %
                                            (self.min_nodes, instanceCount))
                cluster_state = State.SCALE_DOWN

        logging.info('Cluster state is %s' % cluster_state)
        return cluster_state

    def _action(self, state):
        logging.info('Modifying cluster..')
        if state == State.SCALE_OUT:
            self.instances = None
            logging.info('Scaling out the cluster.')
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
            self.instances = None
            logging.info('Scaling down the cluster.')
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
                for instance in self._get_instances():
                    try:
                        if instance.spot_instance_request_id is not None:
                            logging.info('Cancelling spot request...')
                            spot_request_id = instance.spot_instance_request_id
                            self.provider.get_spot_request_by_id(
                                                     spot_request_id).cancel()
                        logging.info('Terminating spot instance...')
                        instance.terminate()
                        instance.update()
                    except:
                        logging.info('Exception. Will remove another instance')
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
        else:
            logging.info('Health check URL not specified. Skipping')