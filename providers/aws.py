import logging
from datetime import timedelta
from datetime import datetime
from boto import ec2
from boto.ec2 import cloudwatch
from errors import ScaleError
import Providers


class AWS(Providers):
    def __init__(self, access_key_id, secret_access_key, region_name):
        self._ec2_conn = ec2.connect_to_region(region_name,
                                            aws_access_key_id=access_key_id,
                                    aws_secret_access_key=secret_access_key)

        self._cloudwatch_conn = cloudwatch.connect_to_region(region_name,
                                            aws_access_key_id=access_key_id,
                                    aws_secret_access_key=secret_access_key)
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
        if security_group is not None:
            instances_in_security_group = []
            for inst in instances:
                groups = []
                for group in inst.groups:
                    groups.append(group)
                if security_group in groups:
                    instances_in_security_group.append(inst)
        return instances_in_security_group

    def get_instance_by_id(self, id):
        conn = self.get_connection()
        reservations = conn.get_all_instances([id])
        for resv in reservations:
            for instance in resv.instances:
                return instance

    def wait_for_run(self, instance, timeout=60, interval=5):
        trial = timeout / interval
        for _ in xrange(trial):
            instance.update()
            if instance.state == 'running':
                break
        else:
            instance.terminate()
            raise ScaleError('Timed out. Cannot launch instance.')
        return instance

    def launch_instance(self, instance_properties):
        conn = self.get_connection()
        resv = conn.run_instances(instance_properties.ami,
                                  instance_type=instance_properties.type,
                                  placement=self._region_name)
        for instance in resv.instances:
            self.wait_for_run(instance)
            conn.create_tags([instance.id],
                             {'Name': instance_properties.name})
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
                    availability_zone=self._region_name)
        return sum(price.price for price in prices) / len(prices)

    def wait_for_fulfill(self, request, timeout=300, interval=15):
        trial = timeout / interval
        for _ in xrange(trial):
            request = self.get_spot_request_by_id(request.id)
            if request.state == 'active':
                break
        else:
            request.cancel()
            raise ScaleError('Timed out. Cannot launch spot instance.')
        return request

    def launch_spot_instance(self, instance_properties):
        conn = self.get_connection()
        price = self.spot_price(instance_properties) * 3
        requests = conn.request_spot_instances(
                    price=price,
                    image_id=instance_properties.ami,
                    count=1,
                    instance_type=instance_properties.type,
                    placement=self._region_name)
        for request in requests:
            request = self.wait_for_fulfill(request)
            instance = self.get_instance_by_id(request.instance_id)
            self.wait_for_run(instance)
            conn.create_tags([instance.id],
                             {'Name': instance_properties.name})
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
                raise ScaleError('Stat semms empty.')
        avg_cluster_utilization = stat_sum / len(instances)
        logging.info('Avg cluster utilization is %s' % avg_cluster_utilization)
        return avg_cluster_utilization