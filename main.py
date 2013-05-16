import argparse
from autoscaling import AutoScale
from constants import APPLICATION_NAME, DEFAULT_CONFIG_PATH
from configuration import Configuration


def main():
    print (APPLICATION_NAME)
    parser = argparse.ArgumentParser(description=APPLICATION_NAME)
    parser.add_argument('--config', default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    configuration = Configuration(args.config)
    config_details = configuration.get_config_details()
    for cluster in config_details['clusters']:
        auto_scale = AutoScale(cluster, config_details)
        auto_scale.start()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)