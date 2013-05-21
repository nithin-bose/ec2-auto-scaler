import logging
import subprocess
from mako.template import Template
from loadbalancers import LoadBalancers
from errors import InstancesNotSetError


class HAProxy(LoadBalancers):

    CONFIG_TPL_PATH = './templates/HAProxy.tpl'
    CONFIG_FILE_PATH = 'example/haproxy.cfg'
    LB_PID_FILE_PATH = '/var/run/haproxy.pid'
    LB_EXECUTABLE = 'haproxy'

    def __init__(self, config_template=None, config_file=None, pIdFile=None,
                                                            executable=None):
        self.templateFile = self.CONFIG_TPL_PATH
        self.configFilename = self.CONFIG_FILE_PATH
        self.pIdFile = self.LB_PID_FILE_PATH
        self.executable = self.LB_EXECUTABLE

        if config_template is not None:
            self.templateFile = config_template
        if config_file is not None:
            self.configFilename = config_file
        if pIdFile is not None:
            self.pIdFile = pIdFile
        if executable is not None:
            self.executable = executable
        self.instances = None

    def setInstances(self, instances):
        self.instances = instances

    def _generate_haproxy_config(self):
        '''
        Generate an haproxy configuration based on the template and instances
        list.
        '''
        if self.instances is None:
            raise InstancesNotSetError()
        return Template(filename=self.templateFile).render(
                                                    instances=self.instances)

    def reloadConfiguration(self):
        # Generate the new config from the template.
        logging.info('Generating new configuration for haproxy.')
        new_configuration = self._generate_haproxy_config()

        # See if this new config is different. If it is then restart using it.
        # Otherwise just delete the temporary file and do nothing.
        logging.info('Comparing to existing configuration.')
        old_configuration = self.file_contents(filename=self.configFilename)
        if new_configuration != old_configuration:
            logging.info('Existing configuration is outdated.')

            # Overwite the existing config file.
            logging.info('Writing new configuration.')
            self.file_contents(filename=self.configFilename,
                          content=new_configuration)
            self._restartLoadBalancer()
        else:
            logging.info('Configuration unchanged. Nothing to do.')

    def _restartLoadBalancer(self):
        # Get PID if haproxy is already running.
        logging.info('Fetching PID from %s.' % self.pIdFile)
        pid = self.file_contents(filename=self.pIdFile)

        # Restart haproxy.
        logging.info('Restarting haproxy...')
        command = '''%s -p %s -f %s -sf %s''' % (self.executable, self.pIdFile,
                                                self.configFilename, pid or '')
        logging.info('Executing: %s' % command)
        subprocess.call(command, shell=True)
        logging.info('Done')