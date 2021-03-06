import logging
from datetime import timedelta
from datetime import datetime
import time
from boto import ec2
from boto.ec2 import cloudwatch
from errors import ScaleError, InstanceLaunchTimeOut, SpotRequestTimeOut
from providers import Providers


class AWS(Providers):
    def __init__(self, access_key_id, secret_access_key, region_name):
        self._ec2_conn = ec2.connect_to_region(region_name,
                                            aws_access_key_id=access_key_id,
                                    aws_secret_access_key=secret_access_key)
        logging.info('Initialized aws connection to %s' % region_name)

        self._cloudwatch_conn = cloudwatch.connect_to_region(region_name,
                                            aws_access_key_id=access_key_id,
                                    aws_secret_access_key=secret_access_key)
        logging.info('Initialized cloud watch connection to %s' % region_name)

        self._region_name = region_name

    def get_connection(self):
        return self._ec2_conn

    def get_cloudwatch_connection(self):
        return self._cloudwatch_conn

    def get_instances(self, security_group=None):
        conn = self.get_connection()
        reservations = conn.get_all_instances()
        instances = [inst for resv in reservations
                              for inst in resv.instances
                                  if inst.state == 'running']
        logging.info('Found %s running instances' % len(instances))
        if security_group is not None:
            logging.info('looking for instances in sg:%s...' % security_group)
            instances_in_security_group = []
            for inst in instances:
                groups = []
                for group in inst.groups:
                    groups.append(group.name)
                if security_group in groups:
                    instances_in_security_group.append(inst)
        logging.info('Found %s instances' % len(instances_in_security_group))
        return instances_in_security_group

    def get_instance_by_id(self, id):
        conn = self.get_connection()
        reservations = conn.get_all_instances([id])
        for resv in reservations:
            for instance in resv.instances:
                return instance

    def wait_for_run(self, instance, timeout=60, interval=5):
        trial = timeout / interval
        logging.info('Waiting for instance to launch...')
        for _ in xrange(trial):
            instance.update()
            logging.info('Checking... Current State: %s', instance.state)
            if instance.state == 'running':
                logging.info('Instance running')
                break
            time.sleep(interval)
        else:
            logging.error('Cancelling launch due to time out.')
            instance.terminate()
            raise InstanceLaunchTimeOut()
        return instance

    def launch_instance(self, instance_properties):
        conn = self.get_connection()
        resv = conn.run_instances(
                        instance_properties.ami,
                        instance_type=instance_properties.type,
                        security_groups=[instance_properties.security_group],
                        placement=instance_properties.availability_zone,
                        key_name=instance_properties.key_pair_name)
        for instance in resv.instances:
            self.wait_for_run(instance)
            conn.create_tags([instance.id],
                             {'Name': 'auto-' + str(datetime.now())})
            instance.update()
            return instance

    def get_spot_request_by_id(self, id):
        conn = self.get_connection()
        requests = conn.get_all_spot_instance_requests([id])
        for request in requests:
            return request

    def spot_price(self, instance_properties, hours=6):
        conn = self.get_connection()
        prices = conn.get_spot_price_history(
                    start_time=(datetime.utcnow() -
                                timedelta(hours=hours)).isoformat(),
                    end_time=datetime.utcnow().isoformat(),
                    instance_type=instance_properties.type,
                    product_description='Linux/UNIX',
                    availability_zone=instance_properties.availability_zone)
        spot_price = sum(price.price for price in prices) / len(prices)
        logging.info('Spot price seems to be: %s' % spot_price)
        return spot_price

    def wait_for_fulfill(self, request, timeout=3000, interval=15):
        trial = timeout / interval
        logging.info('Waiting for request to complete...')
        for _ in xrange(trial):
            request = self.get_spot_request_by_id(request.id)
            logging.info('Checking... Current State: %s', request.state)
            if request.state == 'active':
                logging.info('Spot request active')
                break
            time.sleep(interval)
        else:
            logging.error('Cancelling spot request due to time out.')
            request.cancel()
            raise SpotRequestTimeOut()
        return request

    def launch_spot_instance(self, instance_properties):
        conn = self.get_connection()
        price = self.spot_price(instance_properties) * 3
        logging.info('Requesting spot instance with bid %s ' % price)
        requests = conn.request_spot_instances(
                    price=price,
                    image_id=instance_properties.ami,
                    count=1,
                    instance_type=instance_properties.type,
                    security_groups=[instance_properties.security_group],
                    placement=instance_properties.availability_zone,
                    key_name=instance_properties.key_pair_name)
        for request in requests:
            request = self.wait_for_fulfill(request)
            instance = self.get_instance_by_id(request.instance_id)
            self.wait_for_run(instance)
            conn.create_tags([instance.id],
                             {'Name': 'auto-' + str(datetime.now())})
            instance.update()
            return instance

    def cpu_utilization(self, instances, minutes=10):
        logging.info('In cpu_utilization()')
        logging.info('Getting cloudwatch connection')
        conn = self.get_cloudwatch_connection()
        stat_sum = 0.0
        logging.info('Getting CPU Utilization for instances in list')
        for instance in instances:
            stats = conn.get_metric_statistics(
                        period=60,
                        start_time=datetime.utcnow() -
                        timedelta(minutes=minutes + 5),
                        end_time=datetime.utcnow(),
                        metric_name='CPUUtilization',
                        namespace='AWS/EC2',
                        statistics=['Average'],
                        dimensions={'InstanceId': instance.id})
            if stats:
                stat_sum += sum(stat['Average'] for stat in stats) / len(stats)
            else:
                raise ScaleError('Stat seems empty.')
        try:
            avg_cluster_utilization = stat_sum / len(instances)
        except ZeroDivisionError:
            raise ScaleError('Cluster has no nodes')
        logging.info('Avg cluster utilization is %s' % avg_cluster_utilization)
        return avg_cluster_utilization