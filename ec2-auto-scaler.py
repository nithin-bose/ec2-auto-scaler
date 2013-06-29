import argparse
import logging
import traceback
import time

from libs.YapDi import yapdi

from autoscaling import AutoScale
from constants import APPLICATION_NAME, DEFAULT_CONFIG_PATH, LOG_FORMAT,\
LOG_PATH, DAEMON_PID_FILE
from configuration import Configuration
logging.basicConfig(filename=LOG_PATH, format=LOG_FORMAT, level=logging.DEBUG)


def main():
    print (APPLICATION_NAME)
    parser = argparse.ArgumentParser(description=APPLICATION_NAME)
    parser.add_argument(
                    'command',
                    choices=['start', 'stop', 'restart', 'status'],
                    help='Start, stop, restart or get status of application')
    parser.add_argument(
                    '--config',
                    default=DEFAULT_CONFIG_PATH,
                    help='Path to configuration file')
    args = parser.parse_args()

    daemon = yapdi.Daemon(DAEMON_PID_FILE)
    if args.command in ['start', 'restart']:
        if args.command == 'start':
            print('Starting application...')
            retcode = daemon.daemonize()
        elif args.command == 'restart':
            print('Restarting application...')
            retcode = daemon.restart()

        if retcode == yapdi.OPERATION_SUCCESSFUL:
            logging.info('Running as daemon...')
            logging.info('Parsing configuration')
            configuration = Configuration(args.config)
            logging.info('Fetching configuration details')
            scaling_interval = configuration.get_scaling_interval()
            clusters = configuration.get_cluster_details()
            while True:
                logging.info('Iterating clusters...')
                clusterCount = 0
                for cluster in clusters:
                    clusterCount += 1
                    logging.info('Processing cluster %s...' % clusterCount)
                    try:
                        logging.info('Initializing auto scale')
                        auto_scale = AutoScale(cluster)
                        logging.info('Running auto scale')
                        auto_scale.run()
                    except:
                        traceback.print_exc(file=open(LOG_PATH, "a"))
                    logging.info('Processed cluster %s.' % clusterCount)
                logging.info('All clusters processed')
                logging.info('Waiting %ss till next run...' % scaling_interval)
                time.sleep(scaling_interval)
        elif retcode == yapdi.INSTANCE_ALREADY_RUNNING:
            print("Already running")
        elif retcode == yapdi.INSTANCE_NOT_RUNNING:
            print('Application not running')
        else:
            print('Failed')

    elif args.command == 'stop':
        print('Trying to stop...')
        retcode = daemon.kill()
        if retcode == yapdi.OPERATION_SUCCESSFUL:
            print('Stopped but loadbalancer will continue to run.')
        elif retcode == yapdi.INSTANCE_NOT_RUNNING:
            print('Not running')
        elif retcode == yapdi.OPERATION_FAILED:
            print('Failed')

    elif args.command == 'status':
        pId = daemon.status()
        if pId:
            print('Running with pid %s' % pId)
        else:
            print('Not running')

if __name__ == '__main__':
    try:
        logging.getLogger().setLevel(logging.INFO)
        main()
    except Exception as e:
        traceback.print_exc(file=open(LOG_PATH, "a"))