import argparse
import logging
import traceback
from autoscaling import AutoScale
from constants import APPLICATION_NAME, DEFAULT_CONFIG_PATH, LOG_FORMAT,\
LOG_PATH
from configuration import Configuration
logging.basicConfig(filename=LOG_PATH, format=LOG_FORMAT, level=logging.DEBUG)


def main():
    print (APPLICATION_NAME)
    logging.info('*** Application Start ***')
    parser = argparse.ArgumentParser(description=APPLICATION_NAME)
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    logging.info('Parsing configuration')
    configuration = Configuration(args.config)
    logging.info('Fetching configuration details')
    config_details = configuration.get_config_details()
    for cluster in config_details['clusters']:
        logging.info('Initializing auto scale')
        auto_scale = AutoScale(cluster, config_details)
        logging.info('Running auto scale')
        auto_scale.run()
    logging.info('*** Application End ***')

if __name__ == '__main__':
    try:
        logging.getLogger().setLevel(logging.INFO)
        main()
    except Exception as e:
        traceback.print_exc()