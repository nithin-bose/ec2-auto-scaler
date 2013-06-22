import argparse
import logging
import traceback

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
            retcode = daemon.daemonize()
            print('Starting application...')
        elif args.command == 'restart':
            retcode = daemon.restart()
            print('Restarting application...')

        if retcode == yapdi.OPERATION_SUCCESSFUL:
            print('Running')
            logging.info('Parsing configuration')
            configuration = Configuration(args.config)
            logging.info('Fetching configuration details')
            clusters = configuration.get_cluster_details()
            for cluster in clusters:
                logging.info('Initializing auto scale')
                auto_scale = AutoScale(cluster)
                logging.info('Running auto scale')
                auto_scale.run()
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
        logging.info('*** Application Start ***')
        main()
        logging.info('*** Application End ***')
    except Exception as e:
        traceback.print_exc()