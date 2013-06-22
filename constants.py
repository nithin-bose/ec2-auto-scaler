import os

APPLICATION_NAME = 'ec2-auto-scaler 0.1'
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'example/config.ini')
DEFAULT_PROVIDER = 'aws'
NON_CLUSTER_SECTIONS = ['main', 'aws', 'haproxy']
LOG_FORMAT = '%(asctime)s - %(levelname)s:%(name)s:%(message)s'
RUN_FOLDER = os.path.join(PROJECT_ROOT, 'run')
LOG_PATH = os.path.join(RUN_FOLDER, 'daemon.log')